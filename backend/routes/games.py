from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from config import Config
from models import Game, GamePlayer, Move, Player, Ship, db

games_bp = Blueprint("games", __name__)


def _pid(data):
    """Extract player_id from request body — accepts snake_case or camelCase."""
    return data.get("player_id") or data.get("playerId")


# ------------------------------------------------------------------
# POST /api/games  — Create a new game
# ------------------------------------------------------------------
@games_bp.route("/games", methods=["POST"])
def create_game():
    data = request.get_json(silent=True) or {}

    grid_size = data.get("grid_size") or data.get("gridSize") or Config.DEFAULT_GRID_SIZE
    max_players = data.get("max_players") or data.get("maxPlayers") or 2

    if not isinstance(grid_size, int) or not (Config.MIN_GRID_SIZE <= grid_size <= Config.MAX_GRID_SIZE):
        return jsonify({"error": f"grid_size must be between {Config.MIN_GRID_SIZE} and {Config.MAX_GRID_SIZE}"}), 400

    if not isinstance(max_players, int) or max_players < 1:
        return jsonify({"error": "max_players must be >= 1"}), 400

    creator_id = _pid(data) or data.get("creator_id") or data.get("creatorId")

    if creator_id:
        creator = db.session.get(Player, creator_id)
        if not creator:
            return jsonify({"error": "Creator not found"}), 404

    game = Game(grid_size=grid_size, max_players=max_players)
    db.session.add(game)
    db.session.flush()

    if creator_id:
        gp = GamePlayer(game_id=game.id, player_id=creator_id, turn_order=0)
        db.session.add(gp)

    db.session.commit()
    return jsonify(game.to_dict()), 201


# ------------------------------------------------------------------
# POST /api/games/<id>/join
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>/join", methods=["POST"])
def join_game(game_id):
    data = request.get_json(silent=True) or {}

    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game.status != "waiting":
        return jsonify({"error": "Game is not accepting players"}), 409

    # Accept player_id or playerName lookup
    player_id = _pid(data)
    player_name = data.get("playerName") or data.get("username")

    if not player_id and player_name:
        p = Player.query.filter_by(username=player_name).first()
        if p:
            player_id = p.player_id

    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Invalid player_id"}), 404

    if GamePlayer.query.filter_by(game_id=game_id, player_id=player_id).first():
        return jsonify({"error": "Player already in this game"}), 409

    current_count = GamePlayer.query.filter_by(game_id=game_id).count()
    if current_count >= game.max_players:
        return jsonify({"error": "Game is full"}), 409

    gp = GamePlayer(game_id=game_id, player_id=player_id, turn_order=current_count)
    db.session.add(gp)
    db.session.commit()

    return jsonify(gp.to_dict()), 200


# ------------------------------------------------------------------
# GET /api/games/<id>
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>", methods=["GET"])
def get_game(game_id):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game.to_dict()), 200


# ------------------------------------------------------------------
# POST /api/games/<id>/start
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>/start", methods=["POST"])
def start_game(game_id):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game.status != "waiting":
        return jsonify({"error": "Game already started or finished"}), 400

    if GamePlayer.query.filter_by(game_id=game_id).count() < 2:
        return jsonify({"error": "Need at least 2 players to start"}), 400

    game.status = "placing"
    db.session.commit()
    return jsonify(game.to_dict()), 200


# ------------------------------------------------------------------
# POST /api/games/<id>/place  — Place exactly 3 ships
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>/place", methods=["POST"])
def place_ships(game_id):
    data = request.get_json(silent=True) or {}

    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game.status not in ("waiting", "placing"):
        return jsonify({"error": "Ships can only be placed before the game is active"}), 409

    player_id = _pid(data)
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Invalid player_id"}), 403

    gp = GamePlayer.query.filter_by(game_id=game_id, player_id=player_id).first()
    if not gp:
        return jsonify({"error": "Player is not in this game"}), 403

    if gp.ships_placed:
        return jsonify({"error": "Ships already placed"}), 400

    ships = data.get("ships") or []
    if not isinstance(ships, list) or len(ships) != 3:
        return jsonify({"error": "Must place exactly 3 ships"}), 400

    positions = set()
    for i, s in enumerate(ships):
        row, col = s.get("row"), s.get("col")
        if row is None or col is None:
            return jsonify({"error": f"Ship {i} missing row or col"}), 400
        if not (0 <= row < game.grid_size and 0 <= col < game.grid_size):
            return jsonify({"error": f"Ship at ({row},{col}) out of bounds"}), 400
        if (row, col) in positions:
            return jsonify({"error": f"Duplicate position ({row},{col})"}), 400
        positions.add((row, col))

    placed = []
    for row, col in positions:
        db.session.add(Ship(game_id=game_id, player_id=player_id, row=row, col=col))
        placed.append({"row": row, "col": col})

    gp.ships_placed = True

    all_gps = GamePlayer.query.filter_by(game_id=game_id).all()
    if len(all_gps) >= 2 and all(g.ships_placed for g in all_gps):
        game.status = "active"
        game.current_turn_index = 0

    db.session.commit()
    return jsonify({"status": "placed", "game_id": game_id, "player_id": player_id, "ships": placed}), 200


