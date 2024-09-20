import json
import ollama
import asyncio


#Here we have 3 functions: sealevel, antonuyms, and flight
import requests
def get_current_weather(location, date):
    """Get the current weather in a given location and date"""
    url='https://api.weatherapi.com/v1/current.json?key=f2b1a3991c524713847144853231406&q='+location+'&dt='+date
    response = requests.get(url)
    if response.status_code == 200:
      # Loading the response data into a dictionary variable
      weather_info = json.loads(response.text)
    else:
      print("Failed to retrieve data")
    return json.dumps(weather_info)
    
def get_sealevel_location(location):
    
    return "yes, I have sea level info at "+location
    
def get_antonyms(word: str) -> str:
    "Get the antonyms of the any given word"

    words = {
        "hot": "cold",
        "small": "big",
        "weak": "strong",
        "light": "dark",
        "lighten": "darken",
        "dark": "bright",
    }

    return json.dumps(words.get(word, "Not available in database"))


# In a real application, this would fetch data from a live database or API
def get_flight_times(departure: str, arrival: str) -> str:
    flights = {
        "NYC-LAX": {
            "departure": "08:00 AM",
            "arrival": "11:30 AM",
            "duration": "5h 30m",
        },
        "LAX-NYC": {
            "departure": "02:00 PM",
            "arrival": "10:30 PM",
            "duration": "5h 30m",
        },
        "JFK-LAX": {
            "departure": "08:00 AM",
            "arrival": "11:30 AM",
            "duration": "5h 30m",
        },
        "LAX-JFK": {
            "departure": "02:00 PM",
            "arrival": "10:30 PM",
            "duration": "5h 30m",
        },
        "LHR-JFK": {
            "departure": "10:00 AM",
            "arrival": "01:00 PM",
            "duration": "8h 00m",
        },
        "JFK-LHR": {
            "departure": "09:00 PM",
            "arrival": "09:00 AM",
            "duration": "7h 00m",
        },
        "CDG-DXB": {
            "departure": "11:00 AM",
            "arrival": "08:00 PM",
            "duration": "6h 00m",
        },
        "DXB-CDG": {
            "departure": "03:00 AM",
            "arrival": "07:30 AM",
            "duration": "7h 30m",
        },
    }

    key = f"{departure}-{arrival}".upper()
    return json.dumps(flights.get(key, {"error": "Flight not found"}))

tools=[
        # Define available function#1
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location and date",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA, or London, UK",
                        },

                        "date": {
                            "type": "string",
                            "description": "The date like, today, tomorrow, Monday, next Tuesday, Friday, etc",
                        },
                    },
                    "required": ["location", "date"],
                },
            },
        },
        #function#2
        {
            "type": "function",
            "function": {
                "name": "get_flight_times",
                "description": "Get the flight times between two cities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "departure": {
                            "type": "string",
                            "description": "The departure airport 3-letter code, like JFK, LAX, CDG, DXB",
                        },
                        "arrival": {
                            "type": "string",
                            "description": "The arrival 3-letter airport code, JFK, LAX, CDG, DXB",
                        },
                    },
                    "required": ["departure", "arrival"],
                },
            },
        },
                #function#3
        {
            "type": "function",
            "function": {
                "name": "get_antonyms",
                "description": "Get the antonyms of any given words",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "word": {
                            "type": "string",
                            "description": "The word for which the opposite is required.",
                        },
                    },
                    "required": ["word"],
                },
            },
        },
             #function#4
        {
            "type": "function",
            "function": {
                "name": "get_sealevel_location",
                "description": "Get the sea level locaition of city, state and country",
                "parameters": {
                    "type": "object",
                    "properties": {
                            "city": {
                                "type": "array",
                                "description": "check if there is a city name, if so, just get the city name"
                            },
                            "state": {
                                "type": "array",
                                "description": "if a city in USA if given, just add the 2-letter state, if no, just none, the lengthe is 2"
                            },
                            "country": {
                                "type": "array",
                                "description": "a location country"
                            },
                            "database": {
                                "type": "string",
                                "enum": ["past", "future"],
                                "description":"check the user is asking the past historical sea level change, or, the predicted future sea level; the current year is 2024"
                                },
                            "start_year": {
                                "type": "number",
                                "description": "start year, do not assume"
                            },
                            "end_year": {
                                "type": "number",
                                "description": "end year, do not assume"
                            },
                            
                    },
                    "required": ["country"],
                },
            },
        },
    ]
        
async def run(model: str, user_input: str):
    client = ollama.AsyncClient()
    # Initialize conversation with a user query
    messages = [
        {
            "role": "user",
            "content": user_input,
            # "content": "What is the capital of India?",
        }
    ]

    # First API call: Send the query and function description to the model
    response = await client.chat(
        model=model,
        messages=messages,
        tools=tools,
        format="json"
    )

    # print(f"Response: {response}")

    # Add the model's response to the conversation history
    messages.append(response["message"])

    # print(f"Conversation history:\n{messages}")

    # Check if the model decided to use the provided function
    if not response["message"].get("tool_calls"):
        print("\nThe model didn't use the function. Its response was:")
        print(response["message"]["content"])
        return

    if response["message"].get("tool_calls"):
        # print(f"\nThe model used some tools")
        available_functions = {
            "get_flight_times": get_flight_times,
            "get_antonyms": get_antonyms,
            "get_sealevel_location": get_sealevel_location,
            "get_current_weather": get_current_weather
        }
        # print(f"\navailable_function: {available_functions}")
        for tool in response["message"]["tool_calls"]:
            # print(f"available tools: {tool}")
            # tool: {'function': {'name': 'get_flight_times', 'arguments': {'arrival': 'LAX', 'departure': 'NYC'}}}
            function_to_call = available_functions[tool["function"]["name"]]
            
            print(f"function to call: {function_to_call}")

            if function_to_call == get_flight_times:
                function_response = function_to_call(
                    tool["function"]["arguments"]["departure"],
                    tool["function"]["arguments"]["arrival"],
                )
                print(tool)
                print(f"function response: {function_response}")

            elif function_to_call == get_antonyms:
                function_response = function_to_call(
                    tool["function"]["arguments"]["word"],
                )
                print(f"function response: {function_response}")
                
                
            elif function_to_call == get_sealevel_location:
                function_response="yes, we have sea level info"
                
                print(f"function response: {function_response}")
                
            elif function_to_call == get_current_weather:
                function_response = function_to_call(
                    tool["function"]["arguments"]["location"],
                    tool["function"]["arguments"]["date"],
                )



            response2 = await client.chat(
                model=model,
                messages=[{'role': 'user', 'content': function_response}],
                #tools=tools,
                #format="json"
            )
            print(response2['message']['content'])

            messages.append(
                {
                    "role": "tool",
                    "content": function_response,
                }
            )

            #print(messages)
while True:
    user_input = input("\n Please ask=> ")
    #if not user_input:
    #    user_input = "What is the flight time from NYC to LAX?"
    if user_input.lower() == "exit":
        break

    #asyncio.run(run("llama3-groq-tool-use", user_input))
    asyncio.run(run("llama3.1", user_input))