from flask import Blueprint, jsonify, request, current_app

from models import BoardCell, Game, GamePlayer, Move, Player, db
from game_logic import get_board_as_2d_array

system_bp = Blueprint("system", __name__)


@system_bp.route("/reset", methods=["POST"])
def reset():
    """Wipe all data from the database."""
    db.drop_all()
    db.create_all()
    return jsonify({"status": "reset"}), 200


def check_test_mode():
    """Allow test endpoints whenever TEST_MODE is enabled."""
    if not current_app.config.get("TEST_MODE", False):
        return False, (jsonify({"error": "Test mode is not enabled"}), 403)

    return True, None


@system_bp.route("/test/games/<int:game_id>/restart", methods=["POST"])
def restart_game(game_id):
    """Reset a game: clear board, clear moves, status back to waiting.
    Player statistics remain unchanged.
    """
    allowed, error = check_test_mode()
    if not allowed:
        return error

    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    BoardCell.query.filter_by(game_id=game_id).delete()
    Move.query.filter_by(game_id=game_id).delete()

    game_players = GamePlayer.query.filter_by(gameId=game_id).all()
    for gp in game_players:
        gp.is_eliminated = False

    game.status = "waiting"
    game.current_turn_player_id = None
    game.winner_id = None

    db.session.commit()

    return jsonify({
        "status": "restarted",
        "game_id": game_id,
        "gameId": game_id,
    }), 200


@system_bp.route("/test/games/<int:game_id>/ships", methods=["POST"])
def test_place_starting_cells(game_id):
    """Deterministic starting cell placement for testing."""
    allowed, error = check_test_mode()
    if not allowed:
        return error

    data = request.get_json(silent=True) or {}

    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    player_id = data.get("playerId") or data.get("player_id")
    if not player_id:
        return jsonify({"error": "playerId is required"}), 400

    game_player = GamePlayer.query.filter_by(
        gameId=game_id, playerId=player_id
    ).first()
    if not game_player:
        return jsonify({"error": "Player is not in this game"}), 404

    ships = data.get("ships") or data.get("cells") or []
    if not ships:
        return jsonify({"error": "ships array is required"}), 400

    placed_cells = []

    for ship in ships:
        row = ship.get("row")
        col = ship.get("col")

        if row is None:
            row = ship.get("r")
        if col is None:
            col = ship.get("c")

        if row is None or col is None:
            return jsonify({"error": "Each ship needs row and col"}), 400

        if not (0 <= row < game.grid_size and 0 <= col < game.grid_size):
            return jsonify({"error": f"Position ({row},{col}) is out of bounds"}), 400

        cell = BoardCell.query.filter_by(
            game_id=game_id, row=row, col=col
        ).first()

        if cell:
            cell.owner_player_id = player_id
        else:
            cell = BoardCell(
                game_id=game_id,
                row=row,
                col=col,
                owner_player_id=player_id,
            )
            db.session.add(cell)

        placed_cells.append({"row": row, "col": col})

    db.session.commit()

    return jsonify({
        "status": "placed",
        "game_id": game_id,
        "gameId": game_id,
        "player_id": player_id,
        "playerId": player_id,
        "cells": placed_cells,
        "ships": placed_cells,
    }), 200


@system_bp.route("/test/games/<int:game_id>/board/<player_id>", methods=["GET"])
def test_get_board(game_id, player_id):
    """Reveal board state for a specific player (test mode only)."""
    allowed, error = check_test_mode()
    if not allowed:
        return error

    game = Game.query.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    game_player = GamePlayer.query.filter_by(
        gameId=game_id, playerId=player_id
    ).first()
    if not game_player:
        return jsonify({"error": "Player is not in this game"}), 404

    player_cells = BoardCell.query.filter_by(
        game_id=game_id, owner_player_id=player_id
    ).all()

    cells = [{"row": c.row, "col": c.col} for c in player_cells]
    board = get_board_as_2d_array(game) if game.status != "waiting" else None

    return jsonify({
        "game_id": game_id,
        "gameId": game_id,
        "player_id": player_id,
        "playerId": player_id,
        "cells": cells,
        "cell_count": len(cells),
        "board": board,
    }), 200