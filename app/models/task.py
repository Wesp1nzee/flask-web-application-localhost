from ..extensions import db


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    task_types = db.relationship('TaskType', backref='subject', lazy=True)


class TaskType(db.Model):
    __tablename__ = 'task_types'

    id = db.Column(db.String, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    tasks = db.relationship('Task', backref='task_type', lazy=True)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.String, primary_key=True)
    task_type_id = db.Column(db.String, db.ForeignKey('task_types.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Float, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    answer_string = db.Column(db.String(50), nullable=True)
    patch_file = db.Column(db.String(100), nullable=True)