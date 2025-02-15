from flask import render_template, Blueprint, request, session, redirect, url_for, flash, current_app
from ...models.user import Users, Task, UserTaskStatus, SummaryTopic, Summary, SummaryTask, News
from datetime import datetime
from ...extensions import db
import psutil 
import os
from ...from_admin import NewsForm, SummaryForm
from ...utils.utils import allowed_file
from werkzeug.utils import secure_filename
import logging
from functools import wraps

logging.basicConfig(level=logging.DEBUG)

admin = Blueprint('admin', __name__, template_folder='templates')
admin.static_folder = 'static'

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_logged_in' in session:
        total_users = Users.query.count() 
        total_tasks = Task.query.count()  
        total_resolved_tasks = UserTaskStatus.query.filter(UserTaskStatus.is_correct == True).count()  # Решенные задачи
        total_tasks_today = UserTaskStatus.query.filter(
            db.func.date(UserTaskStatus.attempted_at) == datetime.utcnow().date(),
            UserTaskStatus.is_correct == True
        ).count()  

        cpu_usage = psutil.cpu_percent(interval=1) 
        memory = psutil.virtual_memory() 
        memory_usage = memory.percent 
        disk_usage = psutil.disk_usage('/').percent

        return render_template(
            'admin/admin_dashboard.html',
            total_users=total_users,
            total_tasks=total_tasks,
            total_resolved_tasks=total_resolved_tasks,
            total_tasks_today=total_tasks_today,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage
        )
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_dashboard'))
        else:
            error_message = "Неверный логин или пароль!"
            return render_template('admin/admin_login.html', error_message=error_message)
    
    
    return render_template('admin/admin_login.html')


@admin.route('/admin/add-news', methods=['GET', 'POST'])
def news_admin():
    form = NewsForm()
    if form.validate_on_submit():
        try:
            title = form.title.data
            content = form.content.data
            tags = form.tags.data

            # Обработка загрузки фотографии
            photo_filename = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(photo_path)
                    photo_filename = filename
                else:
                    logging.error("Файл не соответствует допустимым форматам")

            new_news = News(title=title, content=content, tags=tags, photo=photo_filename)
            db.session.add(new_news)
            db.session.commit()
            logging.info("Новость успешно добавлена в базу данных")
            return redirect(url_for('admin.news_admin'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Ошибка при добавлении новости: {e}")
            flash('Ошибка при добавлении новости. Попробуйте еще раз.')

    for field, errors in form.errors.items():
        for error in errors:
            logging.error(f"Ошибка в поле {field}: {error}")

    return render_template('admin/admin_add_news.html', form=form)

@admin.route('/admin/add-summary', methods=['GET', 'POST'])
def add_summary():
    form = SummaryForm()
    if form.validate_on_submit():

        new_topic = SummaryTopic(subject_name=form.subject_name.data, topic_name=form.topic_name.data)
        db.session.add(new_topic)
        db.session.commit()

        new_summary = Summary(summary_topic_id=new_topic.id, content=form.content.data)
        db.session.add(new_summary)
        db.session.commit()

        for task_form in form.tasks.entries:
            new_task = SummaryTask(
                summary_id=new_summary.id,
                question=task_form.task_question.data,
                option_a=task_form.option1.data,
                option_b=task_form.option2.data,
                option_c=task_form.option3.data,
                option_d=task_form.option4.data,
                correct_option=task_form.correct_option.data
            )
            db.session.add(new_task)
        
        db.session.commit()

        flash('Конспект и задачи успешно добавлены!', 'success')
        return redirect(url_for('admin.add_summary'))

    csrf_token = form.csrf_token.current_token  # Получение текущего CSRF токена
    return render_template('admin/add_summary.html', form=form, csrf_token=csrf_token)

@admin.route('/logout-admin')
def logout_admin():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_dashboard'))
