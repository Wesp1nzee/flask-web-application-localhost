from flask import render_template, Blueprint, request, session, redirect, url_for, flash, current_app, jsonify
from ...models.user import Task, Subject, TaskType
from ...extensions import db
import os
from ...utils.utils import allowed_file
from functools import wraps
from PIL import Image
import uuid

admin_tasks = Blueprint('admin_tasks', __name__, template_folder='templates')
admin_tasks.static_folder = 'static'

ALLOWED_EXTENSIONS = {'png'}
UPLOAD_FOLDER = 'app/static/matched_photos'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_tasks.route('/admin/tasks')
@admin_required
def admin_panel():
    return render_template('admin/admin_add_task.html')

@admin_tasks.route('/admin/api/subjects', methods=['GET'])
@admin_required
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([{
        'id': subject.id,
        'name': subject.name
    } for subject in subjects])

@admin_tasks.route('/admin/api/subjects', methods=['POST'])
@admin_required
def create_subject():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Название предмета обязательно'}), 400
    
    try:
        subject = Subject(name=data['name'])
        db.session.add(subject)
        db.session.commit()
        return jsonify({
            'message': 'Предмет успешно создан',
            'id': subject.id,
            'name': subject.name
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_tasks.route('/admin/api/subjects/<int:subject_id>/task-types', methods=['GET'])
@admin_required
def get_subject_task_types(subject_id):
    task_types = TaskType.query.filter_by(subject_id=subject_id).all()
    return jsonify([{
        'id': task_type.id,
        'name': task_type.name
    } for task_type in task_types])

@admin_tasks.route('/admin/api/task-types', methods=['POST'])
@admin_required
def create_task_type():
    data = request.get_json()
    if not data.get('name') or not data.get('subject_id'):
        return jsonify({'error': 'Название и ID предмета обязательны'}), 400
    
    try:
        task_type = TaskType(
            subject_id=data['subject_id'],
            name=data['name']
        )
        db.session.add(task_type)
        db.session.commit()
        return jsonify({
            'message': 'Тип задачи успешно создан',
            'id': task_type.id,
            'name': task_type.name
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_tasks.route('/admin/api/tasks/<string:task_id>', methods=['GET'])
@admin_required
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify({
        'id': task.id,
        'task_type': {
            'id': task.task_type.id,
            'name': task.task_type.name,
            'subject': {
                'id': task.task_type.subject.id,
                'name': task.task_type.subject.name
            }
        },
        'answer': task.answer
    })

@admin_tasks.route('/admin/api/tasks', methods=['POST'])
@admin_required
def create_task():
    if 'image' not in request.files:
        return jsonify({'error': 'Изображение обязательно'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
        
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Разрешены только PNG файлы'}), 400
    
    try:
        task_id = str(uuid.uuid4())[:6].upper()
        filename = f"{task_id}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        image = Image.open(file)
        image.save(filepath, 'PNG')
        
        task = Task(
            id=task_id,
            task_type_id=request.form['task_type_id'],
            answer=float(request.form['answer'])
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Задача успешно создана',
            'id': task_id,
            'task_type': {
                'id': task.task_type.id,
                'name': task.task_type.name
            },
            'answer': task.answer
        }), 201
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_tasks.route('/admin/api/tasks/<string:task_id>', methods=['PUT'])
@admin_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    try:
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '' and allowed_file(file.filename):
                filepath = os.path.join(UPLOAD_FOLDER, f"{task_id}.png")
                image = Image.open(file)
                image.save(filepath, 'PNG')
        
        if 'task_type_id' in request.form:
            task.task_type_id = request.form['task_type_id']
        if 'answer' in request.form:
            task.answer = float(request.form['answer'])
        
        db.session.commit()
        return jsonify({'message': 'Задача успешно обновлена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_tasks.route('/admin/api/tasks/<string:task_id>', methods=['DELETE'])
@admin_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    try:

        filepath = os.path.join(UPLOAD_FOLDER, f"{task_id}.png")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Задача успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_tasks.route('/admin/api/subjects/with-task-types', methods=['POST'])
@admin_required
def create_subject_with_task_types():
    data = request.get_json()
    
    if not data.get('subject_name') or not data.get('task_types'):
        return jsonify({'error': 'Название предмета и типы задач обязательны'}), 400
    
    try:
        subject = Subject(name=data['subject_name'])
        db.session.add(subject)
        db.session.flush()  
        
        task_types = []
        for task_type_name in data['task_types']:
            task_type = TaskType(
                subject_id=subject.id,
                name=task_type_name
            )
            db.session.add(task_type)
            task_types.append(task_type)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Предмет и типы задач успешно созданы',
            'subject': {
                'id': subject.id,
                'name': subject.name
            },
            'task_types': [{
                'id': tt.id,
                'name': tt.name
            } for tt in task_types]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400