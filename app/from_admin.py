from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, FieldList, FormField, FileField
from flask_ckeditor import CKEditorField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = CKEditorField('Content', validators=[DataRequired()])
    tags = StringField('Tags')
    author_id = IntegerField('Author ID')
    photo = FileField('Photo') 
    submit = SubmitField('Submit')

class SummaryTaskForm(FlaskForm):
    task_question = StringField('Вопрос', validators=[DataRequired()])
    option1 = StringField('Вариант 1', validators=[DataRequired()])
    option2 = StringField('Вариант 2', validators=[DataRequired()])
    option3 = StringField('Вариант 3', validators=[DataRequired()])
    option4 = StringField('Вариант 4', validators=[DataRequired()])
    correct_option = StringField('Правильный ответ', validators=[DataRequired()])

class SummaryForm(FlaskForm):
    subject_name = SelectField('Subject Name', choices=[
        ('phy', 'Физике'),
        ('rus', 'Русскому языку'),
        ('math', 'Математики'),
        ('inf', 'Информатике')
    ], validators=[DataRequired()])
    topic_name = StringField('Название темы', validators=[DataRequired()])
    content = CKEditorField('Контент', validators=[DataRequired()])
    tasks = FieldList(FormField(SummaryTaskForm), min_entries=1, validators=[DataRequired()])
    submit = SubmitField('Submit')