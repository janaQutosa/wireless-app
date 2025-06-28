from flask import Flask, render_template, request, jsonify
import requests
from computations import (
    compute_wireless_system,
    compute_ofdm_system,
    compute_link_budget,
    compute_cellular_design
)
from dotenv import load_dotenv
import os
import json
import logging
from cachetools import TTLCache
from openai import OpenAI

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load API key and model from .env
OPENAI_API_KEY ="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"
OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Initialize OpenAI client
from openai import OpenAI

# Replace with your Groq API key
client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)

# Cache for API responses
cache = TTLCache(maxsize=100, ttl=3600)

def chat_with_openai(prompt):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "Always reply ONLY with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return json.dumps({"valid": False, "message": f"AI error: {str(e)}"})


def validate_inputs_with_gpt(inputs, scenario):
    prompt = f"""
You are a JSON validation assistant.

A user submitted parameters for the following scenario: {scenario}.

Inputs:
{json.dumps(inputs, indent=2)}

Your task:
1. Check if required parameters are present.
2. Check for empty or non-numeric values.
3. Check that all numbers are within reasonable engineering ranges.

Respond ONLY with a **valid JSON object**, exactly like this:

{{
  "valid": true,
  "message": "Everything is okay!"
}}

or

{{
  "valid": false,
  "message": "Explain what is wrong and how to fix it."
}}

Do NOT include any other text.
"""
    try:
        response = chat_with_openai(prompt)

        # Make sure it's clean JSON (strip spaces/newlines)
        response = response.strip()
        if not response.startswith("{"):
            response = "{" + response  # Try to fix if model forgot braces
        data = json.loads(response)
        return data["valid"], data["message"]
    except json.JSONDecodeError:
        return False, f"AI validation failed: invalid JSON response:\n{response}"
    except Exception as e:
        return False, f"AI validation crashed: {str(e)}"

def explain_results_with_gpt(results, scenario):
    prompt = f"""
You are a helpful assistant. Explain the {scenario} results in the following clean JSON format:

{{
  "title": "Short, clear title",
  "methodology": "Explanation of how the system works.",
  "components": {{
    "component1": "What this component does and its numeric role.",
    "component2": "Same...",
    ...
  }},
  "interpretation": "Overall meaning of the results."
}}

Use the values in the result to generate explanations. Return only raw JSON (no markdown, no quotes, no backslashes, no newlines).
Results: {json.dumps(results, indent=2)}
"""
    return chat_with_openai(prompt)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/wireless", methods=["GET", "POST"])
def wireless():
    if request.method == "POST":
        inputs = request.form.to_dict()
        is_valid, message = validate_inputs_with_gpt(inputs, "wireless communication system")
        if not is_valid:
            return jsonify({"error": message}), 400
        results = compute_wireless_system(inputs)
        explanation = explain_results_with_gpt(results, "wireless communication system")
        return jsonify({"results": results, "explanation": explanation})
    return render_template("wireless.html")

@app.route("/ofdm", methods=["GET", "POST"])
def ofdm():
    if request.method == "POST":
        inputs = request.form.to_dict()
        is_valid, message = validate_inputs_with_gpt(inputs, "OFDM system")
        if not is_valid:
            return jsonify({"error": message}), 400
        results = compute_ofdm_system(inputs)
        explanation = explain_results_with_gpt(results, "OFDM system")
        return jsonify({"results": results, "explanation": explanation})
    return render_template("ofdm.html")

@app.route("/link_budget", methods=["GET", "POST"])
def link_budget():
    if request.method == "POST":
        inputs = request.form.to_dict()
        is_valid, message = validate_inputs_with_gpt(inputs, "link budget calculation")
        if not is_valid:
            return jsonify({"error": message}), 400
        results = compute_link_budget(inputs)
        explanation = explain_results_with_gpt(results, "link budget calculation")
        return jsonify({"results": results, "explanation": explanation})
    return render_template("link_budget.html")

@app.route("/cellular", methods=["GET", "POST"])
def cellular():
    if request.method == "POST":
        inputs = request.form.to_dict()
        is_valid, message = validate_inputs_with_gpt(inputs, "cellular system design")
        if not is_valid:
            return jsonify({"error": message}), 400
        results = compute_cellular_design(inputs)
        explanation = explain_results_with_gpt(results, "cellular system design")
        return jsonify({"results": results, "explanation": explanation})
    return render_template("cellular.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
