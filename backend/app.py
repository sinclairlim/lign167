from flask import Flask, request, jsonify
from flask_cors import CORS  # referencing flask-cors docs: https://flask-cors.readthedocs.io
from openai import OpenAI  # referencing openai api docs: https://platform.openai.com/docs/introduction
from dotenv import load_dotenv  # referencing python-dotenv docs: https://pypi.org/project/python-dotenv/
import os
import json
import ast  # referencing python ast library docs: https://docs.python.org/3/library/ast.html
import re

# hey let's load environment variables (similar approach found here: https://stackoverflow.com/questions/4906977)
load_dotenv(r"C:\Users\nchai\OneDrive\Desktop\key.env")

app = Flask(__name__)
# enabling cors for frontend-backend communication (ref: https://flask-cors.readthedocs.io/en/latest/)
CORS(app)

# creating openai client (ref: https://platform.openai.com/docs/api-reference)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/api/analyze_code", methods=["POST"])
def analyze_code():
    # printing so we know this function was hit
    print("running analyze_code function")
    data = request.json
    if not data or "code" not in data or "intent" not in data:
        return jsonify({"error": "missing code or intent in request body"}), 400

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
        print(f"valueerror occurred: {ve}")
        return jsonify({"error": str(ve)}), 500
    except Exception as e:
        print(f"error occurred: {e}")
        return jsonify({"error": "an unexpected error occurred."}), 500

def robust_json_parse(response_text: str):
    # this function attempts multiple parsing strategies (inspired by some tips on stack overflow https://stackoverflow.com/questions/956867)
    # tries direct parse, regex extraction, substring extraction, and progressive line trimming
    # everything in lowercase for a more informal style

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
            print(f"regex capture parse error: {e}")

    # --- phase 3: substring extraction
    start_index = response_text.find('{')
    end_index = response_text.rfind('}') + 1
    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_text = response_text[start_index:end_index]
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"substring parse error: {e}")
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
    # not creating a node for every line, but enough to help conceptual clarity

    ast_nodes_str = json.dumps(python_ast_context.get("nodes", []), indent=2)
    ast_edges_str = json.dumps(python_ast_context.get("edges", []), indent=2)

    prompt = (
        "you are an ai that generates a dynamic conceptual graph of the user's python code. "
        "produce enough nodes to capture distinct logic blocks or conceptual chunks, but do not create a node for every line. "
        "if the user's code is more complex, it's okay to have more nodes, but if it’s simple, fewer nodes are acceptable. "
        "if there's a conceptual mismatch, reference the specific line and explain briefly in friendly, conceptual terms.\n\n"
        "output only valid json with 'nodes' and 'edges'. if you include errors, put them in the node itself or a top-level 'errors' array. "
        "no code fences, no bullet points, no forced minimal or fixed node count. the final graph must be parseable.\n\n"
        f"user's intent:\n{intent}\n\n"
        f"ast nodes:\n{ast_nodes_str}\n\n"
        f"ast edges:\n{ast_edges_str}\n\n"
        f"user's code:\n```python\n{code}\n```"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "system",
                "content": (
                    "you produce a dynamic conceptual graph, with 'just enough' nodes for conceptual clarity. "
                    "nodes must reference code lines if mismatches exist, but do not overload with trivial nodes."
                )
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1600,
    )

    response_text = completion.choices[0].message.content.strip()
    print("openai api response for conceptual graph:", response_text)

    conceptual_graph = robust_json_parse(response_text)
    if not conceptual_graph:
        raise ValueError("failed to parse json object from the gpt response.")

    nodes = conceptual_graph.get("nodes", [])
    edges = conceptual_graph.get("edges", [])

    # if there's a separate "errors" array, merge them into the corresponding nodes
    errors_list = conceptual_graph.get("errors", [])
    for error_item in errors_list:
        node_id = str(error_item.get("node", ""))
        error_description = error_item.get("description", "")
        for node in nodes:
            if node.get("id") == node_id:
                node["error"] = error_description
                break

    # transform nodes for react flow
    for node in nodes:
        node['position'] = {'x': 0, 'y': 0}
        label_value = node.pop('label', '')
        error_value = node.pop('error', None)

        node['data'] = {'label': label_value}
        if error_value:
            node['data']['error'] = error_value

        node['type'] = 'customNode'

    return {"nodes": nodes, "edges": edges}

def analyze_code_tree(tree):
    # ast-based structure to give gpt deeper context, not used directly in the final graph
    # referencing ast nodevisitor approach: https://docs.python.org/3/library/ast.html#ast.NodeVisitor
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
                    return "empty function."
                self.current_function_name = node.name
            elif isinstance(node, ast.Call):
                func_name = ast.unparse(node.func)
                if func_name == self.current_function_name:
                    return "recursive call detected."
            return None

    visitor = CodeVisitor()
    visitor.visit(tree)
    return {"nodes": nodes, "edges": edges}

def get_conceptual_explanation(code, intent):
    # provide a single json object with 'explanation' referencing the user's intent
    # referencing a similar approach for short conceptual summaries from openai official examples
    prompt = (
        "you are a conceptual logic tutor. provide a single json object {\"explanation\": \"...\"} "
        "focusing on how this code conceptually aligns or misaligns with the user's intent. "
        "if there's a mismatch, reference the lines of code in plain friendly language. "
        "format the explanation in an appealing manner, but output only the json.\n"
        "refer to the user in a friendly manner.\n\n"
        "{\n"
        '  "explanation": "short conceptual explanation referencing lines and comparing code logic to user intent."\n'
        "}\n"
        f"user intent:\n{intent}\n\n"
        f"code:\n```python\n{code}\n```"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "output only {\"explanation\":\"...\"}, referencing user intent and code lines."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=600,
        )

        response_text = completion.choices[0].message.content.strip()
        print("openai api response (high-level explanation):", response_text)

        # if gpt still wraps it in code fences, strip them
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text.strip("`").strip()
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].strip()

        feedback = robust_json_parse(response_text)
        if feedback is None:
            print("could not parse the explanation json. returning raw text.")
            feedback = {"explanation": response_text}
        return feedback

    except Exception as e:
        print(f"error in get_conceptual_explanation: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # running the flask app in debug mode (see flask docs: https://flask.palletsprojects.com/en/2.2.x/quickstart/)
    app.run(debug=True)
