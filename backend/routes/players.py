from flask import Blueprint, jsonify, request

from models import Player, db

players_bp = Blueprint("players", __name__)


def build_player_payload(player):
    total_games = getattr(player, "totalGames", 0)
    total_wins = getattr(player, "totalWins", 0)
    total_losses = getattr(player, "totalLosses", 0)
    total_moves = getattr(player, "totalMoves", 0)
    total_hits = getattr(player, "totalHits", 0)

    accuracy = 0 if total_moves == 0 else total_hits / total_moves

    return {
        "playerId": player.playerId,
        "player_id": player.playerId,
        "id": player.playerId,
        "displayName": player.displayName,
        "username": player.displayName,
        "name": player.displayName,
        "createdAt": player.createdAt,
        "totalGames": total_games,
        "totalWins": total_wins,
        "totalLosses": total_losses,
        "totalMoves": total_moves,
        "games_played": total_games,
        "wins": total_wins,
        "losses": total_losses,
        "total_shots": total_moves,
        "total_hits": total_hits,
        "accuracy": accuracy,
    }


@players_bp.route("/players", methods=["POST"])
def create_player():
    """Create a new player."""
    data = request.get_json(silent=True) or {}

    if "playerId" in data or "id" in data or "player_id" in data:
        return jsonify({"error": "Client may not supply playerId"}), 400

    username = (
        data.get("username")
        or data.get("playerName")
        or data.get("displayName")
        or data.get("name")
        or ""
    )

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "username is required"}), 400

    username = username.strip()

    existing = Player.query.filter_by(displayName=username).first()
    if existing:
        return jsonify({"error": "displayName already taken"}), 409

    player = Player(displayName=username)
    db.session.add(player)
    db.session.commit()

    return jsonify(build_player_payload(player)), 201


@players_bp.route("/players/<int:player_id>", methods=["GET"])
@players_bp.route("/players/<int:player_id>/stats", methods=["GET"])
def get_player(player_id):
    """Get a player's lifetime statistics."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    return jsonify(build_player_payload(player)), 200