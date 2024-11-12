from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.routes import blueprint as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app