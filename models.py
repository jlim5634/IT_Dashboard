from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON #import JSON type for SQLite

db = SQLAlchemy() #connection between python objects and database

class Users(db.Model): #not just plain classes but database models
    __tablename__ = "users" #sets tablename in database
    
    #db.Column meaning this attribute should become a column in the db. Db like remote control and databsae is the TV
    #db.Model -> database table
    #db.Column -> column
    #db.Session -> transaction manager

    #column has a type and rules/constraints
    #primary_key -> must have unique ID amd tje db auto-generates it. Used to reference rows
    #nullable -> field cannot be empty. db rejects if empty or none
    #unique=True -> two users cannot have same email
   

    id = db.Column(db.Integer, primary_key=True) #create column called id, stores int, treat it as unique indentifier
    name = db.Column(db.String(100), nullable=False)  #db.String(#) -> store string up to # characters long
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False) #employee, it_support, admin
    department = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)  #default=True -> if no val provided, use True. New users active by default and offboarding flips it to False

    onboarding_tasks = db.Column(JSON, default=[])
    
    submitted_tickets = db.relationship( #db.relationship -> allows navigation between tables using python objects not SQL
        "Ticket", foreign_keys="Ticket.submitted_by", back_populates="submitter", cascade="all, delete-orphan" #backref -> creates reverse link automatically
                    #ticker has to user references so submitted_by and assigned_to. This helps SQLAlchemy know which one this relationship refers to
    )

    assigned_tickets = db.relationship(
        "Ticket", foreign_keys="Ticket.assigned_to", back_populates="assigned_user"
    )

    def __repr__(self):
        return f"<User {self.name}>"

class Ticket(db.Model): #relationships defines ticker -> users and inventory -> users
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    priority = db.Column(db.String(50), default="normal")
    status = db.Column(db.String(50), default="Open")

    submitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) #ForeignKey -> store the ID of a row in the users table
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) #True so that every ticket doesn't initially always have assigned user

    submitter = db.relationship(
        "Users",
        foreign_keys=[submitted_by],
        back_populates="submitted_tickets"
    )

    assigned_user = db.relationship(
        "Users",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets"
    )

    def __repr__(self):
        return f"<Ticket {self.title} submitted_by {self.submitted_by} assigned_to {self.assigned_to}>"

    created_at = db.Column(db.DateTime, default=datetime.utcnow) #auto gets timestamp
    resolved_at = db.Column(db.DateTime, nullable=True)

class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50))
    serial_number = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50))
    location = db.Column(db.String(100))

    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    assigned_user = db.relationship(
        "Users",
        foreign_keys=[assigned_to],
        backref="inventory_items"
    )

    def __repr__(self):
        return f"<Inventory {self.device_type} {self.serial_number} assigned_to {self.assigned_to}>"
    
class SystemState(db.Model):
    __table__name = "sytem_state"
    id = db.Column(db.Integer, primary_key=True)
    gameday = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
        
       
