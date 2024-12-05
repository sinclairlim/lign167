from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import ast

# Load environment variables
load_dotenv(r"C:\Users\nchai\OneDrive\Desktop\key.env")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/api/analyze_code", methods=["POST"])
def analyze_code():
    print("Running analyze_code function")
    data = request.json
    if not data or "code" not in data or "intent" not in data:
        return jsonify({"error": "Missing code or intent in request body"}), 400

    code = data["code"]
    intent = data["intent"]

    try:
        # Generate conceptual graph using GPT-4
        conceptual_graph = generate_conceptual_graph(code, intent)

        # Generate high-level feedback using GPT-4
        high_level_feedback = get_high_level_feedback(code)

        # Return nodes, edges, and high-level feedback to the frontend
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

def generate_conceptual_graph(code, intent):
    prompt = (
        "As an AI programming tutor, analyze the following Python code in the context of the user's intent. "
        "Break down the code into its main components and represent them as nodes with concise labels. "
        "Avoid adding extra nodes like 'Missing Implementation' or 'Errors'; focus on the actual code elements. "
        "Create edges to show the logical flow between these nodes. "
        "For each node, provide a simple label such as the code element (e.g., 'Function Declaration', 'return hello_world'). "
        "If a node represents a part of the code with an error, include an 'error' message in the node. "
        "Provide the output in the following JSON format without any code block wrappers or additional text. "
        "Do not include explanations or additional descriptions. Only output the JSON object.\n"
        "{\n"
        '  "nodes": [\n'
        '    {"id": "1", "label": "Code element", "error": "Optional error message"},\n'
        '    ...\n'
        '  ],\n'
        '  "edges": [\n'
        '    {"source": "1", "target": "2"},\n'
        '    ...\n'
        '  ]\n'
        "}\n"
        "Remember: Only output the JSON object, and do not include any explanations, comments, or additional text.\n"
        f"User's intent:\n{intent}\n"
        f"Here is the code:\n```python\n{code}\n```"
    )

    completion = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "system",
                "content": "You are an AI that outputs only JSON objects as responses, without any explanations or additional text.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
    )

    response_text = completion.choices[0].message.content.strip()
    print("OpenAI API Response for Conceptual Graph:", response_text)

    # Remove code block markers if present
    if response_text.startswith("```") and response_text.endswith("```"):
        # Remove triple backticks and 'json' if present
        response_text = response_text.strip('`')
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()

    try:
        # Attempt to parse the response directly
        conceptual_graph = json.loads(response_text)
    except json.JSONDecodeError as json_error:
        print(f"JSON parsing error: {json_error}")

        # Attempt to extract JSON from the response
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1

        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_text = response_text[start_index:end_index]
            try:
                conceptual_graph = json.loads(json_text)
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing error after extraction: {json_error}")
                raise ValueError("Failed to parse JSON object from the response.")
        else:
            raise ValueError("JSON object not found in the response.")

    # At this point, 'conceptual_graph' should be a valid dictionary
    # Now, assign positions and adjust node structures
    nodes = conceptual_graph.get('nodes', [])
    edges = conceptual_graph.get('edges', [])

    # Assign positions and adjust nodes
    for index, node in enumerate(nodes):
        # Assign position
        # Positions will be adjusted by the frontend layout algorithm, so initial positions can be zero
        node['position'] = {'x': 0, 'y': 0}

        # Wrap the label in 'data' as expected by React Flow
        node['data'] = {'label': node.get('label', '')}
        # Include the error message in 'data' if it exists
        if 'error' in node:
            node['data']['error'] = node['error']
            del node['error']

        # Remove 'label' from the root of the node
        if 'label' in node:
            del node['label']

        # Optionally set a default type
        node['type'] = 'customNode'

    # Return the modified conceptual graph
    return {'nodes': nodes, 'edges': edges}

