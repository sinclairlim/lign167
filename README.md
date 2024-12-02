# **FLEX: Fault Localization and Explanations**

## **Overview**
FLEX is a web-based tool designed to help beginner programmers bridge the gap between abstract coding concepts and their implementation. The application provides:
- **Code Analysis**: Analyzes Python code for key structures (e.g., loops, functions, recursion).
- **Conceptual Hints**: Uses a Retrieval-Augmented Generation (RAG) interface to provide contextual hints based on previously analyzed code.
- **Interactive UI**: A React-based frontend for submitting code and viewing analysis results.

---

## **Architecture**
- **Frontend**: React with TypeScript.
- **Backend**: Flask (Python).
- **Database**: Local JSON file (`database.json`) for storing code snippets, analyses, and hints.
- **RAG Interface**: Fetches related hints and explanations from historical data in the database.

---

## **Features**
1. **Code Submission**: Users can input Python code via the frontend.
2. **Code Analysis**: 
   - Identifies structures like loops, conditionals, functions, and more.
   - Parses code using Python's Abstract Syntax Tree (AST).
3. **Conceptual Hints**:
   - Retrieves related hints from a local database for better understanding.
   - Adapts dynamically based on the user's input.
4. **History Retrieval**:
   - Displays all past analyses and related hints.

---

## **Prerequisites**
- Python 3.8 or later
- Flask (`pip install flask`)
- Node.js and npm

---
