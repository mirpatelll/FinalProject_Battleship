from flask import Blueprint, jsonify, request

from models import Player, db

players_bp = Blueprint("players", __name__)


def _valid_username(username):
    if not isinstance(username, str):
        return False
    username = username.strip()
    if not username:
        return False
    return username.replace("_", "").isalnum()


@players_bp.route("/players", methods=["POST"])
def create_player():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    if username is None:
        username = data.get("playerName")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "bad_request", "message": "username is required"}), 400

    username = username.strip()

    if not _valid_username(username):
        return jsonify({"error": "bad_request", "message": "invalid username"}), 400

    existing = Player.query.filter_by(username=username).first()
    if existing:
        return (
            jsonify(
                {
                    "error": "conflict",
                    "message": "username already taken",
                    "player_id": existing.id,
                    "username": existing.username,
                    "displayName": existing.username,
                }
            ),
            409,
        )

    player = Player(username=username)
    db.session.add(player)
    db.session.commit()

    return (
        jsonify(
            {
                "player_id": player.id,
                "username": player.username,
                "displayName": player.username,
            }
        ),
        201,
    )


@players_bp.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player_stats(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "not_found", "message": "player not found"}), 404

    total_shots = player.total_shots or 0
    total_hits = player.total_hits or 0
    accuracy = 0.0 if total_shots == 0 else total_hits / total_shots

    return (
        jsonify(
            {
                "player_id": player.id,
                "username": player.username,
                "games_played": player.games_played or 0,
                "wins": player.wins or 0,
                "losses": player.losses or 0,
                "total_shots": total_shots,
                "total_hits": total_hits,
                "accuracy": accuracy,
                "games": player.games_played or 0,
                "shots": total_shots,
                "hits": total_hits,
            }
        ),
        200,
    )

