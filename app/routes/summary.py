from ..models.summary import MainTopic, SummaryTopic, Summary, SummaryTask
from ..models.user import UserTestProgress
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from ..extensions import db

summary = Blueprint('summary', __name__, template_folder='templates')
summary.static_folder = 'static'

@summary.route('/post-list/<subject_name>')
def post_list(subject_name):
    main_topics = MainTopic.query.filter_by(subject_name=subject_name).all()
    subject_name_correct = {
        'phy': 'Физике',
        "rus": "Русскому языку",
        "math": "Математике",
        "inf": "Информатике"
    }
    return render_template('post_list.html', subject_name=subject_name_correct[subject_name], main_topics=main_topics)

@summary.route('/post/<int:topic_id>')
def post_detail(topic_id):
    topic = SummaryTopic.query.get_or_404(topic_id)
    summary = Summary.query.filter_by(summary_topic_id=topic.id).first()
    tasks = SummaryTask.query.filter_by(summary_id=summary.id).all()

    user_id = session.get('user_id')
    if user_id:
        user_progress = UserTestProgress.query.filter_by(user_id=user_id, summary_id=summary.id).first()
        return render_template('post_detail.html', topic=topic, summary=summary, tasks=tasks, user_progress=user_progress)
    
    return render_template('post_detail.html', topic=topic, summary=summary, tasks=tasks, user_progress=False)

@summary.route('/check-answers/<int:topic_id>', methods=['POST'])
def check_test_summary(topic_id):
    topic = SummaryTopic.query.get_or_404(topic_id)
    summary = Summary.query.filter_by(summary_topic_id=topic.id).first()
    tasks = SummaryTask.query.filter_by(summary_id=summary.id).all()
    
    correct_answers = 0
    total_questions = len(tasks)

    for task in tasks:
        selected_option = request.form.get(f'answer_{task.id}')
        if selected_option == task.correct_option:
            correct_answers += 1

    user_id = session.get('user_id')
    if user_id:
        user_progress = UserTestProgress(
            user_id=user_id,
            summary_id=summary.id,
            correct_answers=correct_answers,
            total_questions=total_questions
        )

        db.session.add(user_progress)
        db.session.commit()

    flash(f'Вы ответили правильно на {correct_answers} из {total_questions} вопросов.', 'success')
    return redirect(url_for('summary.post_detail', topic_id=topic.id))