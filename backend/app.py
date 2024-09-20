from flask import Flask, request, jsonify, session
from flask_cors import CORS
import requests
import json
import os
import traceback
import logging
from datetime import timedelta, datetime
import pandas as pd
from sqlalchemy import create_engine
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

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///your_database.db")
engine = create_engine(DATABASE_URL)


@app.before_request
def make_session_permanent():
    session.permanent = True


def find_cleaned_csv_file():
    """Find the most recently uploaded cleaned CSV file."""
    pattern = '../database/cleaned_sea_level_*.csv'
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)  # Get the most recently created file

def get_first_n_rows_from_csv(file_path, n):
    """Return the first n rows from the cleaned CSV file in the desired JSON format."""
    df = pd.read_csv(file_path)
    df.reset_index(drop=True, inplace=True)  # Reset index for consistent output

    # Generate the columns structure based on DataFrame's columns
    columns = [{"field": col, "headerName": col.capitalize(), "width": 150} for col in df.columns]

    # Generate the rows structure with IDs
    rows = [{"id": idx + 1, **row.to_dict()} for idx, row in df.iterrows()]

    return {"columns": columns, "rows": rows}


@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        prompt = data.get('prompt', None)
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
        
        if prompt.startswith("preview first"):
            n = int(re.search(r'preview first (\d+)', prompt).group(1))  # Extract n from the prompt
            cleaned_file_path = find_cleaned_csv_file()
            if cleaned_file_path:
                result = get_first_n_rows_from_csv(cleaned_file_path, n)
                return jsonify(result), 200
            else:
                return jsonify({"error": "No cleaned CSV file found."}), 404


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

        # Retrieve file context if available
        file_context = session.get('uploaded_file', None)
        if file_context:
            file_info = f"\n\nAn important file was uploaded recently: {file_context['filename']}.\n" \
                f"Here is a preview of the first 5 rows:\n{
                    file_context['preview']}\n"
        else:
            file_info = ""

        system_prompt = "You are a helpful AI assistant named OceanGPT, specializing in ocean-related topics and data analysis. Please provide informative and engaging responses."

        full_prompt = f"{system_prompt}\n\nConversation history:\n{
            conversation}{file_info}\n\nAI:"

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
    app.logger.debug("Entered upload_csv function")

    if 'file' not in request.files:
        app.logger.debug("No file part in request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    app.logger.debug(f"File received: {file.filename}")

    if file.filename == '':
        app.logger.debug("No file selected")
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Define the location and the current date to form the new file name
            location = "sea_level"  # You can change this based on your context
            date_saved = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{location}_{date_saved}.csv"

            # Ensure the 'database' directory exists
            os.makedirs('../database', exist_ok=True)

            # Define the file path to save the uploaded CSV file
            file_path = os.path.join('../database', new_filename)

            # Save the file temporarily for further processing
            file.save(file_path)

            # Now, dynamically find where the actual CSV header starts
            with open(file_path, 'r') as f:
                lines = f.readlines()

            header_line = None
            for i, line in enumerate(lines):
                if re.match(r"^Year, Month,", line):
                    header_line = i
                    break

            if header_line is None:
                app.logger.debug("No valid CSV header found")
                return jsonify({"error": "No valid CSV header found"}), 400

            # Read the CSV data, starting from the header line
            app.logger.debug(f"Reading CSV file from line {header_line}")
            df = pd.read_csv(file_path, skiprows=header_line)

            # Optionally save the cleaned CSV file
            cleaned_file_path = os.path.join(
                '../database', f"cleaned_{new_filename}")
            df.to_csv(cleaned_file_path, index=False)
            app.logger.debug(f"Cleaned CSV saved to {cleaned_file_path}")

            # Store the filename and preview in session for the chatbot
            session['uploaded_file'] = {
                'filename': new_filename,
                'preview': df.head().to_dict(),  # Store preview of first 5 rows
            }

            return jsonify({"message": f"File saved as {new_filename} and processed successfully."}), 200

        except Exception as e:
            app.logger.error(f"Error processing file: {e}")
            return jsonify({"error": "Error processing file"}), 500
    else:
        app.logger.debug("Invalid file format detected")
        return jsonify({"error": "Invalid file format"}), 400


if __name__ == "__main__":
    app.run(debug=True)
