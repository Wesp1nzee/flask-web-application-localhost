from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_mail import Mail
from flask_socketio import SocketIO

migrate = Migrate()
db = SQLAlchemy()
mail = Mail()
socketio = SocketIO()