from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import ast
import re

# loading environment variables (similar approach found here: https://stackoverflow.com/questions/4906977)
load_dotenv(r"C:\Users\nchai\OneDrive\Desktop\key.env")

app = Flask(__name__)
# enabling cors for frontend-backend communication (ref: https://flask-cors.readthedocs.io/en/latest/)
CORS(app)

# creating openai client (ref: https://platform.openai.com/docs/api-reference)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/api/analyze_code", methods=["POST"])
def analyze_code():
    # printing so we know this function was hit
    print("Running analyze_code function")
    data = request.json
    if not data or "code" not in data or "intent" not in data:
        return jsonify({"error": "Missing code or intent in request body"}), 400

    code = data["code"]
    intent = data["intent"]

    try:
        # parsing user code with ast for more context (concept borrowed from https://docs.python.org/3/library/ast.html)
        tree = ast.parse(code)
        python_ast_context = analyze_code_tree(tree)

        # generating a conceptual graph that scales to the code's complexity
        conceptual_graph = generate_dynamic_conceptual_graph(code, intent, python_ast_context)

        # generating simpler, conceptual explanation referencing the user's intent
        high_level_feedback = get_conceptual_explanation(code, intent)

        return jsonify({
            "nodes": conceptual_graph["nodes"],
            "edges": conceptual_graph["edges"],
            "high_level_feedback": high_level_feedback
        })
    except ValueError as ve:
        print(f"ValueError occurred: {ve}")
        return jsonify({"error": str(ve)}), 500
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

def robust_json_parse(response_text: str):
    # this function attempts multiple parsing strategies (inspired by some tips on stack overflow https://stackoverflow.com/questions/956867)
    # tries direct parse, regex extraction, substring extraction, and progressive line trimming

    # this portion was partially generated with ChatGPT, while providing the above from StackOverflow for reference

    # --- phase 1: direct parse
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # --- phase 2: regex extraction
    pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*\})"
    match = re.search(pattern, response_text)
    if match:
        json_candidate = match.group(1) or match.group(2)
        json_candidate = json_candidate.strip('`')
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError as e:
            print(f"Regex capture parse error: {e}")

    # --- phase 3: substring extraction
    start_index = response_text.find('{')
    end_index = response_text.rfind('}') + 1
    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_text = response_text[start_index:end_index]
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"Substring parse error: {e}")
            # --- phase 4: progressive line trimming
            lines = json_text.split('\n')
            while lines:
                candidate = '\n'.join(lines)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    lines.pop()
            return None
    return None

def generate_dynamic_conceptual_graph(code, intent, python_ast_context):
    # dynamically generate a conceptual graph with enough nodes to show distinct logic blocks
    # referencing an approach used for code visualization from https://medium.com/geekculture/visualizing-abstract-syntax-trees

    ast_nodes_str = json.dumps(python_ast_context.get("nodes", []), indent=2)
    ast_edges_str = json.dumps(python_ast_context.get("edges", []), indent=2)

    prompt = (
        "You are an AI that generates a dynamic conceptual graph of the user's Python code. "
        "Produce enough nodes to capture distinct logic blocks or conceptual chunks, but do not be too verbose with the nodes (i.e., create a node for every line)."
        "Create just enough nodes so that the user can grasp the conceptual logic of their code without being overwhelmed by the details."
        "If there's a conceptual mismatch, reference the specific line (e.g. 'if heap[index] > heap[parent]:') "
        "AND attach the error message to the node that actually represents that logic step. "
        "For example, if 'swap with parent' is the conceptual step where the code references 'if heap[index] > heap[parent]', "
        "then the error belongs to the 'swap_parent' node, not just the entire push_heap function.\n\n"
        "Error explanations should explain what conceptually happens in their incorrect code, and how that differs from their intent. It should NOT tell the user what they should do to fix the code. Emphasis on helping the user with conceptual understanding.\n"
        "Error explanations must explain things through logic, rather than referring to abstract terms, or conditions the user may not be familiar with."
        "For instance: 'When Z happens, X happens instead of Y.' Assume that the user is new to CS concepts, and always give concise, clear explanations.\n\n"
        "Output only valid JSON with 'nodes' and 'edges'. If you include errors, link them on the node that logically corresponds to the code line. "
        "Nodes should have position fields with small, close-together coordinates so related nodes appear visually near each other, "
        "for example around (x: 100-300, y: 100-300). The user does NOT want nodes placed far apart.\n\n"
        "No code fences, no bullet points, no forced minimal or fixed node count. The final graph must be parseable.\n\n"
        f"User's intent:\n{intent}\n\n"
        f"AST Nodes:\n{ast_nodes_str}\n\n"
        f"AST Edges:\n{ast_edges_str}\n\n"
        f"User's code:\n```python\n{code}\n```"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "system",
                "content": (
                    "You produce a dynamic conceptual graph, with 'just enough' nodes for conceptual clarity. "
                    "Nodes must reference code lines if mismatches exist, but do not overload with trivial nodes."
                )
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1600,
    )

    response_text = completion.choices[0].message.content.strip()
    print("OpenAI API Response for Conceptual Graph:", response_text)

    conceptual_graph = robust_json_parse(response_text)
    if not conceptual_graph:
        raise ValueError("Failed to parse JSON object from the GPT response.")

    nodes = conceptual_graph.get("nodes", [])
    edges = conceptual_graph.get("edges", [])

    # if there's a separate "errors" array, merge them into the corresponding nodes
    errors_list = conceptual_graph.get("errors", [])
    for err_item in errors_list:
        err_node_id = err_item.get("id", "")
        err_desc = err_item.get("description", "")
        for node in nodes:
            if node.get("id") == err_node_id:
                node["error"] = err_desc
                break

    # convert node errors from object to string
    for node in nodes:
        node['position'] = {'x': 0, 'y': 0}
        label_value = node.pop('label', '')
        error_value = node.pop('error', None)

        node['data'] = {'label': label_value}

        if error_value:
            if isinstance(error_value, dict):
                # combine "line" and "message" into a single string
                line_info = error_value.get("line", "")
                msg_info = error_value.get("message", "")
                combined_err = f"{line_info}\n{msg_info}" if line_info or msg_info else None
                node['data']['error'] = combined_err
            else:
                node['data']['error'] = error_value

        node['type'] = 'customNode'

    return {"nodes": nodes, "edges": edges}

