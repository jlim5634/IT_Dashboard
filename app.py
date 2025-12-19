from flask import Flask, request, jsonify
import os
from models import Users, Ticket, db #import SQLAlchemy instance and models
from datetime import datetime


app = Flask(__name__) #starts flask app


#to config database. use SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///it_ops.db' #tells SQLAlchemy where to store the database. local file it_ops.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) #connects db instance from models.py to Flask app

#create all tables inside Flask app
with app.app_context():
    db.create_all()
    print("Databse tables created successfully!")

#create new ticket
@app.route('/tickets/new', methods=['POST'])
def create_ticket():
    data = request.get_json()
    if not all (k in data for k in ("title", "category", "submitted_by")):
        return jsonify({"error": "Missing required fields"}), 400
    
    ticket = Ticket(
        title=data["title"],
        description=data.get("description", ""),
        category=data["category"],
        priority=data.get("priority", "normal"),
        submitted_by=data["submitted_by"],
        assigned_to=data.get("assigned_to")
    )
    db.session.add(ticket)
    db.session.commit()
    return jsonify({"message": "Ticket created", "ticket_id": ticket.id})

#list all tickets
@app.route('/tickets', methods=['GET'])
def list_tickets():
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
@app.route('/tickets/update/<int:ticket_id>', methods=['POST'])
def update_ticket(ticket_id):
    data = request.get_json()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    
    if "assigned_to" in data:
        ticket.assigned_to = data["assigned_to"]
    if "status" in data:
        ticket.status = data["status"]
        if data["status"].lower() == "resolved":
            ticket.resolved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Ticket updated", "ticket_id": ticket.id})

@app.route('/users/new', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data: #basic validation
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["name", "email", "role"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400
        
    existing_user = Users.query.filter_by(email=data["email"]).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 409

    # if not all (k in data for k in ("name", "email", "role")):
    #     return jsonify({"error": "missing required fields"}), 400
    
    user = Users(
        name=data["name"],
        email=data["email"],
        role=data["role"],
        department=data.get("departement"),
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User created",
        "user_id": user.id
    }), 201

@app.route('/users', methods=['GET'])
#Before building ticket logic, I implimented user creation with validation and uniqueness checks so ticket foreign keys were reliable
def list_users():
    users = Users.query.all()
    return jsonify([
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "active": u.active
        } for u in users 
    ])



if __name__ == "__main__":
    app.run(debug=True) #starts Flask 

