from ..extensions import db
from datetime import datetime

class MainTopic(db.Model):
    __tablename__ = 'main_topics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subject_name = db.Column(db.String(100), nullable=False)  # Название учебного предмета (например, "Физика")
    main_topic_name = db.Column(db.String(100), nullable=False)  # Основная тема (например, "Квантовая механика")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    summary_topics = db.relationship('SummaryTopic', back_populates='main_topic', lazy=True)

class SummaryTopic(db.Model):
    __tablename__ = 'summary_topics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic_name = db.Column(db.String(100), nullable=False)
    main_topic_id = db.Column(db.Integer, db.ForeignKey('main_topics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    main_topic = db.relationship('MainTopic', back_populates='summary_topics')
    summaries = db.relationship('Summary', back_populates='summary_topic', lazy=True)

class Summary(db.Model):
    __tablename__ = 'summaries'

    id = db.Column(db.Integer, primary_key=True)
    summary_topic_id = db.Column(db.Integer, db.ForeignKey('summary_topics.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    summary_topic = db.relationship('SummaryTopic', back_populates='summaries')
    tasks = db.relationship('SummaryTask', backref='summary', lazy=True)
    user_progress = db.relationship('UserTestProgress', back_populates='summary', lazy=True)

class SummaryTask(db.Model):
    __tablename__ = 'summary_tasks'

    id = db.Column(db.Integer, primary_key=True)
    summary_id = db.Column(db.Integer, db.ForeignKey('summaries.id'), nullable=False)
    question = db.Column(db.String, nullable=False)
    option_a = db.Column(db.String, nullable=False)
    option_b = db.Column(db.String, nullable=False)
    option_c = db.Column(db.String, nullable=False)
    option_d = db.Column(db.String, nullable=False)
    correct_option = db.Column(db.String, nullable=False)