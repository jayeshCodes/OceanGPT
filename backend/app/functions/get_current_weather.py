import json
import requests
from datetime import datetime

def get_current_weather(location, date="today"):
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        url = f'https://api.weatherapi.com/v1/current.json?key=f2b1a3991c524713847144853231406&q={location}&dt={date}'
        response = requests.get(url)

        if response.status_code == 200:
            weather_info = response.json()

        else:
            weather_info = {"error": "Failed to retrieve data"}


        return json.dumps(weather_info)

    except Exception as e:
        return json.dumps({"error": str(e)})
