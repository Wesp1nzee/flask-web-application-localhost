from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, render_template
from ...models.user import News
from ...extensions import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from functools import wraps
from PIL import Image
import uuid
from ...utils.utils import allowed_file

admin_news = Blueprint('admin_news', __name__, template_folder='templates')
admin_news.static_folder = 'static'
#TODO вынести в utils
ALLOWED_EXTENSIONS = {'png'}
UPLOAD_FOLDER = 'app/static/news_images'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def save_image(file):
    """Сохраняет изображение и возвращает путь"""
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{str(uuid.uuid4())}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        image = Image.open(file)
        image.save(filepath)
        
        return f"/static/news_images/{filename}"
    return None

@admin_news.route('/admin/news')
@admin_required
def news_panel():
    return render_template('admin/news_management.html')

@admin_news.route('/admin/api/news', methods=['POST'])
@admin_required
def create_news():
    """Создание новой новости"""
    try:
        if 'title' not in request.form:
            return jsonify({'error': 'Заголовок обязателен'}), 400
        
        if 'content' not in request.form:
            return jsonify({'error': 'Контент обязателен'}), 400
        
        filename = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{str(uuid.uuid4())[:8]}.{extension}"
                
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                image = Image.open(file)
                image.save(filepath)
        
        news = News(
            title=request.form['title'],
            content=request.form['content'],
            tags=request.form.get('tags', ''),
            photo=filename,  
            created_at=datetime.utcnow()
        )
        
        db.session.add(news)
        db.session.commit()
        
        return jsonify({
            'message': 'Новость успешно создана',
            'id': news.id,
            'filename': filename
        }), 201
        
    except Exception as e:
        if filename:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, filename))
            except:
                pass
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_news.route('/admin/api/news/by-title/<string:title>', methods=['GET'])
@admin_required
def get_news_by_title(title):
    """Поиск новости по заголовку"""
    try:
        news = News.query.filter(News.title.ilike(f"%{title}%")).first()
        if not news:
            return jsonify({'error': 'Новость не найдена'}), 404
            
        return jsonify({
            'id': news.id,
            'title': news.title,
            'content': news.content,
            'tags': news.tags,
            'photo': news.photo,
            'created_at': news.created_at.isoformat(),
            'views_count': news.views_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_news.route('/admin/api/news/<int:news_id>', methods=['PUT'])
@admin_required
def update_news(news_id):
    """Обновление новости"""
    try:
        news = News.query.get_or_404(news_id)
        
        if 'title' in request.form:
            news.title = request.form['title']
        if 'content' in request.form:
            news.content = request.form['content']
        if 'tags' in request.form:
            news.tags = request.form['tags']
            

        if 'photo' in request.files and request.files['photo'].filename:
            if news.photo:
                old_image_path = os.path.join(current_app.root_path, news.photo.lstrip('/'))
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            news.photo = save_image(request.files['photo'])
        
        db.session.commit()
        return jsonify({'message': 'Новость успешно обновлена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_news.route('/admin/api/news/<int:news_id>', methods=['DELETE'])
@admin_required
def delete_news(news_id):
    """Удаление новости"""
    try:
        news = News.query.get_or_404(news_id)
        
        if news.photo:
            image_path = os.path.join(current_app.root_path, news.photo.lstrip('/'))
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(news)
        db.session.commit()
        
        return jsonify({'message': 'Новость успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