def analyze_code_tree(tree):
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
                "type": type(node).__name__,
                "data": {
                    "label": node_label,
                    "error": error,
                },
                "position": {"x": node_id * 200, "y": len(self.parent_stack) * 100},
            }

            nodes.append(node_info)

            if self.parent_stack:
                parent_id = self.parent_stack[-1]
                edge_info = {
                    "id": f"e{parent_id}-{current_node_id}",
                    "source": parent_id,
                    "target": current_node_id,
                }
                edges.append(edge_info)

            self.parent_stack.append(current_node_id)
            node_id += 1
            super().generic_visit(node)
            self.parent_stack.pop()

        # Lol these should be moved to a mapping / better data structure
        def get_node_label(self, node):
            # Expanded node labels for various structures
            if isinstance(node, ast.FunctionDef):
                return f"Function: {node.name}"
            elif isinstance(node, ast.ClassDef):
                return f"Class: {node.name}"
            elif isinstance(node, ast.For):
                return f"For Loop over {ast.unparse(node.target)}"
            elif isinstance(node, ast.While):
                return f"While Loop ({ast.unparse(node.test)})"
            elif isinstance(node, ast.If):
                return f"If Statement ({ast.unparse(node.test)})"
            elif isinstance(node, ast.Try):
                return "Try-Except Block"
            elif isinstance(node, ast.With):
                return f"With Statement ({ast.unparse(node.items[0].context_expr)})"
            elif isinstance(node, ast.Assign):
                targets = ', '.join([ast.unparse(t) for t in node.targets])
                return f"Assignment: {targets} = {ast.unparse(node.value)}"
            elif isinstance(node, ast.Return):
                return f"Return: {ast.unparse(node.value)}"
            elif isinstance(node, ast.Lambda):
                return "Lambda Function"
            elif isinstance(node, ast.ListComp):
                return "List Comprehension"
            elif isinstance(node, ast.DictComp):
                return "Dictionary Comprehension"
            elif isinstance(node, ast.Call):
                return f"Function Call: {ast.unparse(node.func)}"
            else:
                return type(node).__name__

        def detect_errors(self, node):
            # edge cases
            if isinstance(node, ast.FunctionDef):
                if len(node.body) == 0:
                    return "Function body is empty."
                self.current_function_name = node.name
            elif isinstance(node, ast.Return) and self.current_function_name:
                if node.value is None:
                    return f"Function '{self.current_function_name}' returns None."
            elif isinstance(node, ast.Call):
                func_name = ast.unparse(node.func)
                if func_name == self.current_function_name:
                    return "Recursive call detected."
            elif isinstance(node, ast.If):
                if isinstance(node.test, ast.NameConstant) and node.test.value in [True, False]:
                    return "If condition is always true or false."
            elif isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Constant) and isinstance(node.comparators[0], ast.Constant):
                    return "Comparison between two constants."
            elif isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Constant) and node.value.value is None:
                    return "Assigned None to a variable."
            elif isinstance(node, ast.Try):
                if not node.handlers:
                    return "Try block without except clauses."
            # add more exceptions here
            return None

    visitor = CodeVisitor()
    visitor.visit(tree)

    return {"nodes": nodes, "edges": edges}

def get_high_level_feedback(code):
    prompt = (
        "As an experienced software engineer and educator, analyze the following Python code. "
        "Provide high-level feedback on its logic, structure, and potential issues. "
        "Your response should be in the following JSON format without any code block wrappers or additional text. "
        "Do not include triple backticks or any markdown formatting. Only output the JSON object.\n"
        "{\n"
        '  "summary": "...",\n'
        '  "strengths": ["...", "..."],\n'
        '  "weaknesses": ["...", "..."],\n'
        '  "recommendations": ["...", "..."]\n'
        "}\n"
        f"Here is the code:\n```python\n{code}\n```"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": "You are an experienced software engineer and educator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
        )

        response_text = completion.choices[0].message.content.strip()
        print("OpenAI API Response:", response_text)

        # Remove code block markers if present
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text.strip("`")
            # Remove json label if present
            if response_text.startswith("json"):
                response_text = response_text[len("json"):].strip()

        feedback = json.loads(response_text)
        return feedback
    except json.JSONDecodeError as json_error:
        print(f"JSON parsing error: {json_error}")
        feedback = {"summary": response_text}
        return feedback
    except Exception as e:
        print(f"Error in get_high_level_feedback: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)