def analyze_code_tree(tree):
    # ast-based structure to give gpt deeper context, not used directly in the final graph
    nodes = []
    edges = []
    node_id = 0

    class CodeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.parent_stack = []
            self.current_function_name = None

        def generic_visit(self, node):
            nonlocal node_id
            current_node_id = str(node_id)
            node_label = self.get_node_label(node)
            error = self.detect_errors(node)

            node_info = {
                "id": current_node_id,
                "node_type": type(node).__name__,
                "label": node_label,
                "error": error
            }
            nodes.append(node_info)

            if self.parent_stack:
                parent_id = self.parent_stack[-1]
                edges.append({
                    "id": f"e{parent_id}-{current_node_id}",
                    "source": parent_id,
                    "target": current_node_id,
                })

            self.parent_stack.append(current_node_id)
            node_id += 1
            super().generic_visit(node)
            self.parent_stack.pop()

        def get_node_label(self, node):
            if isinstance(node, ast.FunctionDef):
                return f"FunctionDef: {node.name}"
            elif isinstance(node, ast.ClassDef):
                return f"ClassDef: {node.name}"
            return type(node).__name__

        def detect_errors(self, node):
            # checking for empty function or recursive calls, just as an example
            if isinstance(node, ast.FunctionDef):
                if len(node.body) == 0:
                    return "Empty function."
                self.current_function_name = node.name
            elif isinstance(node, ast.Call):
                func_name = ast.unparse(node.func)
                if func_name == self.current_function_name:
                    return "Recursive call detected."
            return None

    visitor = CodeVisitor()
    visitor.visit(tree)
    return {"nodes": nodes, "edges": edges}

def get_conceptual_explanation(code, intent):
    # provide a single json object with 'explanation' referencing the user's intent
    prompt = (
        "You are a conceptual logic tutor. Provide a single JSON object {\"explanation\": \"...\"} "
        "focusing on how this code conceptually aligns or misaligns with the user's intent. "
        "If there's a mismatch, reference the lines of code in plain friendly language. "
        "For instance, this would be a good sentence within the explanation: When an element is pushed to the heap, "
        "the biggest element is bubbled up to the top instead of the smallest.\n"
        "Format the explanation in an appealing manner, using a bullet point for each line you're referencing.\n\n"
        "{\n"
        '  "explanation": "Short conceptual explanation referencing lines and comparing code logic to user intent."\n'
        "}\n"
        f"User intent:\n{intent}\n\n"
        f"Code:\n```python\n{code}\n```"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Output only {\"explanation\":\"...\"}, referencing user intent and code lines. "
                        "No bullet points, no fix instructions."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=600,
        )

        response_text = completion.choices[0].message.content.strip()
        print("OpenAI API Response (High-Level Explanation):", response_text)

        # strip any code fences
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text.strip("`").strip()
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].strip()

        # --- NEW STEP: attempt to escape unescaped newlines within quoted strings
        # this uses regex that finds text between quotes and replaces raw newlines with \n
        # so that it's valid JSON
        def escape_newlines_in_quoted_strings(m: re.Match):
            content = m.group(0)
            # replace unescaped newlines with \n
            content = content.replace("\n", "\\n")
            return content

        # this regex matches any double-quoted string (including the quotes)
        # note: DOESNT handle every JSON edge case perfectly, but works well for typical multiline GPT outputs
        quoted_string_pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'
        sanitized_response = re.sub(quoted_string_pattern, escape_newlines_in_quoted_strings, response_text)

        feedback = robust_json_parse(sanitized_response)
        if feedback is None:
            print("Could not parse the explanation JSON even after newline escaping. Returning raw text.")
            feedback = {"explanation": response_text}

        return feedback

    except Exception as e:
        print(f"Error in get_conceptual_explanation: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(debug=True)
