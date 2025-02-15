from ..extensions import db
from ..models.user import Users, EmailAuth
from ..forms import RegistrationForm, LoginForm
from flask import Blueprint, render_template, flash, redirect, url_for, request, session, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from ..utils.utils_auth import check_telegram_authorization, send_confirmation_email, get_or_create_user
import json
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
from ..config import Config


auth = Blueprint('auth', __name__, template_folder='templates')
auth.static_folder = 'static'

@auth.route("/auth-tg", methods=["GET"])
def auth_telegram():
    try:
        auth_data = request.args.to_dict()
        check_telegram_authorization(auth_data)
        user = get_or_create_user(auth_data)
        session['user_id'] = user.id
        response = make_response(redirect(url_for('user.main')))
        response.set_cookie("tg_user", json.dumps(auth_data))
        return response
    except Exception as e:
        return str(e), 400

@auth.route('/register', methods=['GET', 'POST'])
def register():
    bot_username = "SigmaFipibot"
    form = RegistrationForm()
    if request.method == 'GET':
        return render_template('register.html', form=form, bot_username=bot_username)
        
    
    if form.validate_on_submit():
        if not EmailAuth.query.filter_by(login=form.login.data).first():
            if not EmailAuth.query.filter_by(email=form.email.data).first():
                new_user = Users(
                    date=datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()

                new_email_auth = EmailAuth(
                    user_id=new_user.id,
                    email=form.email.data,
                    login=form.login.data,
                    password_hash=generate_password_hash(form.password.data),
                    created_at=datetime.utcnow()
                )
                db.session.add(new_email_auth)
                db.session.commit()

                send_confirmation_email(new_user.email_auth.email)

                flash(f'Пользователь {form.login.data} успешно зарегистрирован! Проверьте ваш email для подтверждения.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Ошибка в email. Такой email уже используется', 'danger')
        else:
            flash('Ошибка в логине. Такой пользователь уже существует', 'danger')

    return render_template('register.html', form=form, bot_username=bot_username)

@auth.route('/confirm/<token>')
def confirm_email(token):
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=3600)
    except:
        flash('Ссылка для подтверждения недействительна или истекла', 'danger')
        return redirect(url_for('auth.register'))

    user = Users.query.join(EmailAuth).filter(EmailAuth.email == email).first_or_404()

    if user.email_auth.confirmed:
        flash('Аккаунт уже подтвержден. Пожалуйста, войдите.', 'success')
    else:
        user.email_auth.confirmed = True
        user.email_auth.confirmed_on = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flash('Вы подтвердили свой аккаунт. Спасибо!', 'success')

    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    bot_username = "SigmaFipibot"
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form, bot_username=bot_username)
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = Users.query.join(EmailAuth).filter(EmailAuth.email == email).first()
        if user and check_password_hash(user.email_auth.password_hash, password):
            session['user_id'] = user.id  
            response = jsonify(status='success', redirect_url=url_for('user.main'))
            
            response.set_cookie('session_id', str(user.id), httponly=True, secure=True, max_age=60*60*24)
            flash('Вы успешно вошли в систему!', 'success')
            return response
        else:
            return jsonify(status='error', message='Неправильный email или пароль.')
    
    return render_template('login.html', form=form, bot_username=bot_username)
