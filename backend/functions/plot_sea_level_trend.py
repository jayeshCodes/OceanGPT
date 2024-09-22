import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import session
import os

def plot_sea_level_trend(x_column, y_column):
    print("Plotting sea level trend called")
    if 'uploaded_file' not in session:
        return "No file has been uploaded. Please upload a CSV file first."

    file_info = session['uploaded_file']  # Get file info from the session
    file_path = file_info.get('file_path')  # Access the file path directly
    
    if not os.path.exists(file_path):
        return "The uploaded file could not be found. Please upload the file again."

    df = pd.read_csv(file_path)


    if x_column not in df.columns or y_column not in df.columns:
        return f"One or both of the specified columns ({x_column}, {y_column}) are not in the dataset."

    plt.figure(figsize=(10, 6))
    plt.plot(df[x_column], df[y_column])
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.title(f"{y_column} vs {x_column}")
    plt.grid(True)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    print(image_base64)

    return f"data:image/png;base64,{image_base64}"