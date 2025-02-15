from .extensions import db, migrate, mail, socketio
from flask import Flask
from flask_cors import CORS
from .utils.utils import register_blueprint
from .config import Config
from flask_ckeditor import CKEditor


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config['CKEDITOR_SERVE_LOCAL'] = True
    app.config['CKEDITOR_HEIGHT'] = 400
    CKEditor(app)
    
    CORS(app, resources={
        r"/socket.io/*": {
            "origins": "*",
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"]
        }
    })

    register_blueprint(app)
    app.config.from_object(config_class)
    app.config['UPLOADED_PHOTOS_DEST'] = 'static/uploads'

    import os
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER_ADMIN'], exist_ok=True)

    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    with app.app_context():
        db.create_all()

    return app