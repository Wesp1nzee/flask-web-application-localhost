from ..extensions import db
from datetime import datetime


class News(db.Model):
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.String(255))  # Теги для новости (Теги разделены запятыми)
    views_count = db.Column(db.Integer, default=0)
    photo = db.Column(db.String(255))  # Поле для хранения пути к фотографии

    comments = db.relationship("Comment", back_populates="news", cascade="all, delete-orphan")
    reactions = db.relationship("Reaction", back_populates="news", cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)

    # Связи
    user = db.relationship("Users", back_populates="comments")
    news = db.relationship("News", back_populates="comments")


class Reaction(db.Model):
    __tablename__ = 'reactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Enum('like', 'dislike', name='reaction_types'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)

    user = db.relationship("Users", back_populates="reactions")
    news = db.relationship("News", back_populates="reactions")