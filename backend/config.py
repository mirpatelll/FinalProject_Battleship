import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'battleship.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TEST_PASSWORD = os.getenv("TEST_PASSWORD", "clemson-test-2026")

    MIN_GRID_SIZE = 5
    MAX_GRID_SIZE = 15
    DEFAULT_GRID_SIZE = 8
    DEFAULT_SHIP_COUNT = 3