# ------------------------------------------------------------------
# POST /api/games/<id>/fire
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>/fire", methods=["POST"])
def fire(game_id):
    data = request.get_json(silent=True) or {}

    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game.status == "finished":
        return jsonify({"error": "Game is already finished"}), 410

    if game.status != "active":
        return jsonify({"error": "Game is not active. All players must place ships before firing."}), 409

    player_id = _pid(data)
    row = data.get("row")
    col = data.get("col")

    if player_id is None or row is None or col is None:
        return jsonify({"error": "player_id, row, and col are required"}), 400

    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Invalid player_id"}), 403

    gp = GamePlayer.query.filter_by(game_id=game_id, player_id=player_id).first()
    if not gp:
        return jsonify({"error": "Player is not in this game"}), 403

    active_players = (
        GamePlayer.query
        .filter_by(game_id=game_id, is_eliminated=False)
        .order_by(GamePlayer.turn_order)
        .all()
    )

    if not active_players:
        return jsonify({"error": "No active players"}), 400

    current_player = active_players[game.current_turn_index % len(active_players)]
    if current_player.player_id != player_id:
        return jsonify({"error": "It is not your turn"}), 403

    if not (0 <= row < game.grid_size and 0 <= col < game.grid_size):
        return jsonify({"error": "Coordinates out of bounds"}), 400

    if Move.query.filter_by(game_id=game_id, player_id=player_id, row=row, col=col).first():
        return jsonify({"error": "Already fired at this location"}), 400

    hit_ship = Ship.query.filter(
        Ship.game_id == game_id,
        Ship.player_id != player_id,
        Ship.row == row,
        Ship.col == col,
        Ship.is_sunk == False,
    ).first()

    result = "hit" if hit_ship else "miss"
    if hit_ship:
        hit_ship.is_sunk = True

    db.session.add(Move(game_id=game_id, player_id=player_id, row=row, col=col, result=result))

    player.total_shots += 1
    if result == "hit":
        player.total_hits += 1

    # Check eliminations
    for other_gp in active_players:
        if other_gp.player_id == player_id or other_gp.is_eliminated:
            continue
        if Ship.query.filter_by(game_id=game_id, player_id=other_gp.player_id, is_sunk=False).count() == 0:
            other_gp.is_eliminated = True

    # Refresh active list after eliminations
    active_players = (
        GamePlayer.query
        .filter_by(game_id=game_id, is_eliminated=False)
        .order_by(GamePlayer.turn_order)
        .all()
    )

    next_player_id = None
    if len(active_players) <= 1:
        game.status = "finished"
        if active_players:
            game.winner_id = active_players[0].player_id
        for g in GamePlayer.query.filter_by(game_id=game_id).all():
            p = db.session.get(Player, g.player_id)
            if p:
                p.games_played += 1
                if g.player_id == game.winner_id:
                    p.wins += 1
                else:
                    p.losses += 1
    else:
        current_idx = next((i for i, ap in enumerate(active_players) if ap.player_id == player_id), 0)
        next_idx = (current_idx + 1) % len(active_players)
        game.current_turn_index = active_players[next_idx].turn_order
        next_player_id = active_players[next_idx].player_id

    db.session.commit()

    response = {"result": result, "next_player_id": next_player_id, "game_status": game.status}
    if game.status == "finished":
        response["winner_id"] = game.winner_id
    return jsonify(response), 200


# ------------------------------------------------------------------
# GET /api/games/<id>/moves
# ------------------------------------------------------------------
@games_bp.route("/games/<int:game_id>/moves", methods=["GET"])
def get_moves(game_id):
    game = db.session.get(Game, game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    moves = Move.query.filter_by(game_id=game_id).order_by(Move.id).all()
    return jsonify([m.to_dict() for m in moves]), 200
