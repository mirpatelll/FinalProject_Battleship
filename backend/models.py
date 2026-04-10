from datetime import datetime

from database import db


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    games_played = db.Column(db.Integer, nullable=False, default=0)
    wins = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)
    total_shots = db.Column(db.Integer, nullable=False, default=0)
    total_hits = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        accuracy = 0.0 if self.total_shots == 0 else self.total_hits / self.total_shots
        return {
            "player_id": self.id,
            "username": self.username,
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "total_shots": self.total_shots,
            "total_hits": self.total_hits,
            "accuracy": accuracy,
            "games": self.games_played,
            "shots": self.total_shots,
            "hits": self.total_hits,
        }


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    grid_size = db.Column(db.Integer, nullable=False)
    max_players = db.Column(db.Integer, nullable=False, default=2)

    # Common pool expectation
    status = db.Column(db.String(40), nullable=False, default="waiting_setup")

    current_turn_index = db.Column(db.Integer, nullable=False, default=0)
    winner_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        game_players = (
            GamePlayer.query.filter_by(game_id=self.id)
            .order_by(GamePlayer.turn_order.asc())
            .all()
        )

        active_players = [gp for gp in game_players if not gp.is_eliminated]
        current_turn_player_id = None
        if self.status == "playing" and active_players:
            idx = self.current_turn_index % len(active_players)
            current_turn_player_id = active_players[idx].player_id

        players_payload = []
        for gp in game_players:
            ships_remaining = Ship.query.filter_by(
                game_id=self.id,
                player_id=gp.player_id,
                is_sunk=False,
            ).count()

            players_payload.append(
                {
                    "player_id": gp.player_id,
                    "turn_order": gp.turn_order,
                    "ships_placed": gp.ships_placed,
                    "is_eliminated": gp.is_eliminated,
                    "ships_remaining": ships_remaining,
                }
            )

        return {
            "game_id": self.id,
            "grid_size": self.grid_size,
            "max_players": self.max_players,
            "status": self.status,
            "players": players_payload,
            "current_turn_index": self.current_turn_index,
            "current_turn_player_id": current_turn_player_id,
            "active_players": len(active_players),
            "winner_id": self.winner_id,
            "total_moves": Move.query.filter_by(game_id=self.id).count(),
        }


class GamePlayer(db.Model):
    __tablename__ = "game_players"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False, index=True)

    turn_order = db.Column(db.Integer, nullable=False, default=0)
    ships_placed = db.Column(db.Boolean, nullable=False, default=False)
    is_eliminated = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint("game_id", "player_id", name="uq_game_player"),
    )


class Ship(db.Model):
    __tablename__ = "ships"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False, index=True)

    row = db.Column(db.Integer, nullable=False)
    col = db.Column(db.Integer, nullable=False)
    is_sunk = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint("game_id", "player_id", "row", "col", name="uq_ship_cell"),
    )


class Move(db.Model):
    __tablename__ = "moves"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False, index=True)

    row = db.Column(db.Integer, nullable=False)
    col = db.Column(db.Integer, nullable=False)
    result = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "move_id": self.id,
            "player_id": self.player_id,
            "row": self.row,
            "col": self.col,
            "result": self.result,
            "timestamp": self.created_at.isoformat() + "Z",
        }