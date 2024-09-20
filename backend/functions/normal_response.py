def normal_response(user_input=None, system_response=None):
    system_prompt = """You are a helpful AI assistant named OceanGPT, specializing in ocean-related topics and data analysis. You should only use tools if the user query cannot be answered without external data or function execution. Otherwise, provide responses based on your built-in knowledge."""

    # Generate a simple response based on user input and system response
    if user_input:
        return f"User said: {user_input}. System said: {system_prompt}."
    else:
        return "No user input was provided."