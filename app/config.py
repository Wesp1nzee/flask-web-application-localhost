import os

class Config:
    POSTGRES_USER=os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD=os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_HOST=os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT=os.environ.get('POSTGRES_PORT')
    POSTGRES_DB=os.environ.get('POSTGRES_DB')

    API_KEY_GPT=os.environ.get('API_KEY_GPT')
    FOLDER_ID=os.environ.get('FOLDER_ID')
    PROMT=os.environ.get('PROMT')

    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    SECRET_KEY=os.urandom(24)

    BOT_TOKEN=os.environ.get('BOT_TOKEN')

    MAIL_SERVER = 'smtp.mail.ru'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    UPLOAD_FOLDER = 'app/static/uploads'

    UPLOAD_FOLDER_ADMIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')

    SERVER_NAME='localhost'

    TESTING = True
    DEBUG = False
    DEVELOPMENT = False
    DEBUG_TB_ENABLED = False

    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_ENABLED = False