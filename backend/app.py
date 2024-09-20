from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import os
import traceback
import logging
from datetime import timedelta
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your_fallback_secret_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

CORS(app, supports_credentials=True)

logging.basicConfig(level=logging.DEBUG)

llama_url = "http://localhost:11434/api/generate"

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///your_database.db")
engine = create_engine(DATABASE_URL)


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        prompt = data.get('prompt', None)
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        app.logger.debug(f"Received prompt: {prompt}")
        app.logger.debug(f"Session before processing: {session}")

        # Initialize or retrieve the conversation history
        history = session.get('history', [])
        app.logger.debug(f"Current history: {history}")

        # Add the new user input to the conversation history
        history.append({"role": "user", "content": prompt})

        # Create the complete conversation string to send to Llama
        conversation = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in history])

        system_prompt = "You are a helpful AI assistant named OceanGPT, specializing in ocean-related topics and data analysis. Please provide informative and engaging responses."

        full_prompt = f"{system_prompt}\n\nConversation history:\n{
            conversation}\n\nAI:"

        payload = {
            "model": "llama3.1",
            "prompt": full_prompt,
            "stream": False
        }

        app.logger.debug(f"Sending payload to Llama: {payload}")

        llama_response = requests.post(llama_url, json=payload)
        llama_response.raise_for_status()
        response_text = llama_response.json().get('response', '').strip()

        app.logger.debug(f"Received response from Llama: {response_text}")

        # Add bot response to conversation history
        history.append({"role": "assistant", "content": response_text})

        # Limit the history to last 10 messages to prevent the context from becoming too long
        history = history[-10:]

        # Save the updated history in the session
        session['history'] = history
        app.logger.debug(f"Session after processing: {session}")

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
    session.pop('history', None)  # Clear the session history
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
            df = pd.read_csv(file)
            df.to_sql('your_table_name', con=engine,
                      if_exists='append', index=False)
            return jsonify({"message": "File successfully uploaded and saved to database"}), 200
        except Exception as e:
            app.logger.error(f"Error processing file: {e}")
            return jsonify({"error": "Error processing file"}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True)
