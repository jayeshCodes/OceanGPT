import pandas as pd
import matplotlib.pyplot as plt
from functions.analyze_sea_level_data import analyze_sea_level_data
from functions.plot_sea_level_trend import plot_sea_level_trend

# Uncomment the following lines if you want to analyze the data
# print(analyze_sea_level_data("tail", 5))
# print(analyze_sea_level_data("describe"))

# Load the dataset
df = pd.read_csv("database/sea_level_20240921_114437.csv", delimiter=',', header=0, skiprows=5, index_col=False)
df.columns = df.columns.str.strip()
print(df.head())

# Strip whitespace from column names

# Print the cleaned column names
print("Cleaned columns in DataFrame:", df.columns)

# Check for missing values
print("Missing values in each column:", df.isnull().sum())

# Attempt to plot the data
try:
    plt.figure(figsize=(10, 6))
    plt.plot(df["Year"], df["Monthly_MSL"], marker='o')  # Now should work
    plt.xlabel("Year")
    plt.ylabel("Linear Trend (meters/year)")
    plt.title("Linear Trend vs Year")
    plt.grid(True)
    plt.show()
except KeyError as e:
    print(f"KeyError: {e}. Available columns: {df.columns.tolist()}")
    # Optionally plot Monthly_MSL instead if Linear_Trend is missing
    if 'Monthly_MSL' in df.columns:
        plt.figure(figsize=(10, 6))
        plt.plot(df["Year"], df["Monthly_MSL"], marker='o')
        plt.xlabel("Year")
        plt.ylabel("Monthly MSL (meters)")
        plt.title("Monthly MSL vs Year")
        plt.grid(True)
        plt.show()