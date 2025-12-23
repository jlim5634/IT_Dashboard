from flask import Blueprint, jsonify
from models import SystemState
from app import db

system_bp = Blueprint("system", __name__)


@system_bp.route('/gameday/toggle', methods=['POST']) 
def toggle_gameday(): #allows turning on/off by POST request
    state = get_system_state()
    state.gameday = not state.gameday
    db.session.commit()
    return jsonify({"gameday": state.gameday})


def get_system_state():
    state = SystemState.query.first()
    if not state:
        state = SystemState(gameday=False)
        db.session.add(state)
        db.session.commit()
    return state

def is_gameday():
    return get_system_state().gameday