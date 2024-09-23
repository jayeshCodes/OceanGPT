class ChatServiceError(Exception):
    """Base exception class for ChatService errors."""
    pass

class FunctionExecutionError(ChatServiceError):
    """Exception raised when there's an error executing a function."""
    
    def __init__(self, function_name: str, error_message: str):
        self.function_name = function_name
        self.error_message = error_message
        super().__init__(f"Error executing function '{function_name}': {error_message}")

class JSONDecodeError(ChatServiceError):
    """Exception raised when there's an error decoding JSON."""
    
    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(f"JSON decode error: {error_message}")

class FileProcessingError(ChatServiceError):
    """Exception raised when there's an error processing a file."""
    
    def __init__(self, file_name: str, error_message: str):
        self.file_name = file_name
        self.error_message = error_message
        super().__init__(f"Error processing file '{file_name}': {error_message}")

class InvalidInputError(ChatServiceError):
    """Exception raised when the input provided is invalid."""
    
    def __init__(self, input_name: str, error_message: str):
        self.input_name = input_name
        self.error_message = error_message
        super().__init__(f"Invalid input for '{input_name}': {error_message}")

class OllamaClientError(ChatServiceError):
    """Exception raised when there's an error with the Ollama client."""
    
    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(f"Ollama client error: {error_message}")