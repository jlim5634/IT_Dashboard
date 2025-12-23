from flask import Blueprint, jsonify
from models import Ticket, Users
from sqlalchemy import func
from datetime import datetime

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():
    tickets = Ticket.query.all()
    
    total_tickets = len(tickets)
    open_tickets = sum(1 for t in tickets if t.status != "Resolved")
    resolved_tickets = total_tickets - open_tickets

    #MTTR (mean time to resolve)
    resolved_time = [
        (t.resolved_at - t.created_at).total_seconds()
        for t in tickets
        if t.status == "Resolved" and t.resolved_at
    ]

    mttr_seconds = sum(resolved_time) / len(resolved_time) if resolved_time else 0

    #convert to hours
    mttr_hours = mttr_seconds / 3600

    #tickets per user
    tickets_per_user = {}
    for user in Users.query.all():
        tickets_per_user[user.name] = Ticket.query.filter_by(submitted_by=user.id).count()

    return jsonify({
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "mttr_hours": round(mttr_hours, 2),
        "tickets_per_user": tickets_per_user
    })