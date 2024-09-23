import pandas as pd
from flask import session, jsonify
import os


def analyze_sea_level_data(operation, n=5):
    print("Analyzing sea level data called")
    if 'uploaded_file' not in session:
        return {"response": ["No file has been uploaded. Please upload a CSV file first."], "data": []}

    file_info = session['uploaded_file']  # Get file info from the session
    file_path = file_info.get('file_path')  # Access the file path directly

    if not os.path.exists(file_path):
        return {"response": ["The uploaded file could not be found. Please upload the file again."], "data": []}

    df = pd.read_csv(file_path)

    n = int(n)

    if operation == "head":
        result = df.head(n)
    elif operation == "tail":
        result = df.tail(n)
    elif operation == "describe":
        result = df.describe()
    else:
        return {"response": ["Invalid operation. Please choose 'head', 'tail', or 'describe'."], "data": []}

    # Prepare the response and data format
    response_message = "Here are the results of your operation."
    # Convert the DataFrame to a list of dictionaries
    data_list = result.to_dict(orient="records")

    return {
        "response": [response_message],
        "data": data_list
    }
