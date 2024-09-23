from flask import Blueprint, jsonify, request, session
from app.services.chat_service import ChatService
import asyncio
import logging

logger = logging.getLogger('chat_service')

chat_bp = Blueprint('chat', __name__)
chat_service = ChatService(__name__)
logger.setLevel(logging.DEBUG)


@chat_bp.route('/chat', methods=['POST'])
@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("prompt", "")
    model = data.get("model", "llama3.1")

    if not user_input:
        return jsonify({"error": "No user input provided"}), 400

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            chat_service.process_chat(model, user_input))
        return jsonify({"response": response}), 200
    except Exception as e:
        chat_bp.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@chat_bp.route('/reset', methods=['POST'])
def reset():
    chat_service.reset_conversation()
    return jsonify({"message": "Conversation history cleared"}), 200


@chat_bp.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            result = chat_service.process_csv(file)
            return jsonify(result), 200 if "message" in result else 400
        except Exception as e:
            return jsonify({"error": "Error processing file", "details": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400