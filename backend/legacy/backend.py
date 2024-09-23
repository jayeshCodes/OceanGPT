import json
import asyncio
import re
import ollama
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import traceback
import logging
from datetime import timedelta, datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

# Import functions from the functions folder
from functions.get_current_weather import get_current_weather
from functions.analyze_sea_level_data import analyze_sea_level_data
from functions.plot_sea_level_trend import plot_sea_level_trend

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

    if 'history' not in session:
        session['history'] = []

    system_prompt = """
    You are OceanGPT, a helpful AI assistant specializing in ocean-related topics and data analysis. 
    Introduce yourself as OceanGPT when asked about your identity. Use tools only if necessary. Otherwise, respond based on your built-in knowledge. Again, use tools only if necessary (e.g., to analyze data or plot trends).
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

    response_content = response["message"]["content"]

    if "tool_calls" not in response["message"]:
        session['history'].append({"role": "user", "content": user_input})
        session['history'].append(
            {"role": "assistant", "content": response_content})
        return response_content

    available_functions = {
        "dummy_function": lambda: {"response": ["Respond normally without calling a function."]},
        "get_current_weather": get_current_weather,
        "analyze_sea_level_data": analyze_sea_level_data,
        "plot_sea_level_trend": plot_sea_level_trend
    }

    for tool in response["message"]["tool_calls"]:
        function_name = tool["function"]["name"]
        function_to_call = available_functions.get(function_name)

        if function_to_call:
            try:
                function_args = json.loads(tool["function"]["arguments"]) if isinstance(
                    tool["function"]["arguments"], str) else tool["function"]["arguments"]
                function_response = function_to_call(**function_args)
                # print(function_response)

                messages.append(
                    {
                        "role": "tool",
                        "content": str(function_response),
                    }
                )

                # add json data to a separate structure for processing in the frontend
                json_data = function_response["data"] if "data" in function_response else None

                response2 = await client.chat(
                    model=model,
                    messages=messages +
                    [{'role': 'user', 'content': str(function_response)}],
                )

                final_response = response2["message"]["content"]
                session['history'].append(
                    {"role": "assistant", "content": final_response})
                return final_response, json_data

            except json.JSONDecodeError:
                app.logger.error(f"Error decoding JSON for function arguments: {
                                 tool['function']['arguments']}")
                return "There was an error processing the function arguments."
            except Exception as e:
                app.logger.error(f"Error calling function {
                                 function_name}: {str(e)}")
                return f"There was an error executing the {function_name} function."

    # If no function was called, return the original response
    session['history'].append({"role": "user", "content": user_input})
    session['history'].append(
        {"role": "assistant", "content": response_content})
    return response_content


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("prompt", "")
    model = data.get("model", "llama3.1")

    if not user_input:
        return jsonify({"error": "No user input provided"}), 400

    try:
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
        try:
            location = "sea_level"  # Default location
            date_saved = datetime.now().strftime("%Y%m%d")
            new_filename = f"{location}_{date_saved}.csv"

            os.makedirs('../database', exist_ok=True)
            file_path = os.path.join('../database', new_filename)

            # Check if a file with the same location already exists
            existing_files = [f for f in os.listdir(
                '../database') if f.startswith(location)]
            overwrite = False
            existing_file_info = None

            for existing_file in existing_files:
                existing_file_path = os.path.join('../database', existing_file)
                file_age = (datetime.now(
                ) - datetime.fromtimestamp(os.path.getmtime(existing_file_path))).days

                # Check if the existing file is older than 30 days
                if file_age > 30:
                    overwrite = True
                    break
                else:
                    # Save the existing file information
                    existing_file_info = {
                        'filename': existing_file,
                        'file_path': existing_file_path,
                        'file_age': file_age,
                    }

            # If there are no files or we decided to overwrite, save the new file
            if not existing_files or overwrite:
                file.save(file_path)

                df = pd.read_csv(file_path, delimiter=',', header=0,
                                 skiprows=5, index_col=False)
                df.columns = df.columns.str.strip()
                cleaned_file_path = os.path.join(
                    '../database', f"cleaned_{new_filename}")
                df.to_csv(cleaned_file_path, index=False)

                df = pd.read_csv(cleaned_file_path)

                session['uploaded_file'] = {
                    'filename': f"cleaned_{new_filename}",
                    'file_path': cleaned_file_path,
                    'preview': df.head().to_dict(),
                    "context": "a dataset representing sea level data over the years",
                }

            # Include existing file info if available
            if existing_file_info:
                session['existing_file'] = existing_file_info

                return jsonify({"message": f"File saved as {new_filename} and processed successfully."}), 200
            else:
                # Include existing file info in the session
                session['existing_file'] = existing_file_info
                return jsonify({"error": "An existing file is still valid and not older than 30 days."}), 400

        except Exception as e:
            app.logger.error(f"Error processing file: {e}")
            return jsonify({"error": "Error processing file"}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True)
