from ..models.user import Task, UserTaskStatus, TaskType
from math import ceil
from flask import Blueprint, render_template, redirect, url_for, request, session, send_from_directory
from ..lexicon.task_list import TASK_LIST_MATH


user = Blueprint('user', __name__, template_folder='templates')
user.static_folder = 'static'

@user.route('/')
def main():
    return render_template('main.html')
    
@user.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('user.main'))

@user.route('/task_list/<int:subject_id>')
def task_list(subject_id):
    tasks_count = Task.query.join(TaskType).filter(TaskType.subject_id == subject_id).count()
    return render_template('task_list.html', task_list=TASK_LIST_MATH, task_count=str(tasks_count))

@user.route('/photo_task/<int:subject_id>/<int:task_type_id>')
def photo_task(subject_id, task_type_id):
    user_id = session.get('user_id')

    tasks = Task.query.filter_by(task_type_id=task_type_id).all()
    page = request.args.get('page', 1, type=int)
    per_page = 10 
    total_tasks = len(tasks)
    total_pages = ceil(total_tasks / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    tasks_to_display = tasks[start:end]

    task_statuses = UserTaskStatus.query.filter(
        UserTaskStatus.user_id == user_id,
        UserTaskStatus.task_id.in_([task.id for task in tasks_to_display])
    ).all()

    task_status_map = {status.task_id: status.is_correct for status in task_statuses}

    for task in tasks_to_display:
        if not task.answer:
            task.answer = "Ответа нет"
    
    return render_template(
        'photo_task.html', 
        task_list=tasks_to_display, 
        current_page=page, 
        total_pages=total_pages, 
        subject_id=subject_id,
        task_type_id=task_type_id,
        task_status_map=task_status_map 
    )

@user.route('/favicon.ico')
def favicon():
    return send_from_directory('static/images', 'favicon.ico', mimetype='image/vnd.microsoft.icon')
