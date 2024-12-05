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
    if not data or "code" not in data:
        return jsonify({"error": "Missing code in request body"}), 400

    code = data["code"]

    try:
        # Parse code
        tree = ast.parse(code)

        # Analyze the code tree
        analysis_result = analyze_code_tree(tree)

        # Generate high-level feedback using gpt-4o-2024-11-20
        high_level_feedback = get_high_level_feedback(code)

        # Return nodes, edges, and high-level feedback to the frontend
        return jsonify({
            "nodes": analysis_result["nodes"],
            "edges": analysis_result["edges"],
            "high_level_feedback": high_level_feedback
        })
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

def generate_conceptual_graph(code, intent):
    prompt = (
        "As an AI programming tutor, analyze the following Python code in the context of the user's intent. "
        "Break down the code into conceptual components (e.g., functions, loops, conditionals) and represent them as nodes. "
        "Create edges to show the logical flow between these nodes. "
        "For each node, provide a descriptive label that clearly indicates what that part of the code does. "
        "If there are any logical errors or discrepancies between the code and the intended goal, include an 'error' message in the node. "
        "Provide the output in the following JSON format without any code block wrappers or additional text. "
        "Do not include explanations or additional descriptions. Only output the JSON object.\n"
        "{\n"
        '  "nodes": [\n'
        '    {"id": "1", "label": "Descriptive label", "error": "Optional error message"},\n'
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

    node_info = data["nodeInfo"]

    try:
        # Construct a detailed prompt with structured output
        prompt = (
            "As an AI programming tutor, analyze the following code structure or error and provide a detailed explanation. "
            "Your response should include: "
            "1. A brief description of the structure or error. "
            "2. The underlying computer science concepts involved. "
            "3. Potential issues or errors and how to fix them. "
            "Provide the output in the following JSON format:\n"
            "{\n"
            '  "description": "...",\n'
            '  "concepts": ["...", "..."],\n'
            '  "issues": ["...", "..."],\n'
            '  "suggestions": ["...", "..."]\n'
            "}\n"
            f"Here is the code structure or error: {node_info}"
        )

        completion = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": "You are an AI programming tutor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
        )

        # Extract and parse the response
        response_text = completion.choices[0].message.content.strip()
        explanation = json.loads(response_text)

        return jsonify({"explanation": explanation})
    except json.JSONDecodeError as json_error:
        # Handle JSON parsing errors
        print(f"JSON parsing error: {json_error}")
        # Fallback to unstructured text
        explanation = {"description": response_text}
        return jsonify({"explanation": explanation})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

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
        "Your response should be in the following JSON format without any code block wrappers or additional text:\n"
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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an experienced software engineer and educator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
        )

        response_text = completion.choices[0].message.content.strip()
        print("OpenAI API Response:", response_text)

        # this section to debug weird json
        if response_text.startswith("```") and response_text.endswith("```"):
            response_text = response_text.strip("`")
            # remove json label if present too
            if response_text.startswith("json"):
                response_text = response_text[len("json"):].strip()
        
        # in case theres still kson
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