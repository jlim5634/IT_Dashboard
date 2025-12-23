from flask import Blueprint, request, jsonify
from models import Ticket, Users, db
from datetime import datetime
from sqlalchemy import case
from routes.system import is_gameday

tickets_bp = Blueprint("tickets", __name__)

GAME_DAY = False

#create new ticket
@tickets_bp.route("/tickets/new", methods=["POST"])#POST used to send data to server
def create_ticket():
    data = request.get_json()
    if not all (k in data for k in ("title", "category", "submitted_by")):
        return jsonify({"error": "Missing required fields"}), 400

    priority = "Game Day Critical" if is_gameday() else data.get("priority", "normal")
    
    ticket = Ticket(
        title=data["title"],
        description=data.get("description", ""),
        category=data["category"],
        priority=priority,
        submitted_by=data["submitted_by"],
        assigned_to=data.get("assigned_to")
    )

    
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket created", "ticket_id": ticket.id})

#list all tickets
@tickets_bp.route('/tickets', methods=['GET'])
def list_tickets():

    if GAME_DAY:
        #sort game day critical tickets first then by ID desc
        tickets = Ticket.query.order_by(
            case(
                (Ticket.priority == "Game Day Critical", 1),
                else_=0
            ).desc(),
            Ticket.id.desc()
        ).all()
    else:
        tickets = Ticket.query.order_by(Ticket.id.desc()).all()

    result = []
    for t in tickets:
        result.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "submitted_by": t.submitter.name if t.submitter else None,
            "assigned_to": t.assigned_user.name if t.assigned_user else None,
            "created_at": t.created_at.isoformat(),
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None
        })

   
    return jsonify(result)


#update a ticket (assign or resolve)
@tickets_bp.route('/tickets/update/<int:ticket_id>', methods=['POST'])
def update_ticket(ticket_id):

    VALID_STATUSES = ["Open", "In Progress", "Resolved"]
    data = request.get_json()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    if "assigned_to" in data:
        ticket.assigned_to = data["assigned_to"]

    if "status" in data: #enfoorce valid ticket statuses
        ticket.status = data["status"]
        
        if data["status"].lower() == "resolved":
            ticket.resolved_at = datetime.utcnow()
        
        if data["status"] not in VALID_STATUSES:
            return jsonify({"error": "Invalid stratus"}), 400
        
        ticket.status = data["status"]

    if "status" in data and data["status"].lower() == "resolved": #to prevent resolving unassigned tickets
        if not ticket.assigned_to:
            return jsonify({"error": "Ticket must be assigned before resolving"}), 400

    if "assigned_to" in data:
        ticket.assigned_to = data["assigned_to"]
        if ticket.status == "Open":
            ticket.status = "In Progress"
    

    db.session.commit()

    return jsonify({"message": "Ticket updated", "ticket_id": ticket.id})

@tickets_bp.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "Ticket deleted"})

