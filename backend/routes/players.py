from flask import Blueprint, jsonify, request

from models import Player, db

players_bp = Blueprint("players", __name__)


@players_bp.route("/players", methods=["POST"])
def create_player():
    """Create a new player. Client sends playerName, server generates playerId."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Reject if client tries to supply a playerId
    if "playerId" in data:
        return jsonify({"error": "Client may not supply playerId"}), 400

    player_name = data.get("playerName") or data.get("displayName")
    if not player_name or not player_name.strip():
        return jsonify({"error": "playerName is required"}), 400

    player_name = player_name.strip()

    # Check for duplicate displayName
    existing = Player.query.filter_by(displayName=player_name).first()
    if existing:
        return jsonify({"error": "displayName already taken"}), 409

    # Server generates playerId (UUID)
    player = Player(displayName=player_name)
    db.session.add(player)
    db.session.commit()

    return jsonify(player.to_dict()), 201


@players_bp.route("/players/<player_id>", methods=["GET"])
def get_player(player_id):
    """Get a player's lifetime statistics."""
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    return jsonify(player.to_dict()), 200