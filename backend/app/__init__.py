from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.controllers.chat_controller import chat_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, supports_credentials=True)
    
    app.register_blueprint(chat_bp)
    
    return app