import pandas as pd
from flask import session, jsonify
import os
import logging

def analyze_sea_level_data(operation, n=5):
    logging.info("Analyzing sea level data called")
    
    if 'uploaded_file' not in session:
        logging.warning("No file in session")
        return {"response": ["No file has been uploaded. Please upload a CSV file first."], "data": []}

    file_info = session.get('uploaded_file', {})
    file_path = file_info.get('file_path')

    if not file_path:
        logging.error("File path missing from session data")
        return {"response": ["File information is incomplete. Please upload the file again."], "data": []}

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return {"response": ["The uploaded file could not be found. Please upload the file again."], "data": []}

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        return {"response": ["Error reading the CSV file. Please ensure it's a valid sea level data file."], "data": []}

    try:
        n = int(n)
    except ValueError:
        logging.warning(f"Invalid value for n: {n}")
        n = 5  # Default to 5 if conversion fails

    if operation == "head":
        result = df.head(n)
    elif operation == "tail":
        result = df.tail(n)
    elif operation == "describe":
        result = df.describe()
    else:
        logging.warning(f"Invalid operation requested: {operation}")
        return {"response": ["Invalid operation. Please choose 'head', 'tail', or 'describe'."], "data": []}

    # Prepare the response and data format
    response_message = f"Here are the results of your '{operation}' operation on {file_info.get('filename', 'the uploaded file')}."
    
    # Convert the DataFrame to a list of dictionaries
    data_list = result.to_dict(orient="records")

    logging.info(f"Analysis completed: {operation}")
    return {
        "response": [response_message],
        "data": data_list
    }