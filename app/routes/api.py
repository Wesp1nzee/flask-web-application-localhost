from flask import Blueprint, request, jsonify, session
from ..models.user import Users, Task, UserTaskStatus
from ..extensions import db
from datetime import datetime

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/api/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    task_id = data.get('id')
    user_answer = data.get('answer')
    if not user_answer:
        return jsonify(error="Пустое поле ввода"), 404

    user_answer = float(user_answer)
    task = Task.query.get(task_id)
    
    if task is None:
        return jsonify(error="Task not found"), 404

    user_id = session.get('user_id')

    is_correct = user_answer == task.answer

    if user_id:
        user_task_status = UserTaskStatus.query.filter_by(user_id=user_id, task_id=task_id).first()
        if not user_task_status:
            user_task_status = UserTaskStatus(user_id=user_id, task_id=task_id, is_correct=is_correct)
            db.session.add(user_task_status)
        else:
            user_task_status.is_correct = is_correct
            user_task_status.attempted_at = datetime.utcnow()

        db.session.commit()


    return jsonify(correct=is_correct, task_id=task_id, user_id=user_id)

@api.route('/api/check_login', methods=['POST'])
def check_login():
    login = request.json.get('login')
    user = Users.query.filter_by(login=login).first()
    exists = user is not None
    return jsonify({'exists': exists})
