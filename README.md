# Virus Outbreak

**CPSC 3750 Final Project — Clemson University**

A turn-based multiplayer territory control game. Players compete to infect and control cells on a grid board. Each player starts with one infected cell and spreads to adjacent cells on their turn. Players are eliminated when they lose all cells. The last player standing wins.

## Architecture Overview

### Tech Stack
- **Backend:** Python 3 + Flask
- **Database:** SQLite via SQLAlchemy ORM (swappable to MySQL/PostgreSQL)
- **Testing:** pytest

### Project Structure
```
virus-outbreak/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config.py           # Configuration (DB URI, game defaults)
│   ├── database.py         # SQLAlchemy initialization
│   ├── models.py           # ORM models (6 tables)
│   ├── game_logic.py       # Core rules engine
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── games.py        # Game endpoints (create, join, start, move, state)
│   │   └── players.py      # Player endpoints (create, stats)
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_phase1.py  # Phase 1 test suite (39 tests)
│   └── requirements.txt
├── frontend/               # Phase 2
│   ├── index.html
│   ├── style.css
│   └── app.js
├── venv/                   # Virtual environment (not committed)
└── README.md
```

### Database Schema

Six relational tables with foreign key constraints:

- **users** — Player accounts with unique usernames
- **games** — Game instances tracking status (waiting → active → finished), grid size, current turn, and winner
- **game_players** — Join table linking players to games with turn order and elimination status. Unique constraint on (game_id, player_id) prevents duplicate joins
- **board_cells** — Grid cells with ownership tracking. Unique constraint on (game_id, row, col) ensures one cell per position
- **moves** — Complete move log with source, target, and ISO 8601 timestamps
- **player_stats** — Lifetime statistics per player (games played, wins, moves made, cells captured)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/players` | Create a player |
| GET | `/players/<id>/stats` | Get player statistics |
| POST | `/games` | Create a game (configurable grid size) |
| POST | `/games/<id>/join` | Join a game |
| POST | `/games/<id>/start` | Start a game (requires 2+ players) |
| POST | `/games/<id>/move` | Make a move (server validates all rules) |
| GET | `/games/<id>` | Get full game state (board, players, moves) |

### Game Rules

- Players take turns in strict rotation order
- On each turn, a player spreads their virus to one adjacent cell (up/down/left/right only)
- A player can capture empty cells or opponent cells
- A player is eliminated when they own zero cells
- Eliminated players are skipped in turn rotation
- The game ends when only one player remains
- All rules are enforced server-side; illegal moves are rejected with descriptive errors

## Testing Strategy

### Approach
All game rules are enforced and tested server-side via automated API tests. Tests use an in-memory SQLite database so each test runs in isolation with a fresh database.

### Test Categories
1. **Player CRUD** — Creation, duplicate username rejection, empty username rejection, stats retrieval, not-found handling
2. **Game Creation** — Default grid size, custom grid size, invalid grid size rejection (too small/large)
3. **Join Logic** — Successful join, turn order assignment, duplicate join rejection, wrong status rejection, game/player not found
4. **Game Start** — Status transition, board creation, starting cell assignment, insufficient players rejection, games_played stat increment
5. **Move Validation** — Valid moves to empty cells, wrong turn rejection, unowned source rejection, non-adjacent rejection, out-of-bounds rejection, own-cell target rejection, timestamp logging
6. **Turn Rotation** — Turn advances after move, wraps around after last player, three-player rotation
7. **Game State** — Waiting state (no board), active state (full board), not-found handling, move history, cell count tracking
8. **Stats Tracking** — Increments on move, increments on game start, accumulates across multiple moves

### Running Tests
```bash
cd backend
source ../venv/bin/activate
pytest tests/test_phase1.py -v
```

Current status: **39 tests, all passing**

## Setup & Run

```bash
# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run server
python app.py
```

Server runs at `http://localhost:5000`.

## AI Tools Used
- Claude (Anthropic) — Architecture design, code generation, test planning

## Team Members
- [Name 1] — St Angelo Davis - Frontend Implementation
- [Name 2] — Mir Patel - Backend Implementation