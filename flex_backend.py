from flask import Flask, request, jsonify
import ast
import json
import os

app = Flask(__name__)

DB_FILE = "database.json"

# Utility to parse Python code and identify structures
class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.summary = []

    def visit_FunctionDef(self, node):
        self.summary.append(f"Function: {node.name}")
        self.generic_visit(node)

    def visit_If(self, node):
        self.summary.append("If statement found")
        self.generic_visit(node)

    def visit_While(self, node):
        self.summary.append("While loop found")
        self.generic_visit(node)

    def visit_For(self, node):
        self.summary.append("For loop found")
        self.generic_visit(node)

    def visit_Assign(self, node):
        self.summary.append("Variable assignment")
        self.generic_visit(node)

    def analyze(self, code):
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.summary
        except SyntaxError as e:
            return [f"Syntax Error: {e}"]

# Helper to load and save the JSON DB
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/analyze', methods=['POST'])
def analyze_code():
    code = request.json.get('code', '')
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze(code)

    # RAG: Fetch historical entries for related hints
    db = load_db()
    related_hints = [
        entry["analysis"] for entry in db if any(item in code for item in entry["code"].split())
    ]

    entry = {"code": code, "analysis": analysis, "hints": related_hints}
    db.append(entry)
    save_db(db)

    return jsonify({"analysis": analysis, "hints": related_hints})

@app.route('/history', methods=['GET'])
def get_history():
    db = load_db()
    return jsonify(db)

if __name__ == '__main__':
    app.run(debug=True)
