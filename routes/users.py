from flask import Blueprint, request, jsonify
from models import Users, Ticket, Inventory, db

users_bp = Blueprint("users", __name__)

@users_bp.route('/users/new', methods=['POST'])
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

    if not all (k in data for k in ("name", "email", "role")):
        return jsonify({"error": "missing required fields"}), 400
    
    user = Users(
        name=data["name"],
        email=data["email"],
        role=data["role"],
        department=data.get("departement"),
        onboarding_tasks = [ #add onboarding tasks with user creation. when user is created, their record is added to users table and inventory can optionally be assigned
            {"task": "Image laptop", "completed": False},
            {"task": "Install software", "completed":False},
            {"task": "Grant access", "completed": False}
        ]
    )

    onboarding_tasks = [ #add onboarding tasks with user creation. when user is created, their record is added to users table and inventory can optionally be assigned
        {"task": "Image laptop", "completed": False},
        {"task": "Install software", "completed":False},
        {"task": "Grant access", "completed": False}
    ]

    

    user.onboarding_tasks = onboarding_tasks

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User created",
        "user_id": user.id,
        "onboarding_tasks": onboarding_tasks
    }), 201

@users_bp.route("/users", methods=["GET"])
def get_users():
    users= Users.query.all()
    return jsonify([{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "department": u.department, "active": u.active} for u in users])


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    u = Users.query.get_or_404(user_id)
    data = request.json
    u.name = data.get("name", u.name)
    u.email = data.get("email", u.email)
    u.role = data.get("role", u.role)
    u.department = data.get("department", u.department)
    u.active = data.get("active", u.active)
    db.session.commit()
    return jsonify({"message": "User updated"})

@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    u = Users.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({"message": "User deleted"})

@users_bp.route('/users', methods=['GET'])
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

@users_bp.route('/users/onboarding_status', methods=['GET'])
def onboarding_status():
    users = Users.query.all()
    result = []

    for user in users:
        tasks = user.onboarding_tasks or []
        completed_count = sum(1 for t in tasks if t["completed"])
        total_tasks = len(tasks)
        result.append({
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "active": user.active,
            "onboarding_completed": completed_count,
            "onboarding_total": total_tasks,
            "tasks": tasks
        })

    return jsonify(result)

@users_bp.route('/users/deactivate/<int:user_id>', methods=['POST'])
def offboarding(user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    #deactivate user
    user.active = False

    #unassign their tickets assigned to them
    tickets = Ticket.query.filter_by(assigned_to=user_id).all()
    for ticket in tickets:
        ticket.assigned_to = None
        if ticket.status != "Resolved":
            ticket.status = "Open"
    
    #unassign inventory
    devices = Inventory.query.filter_by(assigned_to=user.id).all()
    for device in devices:
        device.assigned_to = None
    
    db.session.commit()

    return jsonify({
        "message": f"User {user.name} deactivated. Tickets and inventory unassigned"
    })

@users_bp.route('/tasks/complete', methods=['POST'])
def mark_tasks_complete():
    data = request.get_json()
    user_id = data.get("user_id")
    task_name = data.get("task")

    user = Users.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "user not found"}), 404

    #mark tasks complete
    for task in user.onboarding_tasks: #iterate through the tasks table
        if task["task"] == data["task"]:
            task["completed"] = True
            break
    else:
        return jsonify({"error": "Task not found"}), 404

    db.session.commit()#if onboarding_tasks are stored in DB
    return jsonify({"message": f"Task '{task_name}' marked complete for {user.name}"})

