from flask import Blueprint, request, jsonify
from models import Users, db, Inventory


inventory_bp = Blueprint("inventory", __name__)

@inventory_bp.route('/inventory/new', methods=['POST'])
def create_inventory():
    data = request.get_json()

    #basic validation
    required_fields = ["device_type", "serial_number", "status"]
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    #to prevent dupe serial #
    existing = Inventory.query.filter_by(serial_number=data["serial_number"]).first()
    if existing:
        return jsonify({"error": "Devic with this serial already exists"}), 409

    inventory = Inventory(
        device_type=data["device_type"],
        serial_number=data["serial_number"],
        status=data["status"],
        location=data.get("location"),
        assigned_to=data.get("assigned_to")
    )

    db.session.add(inventory)
    db.session.commit()

    return jsonify({"message": "Device created", "device_id": inventory.id}), 201

@inventory_bp.route ('/inventory', methods=['GET'])
def list_inventory():
    devices = Inventory.query.order_by(Inventory.id.desc()).all()
    result = []
    for d in devices:
        result.append({
            "id": d.id,
            "device_type": d.device_type,
            "serial_number": d.serial_number,
            "status": d.status,
            "location": d.location,
            "assigned_to": d.assigned_user.name if d.assigned_user else None
        })
    return jsonify(result)

@inventory_bp.route("/inventory", methods=["GET"])
def get_inventory():
    items = Inventory.query.all()
    return jsonify([{
        "id": i.id,
        "device_type": i.device_type,
        "serial_number": i.serial_number,
        "status": i.status,
        "location": i.location,
        "assigned_to": i.assigned_to
    } for i in items])

@inventory_bp.route('/inventory/update/<int:device_id>', methods=['POST'])
def update_inventory(device_id):
    data = request.get_json()
    device = Inventory.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    #allow updating,status,location,assigned_to
    if "status" in data:
        device.status = data["status"]
    if "location" in data:
        device.location = data["location"]
    if "assigned_to" in data:
        #check user exists and active
        user = Users.query.get(data["assigned_to"])
        if not user or not user.active:
            return jsonify({"error": "Cannot assign to invalid or inactive user"}), 400
        device.assigned_to = data["assigned_to"]
    db.session.commit()
    return jsonify({"message": "Device updated", "device_id": device.id})

@inventory_bp.route('/inventory/delete/<int:device_id>', methods=['DELETE'])
def delete_inventory(device_id):
    device = Inventory.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": "Device deleted"})

