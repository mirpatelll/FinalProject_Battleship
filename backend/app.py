from flask import Flask

from config import Config
from database import init_db
from routes.games import games_bp
from routes.players import players_bp


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database and create tables
    init_db(app)

    # Register blueprints
    app.register_blueprint(games_bp)
    app.register_blueprint(players_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)