from flask.app import App
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from ..extensions import db
from ..models.user import UserTaskStatus, UserTestProgress, Task
from datetime import datetime, timedelta
from sqlalchemy import func

ALLOWED_EXTENSIONS = {'png'}

def login_required(f):
    @wraps(f)  
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('user.main'))
        return f(*args, **kwargs)
    return decorated_function

def register_blueprint(app: App):
    from ..routes import admin, api, auth, user, profile, gpt, summary, post, ide, admin_tasks, admin_news
    app.register_blueprint(admin)
    app.register_blueprint(user)
    app.register_blueprint(api)
    app.register_blueprint(gpt)
    app.register_blueprint(profile)
    app.register_blueprint(auth)
    app.register_blueprint(summary)
    app.register_blueprint(post)
    app.register_blueprint(ide)
    app.register_blueprint(admin_tasks)
    app.register_blueprint(admin_news)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_statistics(user_id):
    total_tasks = Task.query.count()
    

    completed_tasks = UserTaskStatus.query.filter(
        UserTaskStatus.user_id == user_id,
        UserTaskStatus.is_correct == True
    ).count()
    
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    total_attempts = UserTaskStatus.query.filter(
        UserTaskStatus.user_id == user_id
    ).count()
    
    accuracy = (completed_tasks / total_attempts * 100) if total_attempts > 0 else 0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_percentage': completion_percentage,
        'accuracy': accuracy,
        'total_attempts': total_attempts
    }

def get_user_activity(user_id):
    today = datetime.utcnow()
    start_date = today - timedelta(days=365)
    
    task_activity = (
        db.session.query(
            func.date(UserTaskStatus.attempted_at).label('date'),
            func.count(UserTaskStatus.id).label('count')
        )
        .filter(
            UserTaskStatus.user_id == user_id,
            UserTaskStatus.attempted_at >= start_date
        )
        .group_by(func.date(UserTaskStatus.attempted_at))
        .all()
    )

    test_activity = (
        db.session.query(
            func.date(UserTestProgress.completed_at).label('date'),
            func.count(UserTestProgress.id).label('count')
        )
        .filter(
            UserTestProgress.user_id == user_id,
            UserTestProgress.completed_at >= start_date
        )
        .group_by(func.date(UserTestProgress.completed_at))
        .all()
    )

    activity_data = {}
    for record in task_activity + test_activity:
        date_str = record.date.strftime('%Y-%m-%d')
        activity_data[date_str] = activity_data.get(date_str, 0) + record.count
    
    return [{'date': k, 'value': v} for k, v in activity_data.items()]