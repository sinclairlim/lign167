from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os

# put your directory here
load_dotenv(r"C:\Users\nchai\OneDrive\Desktop\key.env")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/api/explain", methods=["POST"])
def explain():
    data = request.json
    if not data or "nodeLabel" not in data:
        return jsonify({"error": "Missing nodeLabel in request body"}), 400

    node_label = data["nodeLabel"]

    try:
        # Use the updated OpenAI client with chat-based model
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Explain the following operation: {node_label}"}
            ],
            max_tokens=100,
        )
        
        # Extract response content using Pydantic model methods
        explanation = completion.choices[0].message.content.strip()
        
        # Convert completion to a dictionary if needed for debugging or additional processing
        response_data = completion.model_dump()

        return jsonify({"explanation": explanation, "response_data": response_data})
    except Exception as e:
        print(f"Error occurred: {e}")  # Print the error for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
