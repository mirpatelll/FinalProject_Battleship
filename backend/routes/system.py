from flask import Blueprint, jsonify

from models import db

system_bp = Blueprint("system", __name__)


@system_bp.route("/reset", methods=["POST"])
def reset():
    """Wipe all data from the database."""
    db.drop_all()
    db.create_all()
    return jsonify({"status": "reset"}), 200