import json
import asyncio
import os
from datetime import datetime
import pandas as pd
from flask import session
import ollama
from app.config import Config
from app.exceptions.app_exceptions import FunctionExecutionError, JSONDecodeError

# Import functions from the functions folder
from app.functions.get_current_weather import get_current_weather
from app.functions.analyze_sea_level_data import analyze_sea_level_data
from app.functions.plot_sea_level_trend import plot_sea_level_trend

class ChatService:
    def __init__(self, logger):
        self.logger = logger
        self.client = ollama.AsyncClient()
        
        # Load tools from tools.json
        with open(os.path.join(Config.APP_DIR, 'tools.json'), 'r') as f:
            self.tools = json.load(f)

        self.system_prompt = """
        You are OceanGPT, a helpful AI assistant specializing in ocean-related topics and data analysis. 
        Introduce yourself as OceanGPT when asked about your identity. Use tools only if necessary. Otherwise, respond based on your built-in knowledge. Again, use tools only if necessary (e.g., to analyze data or plot trends).
        """

        # Map function names to imported functions
        self.available_functions = {
            "get_current_weather": get_current_weather,
            "analyze_sea_level_data": analyze_sea_level_data,
            "plot_sea_level_trend": plot_sea_level_trend
        }

    async def process_chat(self, model: str, user_input: str):
        if 'history' not in session:
            session['history'] = []

        messages = session['history'] + [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": user_input
            }
        ]

        response = await self.client.chat(
            model=model,
            messages=messages,
            tools=self.tools,
            format="json"
        )

        self.logger.debug(f"Response from Ollama: {response}")

        response_content = response["message"]["content"]

        if "tool_calls" not in response["message"]:
            self._update_history(user_input, response_content)
            return response_content

        return await self._handle_tool_calls(model, messages, response)

    async def _handle_tool_calls(self, model, messages, response):
        for tool in response["message"]["tool_calls"]:
            function_name = tool["function"]["name"]
            function_to_call = self.available_functions.get(function_name)

            if function_to_call:
                try:
                    function_args = self._parse_function_args(tool["function"]["arguments"])
                    function_response = function_to_call(**function_args)

                    messages.append(
                        {
                            "role": "tool",
                            "content": str(function_response),
                        }
                    )

                    json_data = function_response.get("data")

                    response2 = await self.client.chat(
                        model=model,
                        messages=messages + [{'role': 'user', 'content': str(function_response)}],
                    )

                    final_response = response2["message"]["content"]
                    self._update_history("", final_response)
                    return final_response, json_data

                except JSONDecodeError as e:
                    self.logger.error(f"Error decoding JSON for function arguments: {tool['function']['arguments']}")
                    raise e
                except Exception as e:
                    self.logger.error(f"Error calling function {function_name}: {str(e)}")
                    raise FunctionExecutionError(function_name, str(e))

        # If no function was called, return the original response
        self._update_history(messages[-1]["content"], response["message"]["content"])
        return response["message"]["content"]

    def _parse_function_args(self, args):
        return json.loads(args) if isinstance(args, str) else args

    def _update_history(self, user_input, assistant_response):
        if user_input:
            session['history'].append({"role": "user", "content": user_input})
        session['history'].append({"role": "assistant", "content": assistant_response})

    def reset_conversation(self):
        session.pop('history', None)

    def process_csv(self, file):
        try:
            location = "sea_level"  # Default location
            date_saved = datetime.now().strftime("%Y%m%d")
            new_filename = f"{location}_{date_saved}.csv"

            os.makedirs(Config.DATABASE_DIR, exist_ok=True)
            file_path = os.path.join(Config.DATABASE_DIR, new_filename)

            existing_files = [f for f in os.listdir(Config.DATABASE_DIR) if f.startswith(location)]
            overwrite = False
            existing_file_info = None

            for existing_file in existing_files:
                existing_file_path = os.path.join(Config.DATABASE_DIR, existing_file)
                file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(existing_file_path))).days

                if file_age > 30:
                    overwrite = True
                    break
                else:
                    existing_file_info = {
                        'filename': existing_file,
                        'file_path': existing_file_path,
                        'file_age': file_age,
                    }

            if not existing_files or overwrite:
                file.save(file_path)

                df = pd.read_csv(file_path, delimiter=',', header=0, skiprows=5, index_col=False)
                df.columns = df.columns.str.strip()
                cleaned_file_path = os.path.join(Config.DATABASE_DIR, f"cleaned_{new_filename}")
                df.to_csv(cleaned_file_path, index=False)

                df = pd.read_csv(cleaned_file_path)

                session['uploaded_file'] = {
                    'filename': f"cleaned_{new_filename}",
                    'file_path': cleaned_file_path,
                    'preview': df.head().to_dict(),
                    "context": "a dataset representing sea level data over the years",
                }

                return {"message": f"File saved as {new_filename} and processed successfully."}
            else:
                session['existing_file'] = existing_file_info
                return {"error": "An existing file is still valid and not older than 30 days."}

        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            raise