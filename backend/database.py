from models import db


def init_db(app):
    """Initialize the database and create all tables."""
    db.init_app(app)
    with app.app_context():
        db.create_all()