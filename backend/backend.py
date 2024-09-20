import json
import asyncio
import ollama
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import traceback
import logging
from datetime import timedelta

# Import functions from the functions folder
from functions.get_current_weather import get_current_weather
from functions.normal_response import normal_response

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your_fallback_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

CORS(app, supports_credentials=True)

logging.basicConfig(level=logging.DEBUG)

with open('tools.json', 'r') as f:
    tools = json.load(f)


async def run(model: str, user_input: str):
    client = ollama.AsyncClient()

    # Check if conversation history exists in the session
    if 'history' not in session:
        session['history'] = []

    # Updated system prompt introducing OceanGPT
    system_prompt = """
    You are OceanGPT, a helpful AI assistant specializing in ocean-related topics and data analysis. 
    Introduce yourself as OceanGPT when asked about your identity. Use tools only if necessary. Otherwise, respond based on your built-in knowledge.
    """
    
    messages = session['history'] + [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    response = await client.chat(
        model=model,
        messages=messages,
        tools=tools,
        format="json"
    )

    app.logger.debug(f"Response from Ollama: {response}")

    # Check if the content can be directly used (without tools)
    response_content = response["message"]["content"]

    # If no tool calls and the response is complete, return it
    if response_content and "tool_calls" not in response["message"]:
        session['history'].append({"role": "user", "content": user_input})
        session['history'].append({"role": "assistant", "content": response_content})
        return response_content

    # If tool calls are detected, process them
    available_functions = {
        "normal_response": normal_response,
        "get_current_weather": get_current_weather
    }

    if response["message"].get("tool_calls"):
        for tool in response["message"]["tool_calls"]:
            function_to_call = available_functions.get(tool["function"]["name"])

            if function_to_call == normal_response:
                function_response = function_to_call(
                    user_input=user_input, system_response=response_content)

                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                    }
                )

                response2 = await client.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': function_response}],
                )

                session['history'].append({"role": "assistant", "content": response2["message"]["content"]})
                return response2["message"]["content"]

            elif function_to_call == get_current_weather:
                function_response = function_to_call(
                    tool["function"]["arguments"]["location"],
                    tool["function"]["arguments"]["date"]
                )

                messages.append(
                    {
                        "role": "tool",
                        "content": function_response,
                    }
                )

                response2 = await client.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': function_response}],
                )

                session['history'].append({"role": "assistant", "content": response2["message"]["content"]})
                return response2["message"]["content"]

    # Return original response if no tool was needed
    session['history'].append({"role": "user", "content": user_input})
    session['history'].append({"role": "assistant", "content": response_content})
    return response["message"]["content"]


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("prompt", "")
    model = data.get("model", "llama3.1")

    if not user_input:
        return jsonify({"error": "No user input provided"}), 400

    try:
        # Run the async function in Flask
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(run(model, user_input))

        return jsonify({"response": response}), 200

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@app.route('/reset', methods=['POST'])
def reset():
    session.pop('history', None)
    return jsonify({"message": "Conversation history cleared"}), 200


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.csv'):
        # Process the CSV file here
        return jsonify({"message": f"Successfully uploaded {file.filename}"}), 200
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV file."}), 400


if __name__ == "__main__":
    app.run(debug=True)