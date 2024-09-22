import pandas as pd
from flask import session
import os

def plot_sea_level_trend(x_column, y_column):
    print("Plotting sea level trend called")
    if 'uploaded_file' not in session:
        return {
            "response": ["No file has been uploaded. Please upload a CSV file first."],
            "data": {"xAxis": [], "series": []}
        }

    file_info = session['uploaded_file']  # Get file info from the session
    file_path = file_info.get('file_path')  # Access the file path directly
    
    if not os.path.exists(file_path):
        return {
            "response": ["The uploaded file could not be found. Please upload the file again."],
            "data": {"xAxis": [], "series": []}
        }

    df = pd.read_csv(file_path)

    if x_column not in df.columns or y_column not in df.columns:
        return {
            "response": [f"One or both of the specified columns ({x_column}, {y_column}) are not in the dataset."],
            "data": {"xAxis": [], "series": []}
        }

    # Sort the dataframe by x_column to ensure proper ordering
    df = df.sort_values(by=x_column)

    x_data = df[x_column].tolist()
    y_data = df[y_column].tolist()

    return {
        "response": [f"Data prepared for plotting {y_column} vs {x_column}"],
        "data": {
            "xAxis": [{"data": x_data}],
            "series": [{"data": y_data, "name": y_column}]
        }
    }