from ..extensions import db
from datetime import datetime
from .task import Subject, TaskType, Task 
from .summary import SummaryTopic, Summary, SummaryTask
from .post import News, Comment, Reaction

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    auth_methods = db.relationship("UserAuthTelegram", back_populates="user")
    email_auth = db.relationship("EmailAuth", back_populates="user", uselist=False)
    dialogues = db.relationship("Dialogue", back_populates="user")
    test_progress = db.relationship('UserTestProgress', back_populates='user', lazy=True)
    comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reactions = db.relationship("Reaction", back_populates="user", cascade="all, delete-orphan")

class UserAuthTelegram(db.Model):
    __tablename__ = 'user_auth_telegram'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    external_id = db.Column(db.String(100), nullable=False)  
    first_name = db.Column(db.String(100), nullable=True)  
    last_name = db.Column(db.String(100), nullable=True)  
    username = db.Column(db.String(50), nullable=True)  
    photo_url = db.Column(db.String(300), nullable=True)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  

    user = db.relationship("Users", back_populates="auth_methods")

class EmailAuth(db.Model):
    __tablename__ = 'email_auth'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    login = db.Column(db.String(50), nullable=False, unique=True)  
    password_hash = db.Column(db.String(256), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  
    confirmed = db.Column(db.Boolean, default=False)  
    confirmed_on = db.Column(db.DateTime, nullable=True) 

    user = db.relationship("Users", back_populates="email_auth")

class UserTaskStatus(db.Model):
    __tablename__ = 'user_task_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String, db.ForeignKey('tasks.id'), nullable=False)  
    is_correct = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users', backref=db.backref('task_statuses', lazy=True))
    task = db.relationship('Task', backref=db.backref('user_statuses', lazy=True))

class UserTestProgress(db.Model):
    __tablename__ = 'user_test_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    summary_id = db.Column(db.Integer, db.ForeignKey('summaries.id'), nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users', back_populates='test_progress')
    summary = db.relationship('Summary', back_populates='user_progress')

class Dialogue(db.Model):
    __tablename__ = 'dialogues' 

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    total_tokens = db.Column(db.Integer, nullable=False)
    is_title_changed = db.Column(db.Boolean, default=False)

    user = db.relationship("Users", back_populates="dialogues") 
    messages = db.relationship("Message", back_populates="dialogue")  

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    dialogue_id = db.Column(db.Integer, db.ForeignKey('dialogues.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.Integer, nullable=False)

    dialogue = db.relationship("Dialogue", back_populates="messages")
