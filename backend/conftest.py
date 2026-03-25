import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from config import TestConfig
from models import db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def player_id(client):
    """Create a player and return their player_id."""
    resp = client.post("/api/players", json={"username": "player1"})
    data = resp.get_json()
    return data["player_id"]


@pytest.fixture
def player2_id(client):
    """Create a second player and return their player_id."""
    resp = client.post("/api/players", json={"username": "player2"})
    data = resp.get_json()
    return data["player_id"]


@pytest.fixture
def game_id(client, player_id, player2_id):
    """
    Create a game with 2 players joined and started (status='placing').
    Returns the game id (integer).
    """
    # Create game
    resp = client.post("/api/games", json={"grid_size": 8})
    game = resp.get_json()
    gid = game["id"]

    # Join both players
    client.post(f"/api/games/{gid}/join", json={"player_id": player_id})
    client.post(f"/api/games/{gid}/join", json={"player_id": player2_id})

    # Start game -> transitions to "placing"
    client.post(f"/api/games/{gid}/start")

    return gid