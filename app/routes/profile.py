from flask import Blueprint, render_template, jsonify, request, session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from ..extensions import db
from ..models.user import Users, UserTaskStatus, Task, Subject, EmailAuth, TaskType
import json
from werkzeug.security import check_password_hash, generate_password_hash
from ..utils.utils import login_required, get_user_statistics, get_user_activity

profile = Blueprint('profile', __name__, template_folder='templates')
profile.static_folder = 'static'

@profile.route('/profile')
@login_required
def profile_view():
    user_id = session['user_id']
    user = Users.query.get_or_404(user_id)
    
    stats = get_user_statistics(user_id)
    
    subjects = Subject.query.all()
    
    activity_data = get_user_activity(user_id)

    return render_template(
        'profile.html',
        user=user,
        stats=stats,
        subjects=subjects,
        activity_data=json.dumps(activity_data)
    )

@profile.route('/api/user/statistics')
@login_required
def get_detailed_statistics():
    user_id = session['user_id']
    subject_id = request.args.get('subject', '')
    period = request.args.get('period', 'day')
    
    today = datetime.utcnow()
    if period == 'day':
        start_date = today - timedelta(days=1)
    elif period == 'week':
        start_date = today - timedelta(weeks=1)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    else:
        return jsonify({'error': 'Invalid period'}), 400
    
    query = db.session.query(
        func.date(UserTaskStatus.attempted_at).label('date'),
        func.count(UserTaskStatus.id).label('total'),
        func.sum(case((UserTaskStatus.is_correct == True, 1), else_=0)).label('correct')
    ).filter(
        UserTaskStatus.user_id == user_id,
        UserTaskStatus.attempted_at >= start_date
    )

    if subject_id:
        query = query.join(Task, UserTaskStatus.task_id == Task.id)\
                     .join(TaskType, Task.task_type_id == TaskType.id)\
                     .filter(TaskType.subject_id == subject_id)
    
    stats = query.group_by(func.date(UserTaskStatus.attempted_at)).all()
    
    dates = []
    solved_tasks = []
    accuracy = []
    
    for stat in stats:
        dates.append(stat.date.strftime('%Y-%m-%d'))
        solved_tasks.append(stat.total)
        accuracy.append((stat.correct / stat.total * 100) if stat.total > 0 else 0)
    
    result = {
        'dates': dates,
        'solvedTasks': solved_tasks,
        'accuracy': accuracy
    }
    
    return jsonify(result)

@profile.route('/api/user/update-info', methods=['POST'])
@login_required
def update_user_info():
    user_id = session['user_id']
    user = Users.query.get_or_404(user_id)
    
    try:
        if 'email' in request.form and request.form['email']:
            existing_email = EmailAuth.query.filter_by(email=request.form['email']).first()
            if existing_email and existing_email.user_id != user_id:
                return jsonify({'error': 'Email уже используется'}), 400
            
            if user.email_auth:
                user.email_auth.email = request.form['email']
            else:
                email_auth = EmailAuth(
                    user_id=user_id,
                    email=request.form['email'],
                    login=request.form['email'].split('@')[0],
                    password_hash='temporary' 
                )
                db.session.add(email_auth)
        
        db.session.commit()
        return jsonify({'message': 'Информация успешно обновлена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@profile.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    user = Users.query.get_or_404(user_id)
    
    if not user.email_auth:
        return jsonify({'error': 'Невозможно изменить пароль для данного метода авторизации'}), 400
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    user_password = Users.query.join(EmailAuth).filter(EmailAuth.user_id == user_id).first()
    if not check_password_hash(user_password.email_auth.password_hash, current_password):
        return jsonify({'error': 'Неверный текущий пароль'}), 400
    
    try:
        user.email_auth.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Пароль успешно изменен'})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 400