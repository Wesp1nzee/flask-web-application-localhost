import re
from ..extensions import db, mail
from ..models.user import Users, UserAuthTelegram
from yandex_cloud_ml_sdk import YCloudML
from ..config import Config
import hashlib
import hmac
import time
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import render_template, url_for

BOT_TOKEN = Config().BOT_TOKEN

def get_yandex_gpt_messages(message_history):
    """
    Функция для отправки сообщений в GPT с поддержкой контекста
    message_history: список сообщений в формате [{"role": "user/assistant/system", "text": "сообщение"}]
    """
    try:
        messages = [
            {
                "role": "system",
                "text": "Ты умный ассистент, который помогает пользователям с их вопросами."
            }
        ]
        
        messages.extend(message_history)
        
        sdk = YCloudML(
            folder_id=Config().FOLDER_ID,
            auth=Config().API_KEY_GPT,
        )

        result = sdk.models.completions("yandexgpt").configure(temperature=0.5).run(messages)
        
        response_text = result.alternatives[0].text if result.alternatives else "No response from model."
        total_tokens = result.usage.total_tokens
        
        return response_text, total_tokens
    except Exception as e:
        print(f"Error in get_yandex_gpt_messages: {e}")
        return "Произошла ошибка при обработке запроса.", 0

def fix_markdown_tables(text):
    """
    Исправляет таблицы в тексте, чтобы они корректно рендерились в HTML.
    """
    table_pattern = re.compile(r"(\|.*?\|\n\|[-:\s|]+\|\n(?:\|.*?\|\n)+)")
    matches = table_pattern.findall(text)

    for match in matches:
        fixed_table = "\n".join(line.strip() for line in match.splitlines())
        fixed_table = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', fixed_table)  # Жирный текст
        fixed_table = re.sub(r'\*(.*?)\*', r'<em>\1</em>', fixed_table)  # Курсив
        text = text.replace(match, fixed_table)

    return text


def check_telegram_authorization(auth_data):
    check_hash = auth_data.pop("hash", None)
    data_check_arr = [f"{key}={value}" for key, value in sorted(auth_data.items())]
    data_check_string = "\n".join(data_check_arr)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hash_calc = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if hash_calc != check_hash:
        raise ValueError("Данные не от Telegram")
    if time.time() - int(auth_data["auth_date"]) > 86400:
        raise ValueError("Данные устарели")


def get_or_create_user(auth_data):
    telegram_id = auth_data["id"]
    user_auth = UserAuthTelegram.query.filter_by(external_id=telegram_id).first()
    if user_auth:
        return user_auth.user
    else:
        user = Users()
        db.session.add(user)
        db.session.commit()
        user_auth = UserAuthTelegram(
            user_id=user.id,
            external_id=telegram_id,
            first_name=auth_data.get("first_name"),
            last_name=auth_data.get("last_name"),
            username=auth_data.get("username"),
            photo_url=auth_data.get("photo_url")
        )
        db.session.add(user_auth)
        db.session.commit()
        return user

def send_confirmation_email(user_email):
    serializer = URLSafeTimedSerializer(Config().SECRET_KEY)
    token = serializer.dumps(user_email, salt='email-confirm-salt')
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('email_confirmation.html', confirm_url=confirm_url)
    
    msg = Message(
        subject='Подтверждение Email',
        sender=Config().MAIL_DEFAULT_SENDER,
        recipients=[user_email],
        body='Пожалуйста, подтвердите ваш email, перейдя по следующей ссылке: {}'.format(confirm_url),
        html=html
    )
    mail.send(msg)
