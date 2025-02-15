from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, EqualTo, Email, NumberRange

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    login = StringField('Логин', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=2, max=25)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=2, max=25)])
    submit = SubmitField('Войти')

class VariantSettingsForm(FlaskForm):
    subject = SelectField('Выберите предмет', choices=[], validators=[DataRequired()])
    task_type = SelectField('Выберите тип задачи', choices=[], validators=[DataRequired()])
    num_tasks = IntegerField('Number of Tasks', validators=[DataRequired(), NumberRange(min=1, message="Must be at least 1")])
    submit = SubmitField('Generate Variant')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ReactionForm(FlaskForm):
    csrf_token = HiddenField()
    type = SelectField('Reaction', choices=[('like', 'Like'), ('dislike', 'Dislike')], validators=[DataRequired()])
    submit = SubmitField('React')