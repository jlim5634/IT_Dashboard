from flask import Flask
from models import db #import SQLAlchemy instance and models
from routes.tickets import tickets_bp
from routes.users import users_bp
from routes.inventory import inventory_bp
from routes.system import system_bp
from routes.metrics import metrics_bp

app = Flask(__name__) #starts flask app

#to config database. use SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///IT_Dashboard.db' #tells SQLAlchemy where to store the database. local file it_ops.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) #connects db instance from models.py to Flask app

#create all tables inside Flask app
with app.app_context():
    db.create_all()
    print("Databse tables created successfully!")

app.register_blueprint(tickets_bp)
app.register_blueprint(users_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(system_bp)
app.register_blueprint(metrics_bp)


if __name__ == "__main__":
    app.run(debug=True) #starts Flask 

