from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import os
import traceback
import logging
from datetime import timedelta, datetime
import pandas as pd
import re
import glob

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your_fallback_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

CORS(app, supports_credentials=True)

logging.basicConfig(level=logging.DEBUG)

llama_url = "http://localhost:11434/api/generate"

with open('tools.json', 'r') as f:
    tools = json.load(f)

def get_current_weather(location):
    try:
        logging.info(f"Weather API called for location: {location}")
        date = datetime.now().strftime("%Y-%m-%d")
        url = f'https://api.weatherapi.com/v1/current.json?key=f2b1a3991c524713847144853231406&q={location}&dt={date}'
        response = requests.get(url)

        if response.status_code == 200:
            weather_info = response.json()
            logging.info(f"Weather API response: {weather_info}")
        else:
            weather_info = {"error": "Failed to retrieve data"}
            logging.error(f"Weather API call failed with status: {response.status_code}")

        return json.dumps(weather_info)

    except Exception as e:
        logging.error(f"Error in get_current_weather: {str(e)}")
        return json.dumps({"error": str(e)})

@app.before_request
def make_session_permanent():
    session.permanent = True


def find_cleaned_csv_file():
    """Find the most recently uploaded cleaned CSV file."""
    pattern = '../database/cleaned_sea_level_*.csv'
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def get_first_n_rows_from_csv(file_path, n):
    """Return the first n rows from the cleaned CSV file in the desired JSON format."""
    df = pd.read_csv(file_path)
    df.reset_index(drop=True, inplace=True)

    columns = [{"field": col, "headerName": col.capitalize(), "width": 150}
               for col in df.columns]
    rows = [{"id": idx + 1, **row.to_dict()}
            for idx, row in df.head(n).iterrows()]

    return {"columns": columns, "rows": rows}


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        prompt = data.get('prompt', '')

        if prompt.startswith("preview first"):
            n = int(re.search(r'preview first (\d+)', prompt).group(1))
            cleaned_file_path = find_cleaned_csv_file()
            if cleaned_file_path:
                result = get_first_n_rows_from_csv(cleaned_file_path, n)
                return jsonify(result), 200
            else:
                return jsonify({"error": "No cleaned CSV file found."}), 404

        history = session.get('history', [])
        history.append({"role": "user", "content": prompt})

        conversation = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history])

        file_context = session.get('uploaded_file', None)
        file_info = ""
        if file_context:
            file_info = f"\n\nA file named {
                file_context['filename']} was uploaded recently. You can refer to this file if relevant to the user's query, but don't focus on it unless specifically asked."

        system_prompt = """You are a helpful AI assistant named OceanGPT, specializing in ocean-related topics and data analysis. Please provide informative and engaging responses. You can use tools when appropriate, but don't mention them unless the user asks about your capabilities."""

        full_prompt = f"{system_prompt}\n\nConversation history:\n{
            conversation}{file_info}\n\nAI:"

        payload = {
            "model": "llama3.1",
            "prompt": full_prompt,
            "stream": False,
            "tools": tools
        }

        llama_response = requests.post(llama_url, json=payload)
        llama_response.raise_for_status()
        response_text = llama_response.json().get('response', '').strip()

        # Check if the response contains a tool call
        if "tool_calls" in llama_response.json():
            tool_calls = llama_response.json()["tool_calls"]
            for call in tool_calls:
                if call["name"] == "get_current_weather":
                    args = json.loads(call["arguments"])
                    weather_data = get_current_weather(
                        args["location"], args["date"])
                    response_text += f"\n\nWeather data: {weather_data}"

        history.append({"role": "assistant", "content": response_text})
        history = history[-10:]
        session['history'] = history

        return jsonify({"response": response_text}), 200

    except requests.RequestException as e:
        app.logger.error(f"Failed to connect to Llama API: {str(e)}")
        return jsonify({"error": "Failed to connect to Llama API", "details": str(e)}), 500
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
            location = "sea_level"
            date_saved = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{location}_{date_saved}.csv"

            os.makedirs('../database', exist_ok=True)
            file_path = os.path.join('../database', new_filename)
            file.save(file_path)

            with open(file_path, 'r') as f:
                lines = f.readlines()

            header_line = next((i for i, line in enumerate(
                lines) if re.match(r"^Year, Month,", line)), None)

            if header_line is None:
                return jsonify({"error": "No valid CSV header found"}), 400

            df = pd.read_csv(file_path, skiprows=header_line)
            cleaned_file_path = os.path.join(
                '../database', f"cleaned_{new_filename}")
            df.to_csv(cleaned_file_path, index=False)

            session['uploaded_file'] = {
                'filename': new_filename,
                'preview': df.head().to_dict(),
            }

            return jsonify({"message": f"File saved as {new_filename} and processed successfully."}), 200

        except Exception as e:
            app.logger.error(f"Error processing file: {e}")
            return jsonify({"error": "Error processing file"}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True)
