def normal_response(user_input=None, system_response=None):
    system_prompt = """You are a helpful AI assistant named OceanGPT, specializing in ocean-related topics and data analysis. You should only use tools if the user query cannot be answered without external data or function execution. Otherwise, provide responses based on your built-in knowledge."""

    # Generate a simple response based on user input and system response
    if user_input:
        response = f"User said: {user_input}. System replied: {system_response}. Your identity: {system_prompt}."
    else:
        response = "No user input was provided."

    # Append to session history to maintain context
    if 'history' not in session:
        session['history'] = []
    
    session['history'].append({"role": "assistant", "content": response})
    
    return response