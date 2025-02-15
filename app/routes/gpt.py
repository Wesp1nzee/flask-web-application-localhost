from ..forms import RegistrationForm
from flask import Blueprint, render_template, flash, request, session, jsonify
from ..models.user import Message, Dialogue
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from ..extensions import db
from ..utils.utils_auth import get_yandex_gpt_messages
from markdown import Markdown

gpt = Blueprint('gpt', __name__, template_folder='templates')
gpt.static_folder = 'static'


def format_markdown(text):
    try:
        md = Markdown(extensions=[
            'fenced_code',
            'tables',
            'attr_list',
            'codehilite',
            'nl2br',
            TableExtension(),
            FencedCodeExtension()
        ])
        
        html = md.convert(text)
        html = html.replace(
            '<pre class="codehilite"><code',
            '<div class="code-block"><button class="copy-button">Копировать</button><pre class="codehilite"><code'
        ).replace('</code></pre>', '</code></pre></div>')
        
        return html
    except Exception as e:
        print(f"Ошибка форматирования markdown: {e}")
        return text

@gpt.route('/gpt', methods=['GET'])
def gpt_page():
    form = RegistrationForm()
    user_id = session.get('user_id')
    if not user_id:
        flash('Вы не зарегистрированы, поэтому вам недоступна поддержка контекста и сохранение чата с ChatGPT.')
        return render_template('gpt.html', form=form)

    dialogues = Dialogue.query.filter_by(
        user_id=user_id,
        is_title_changed=True 
    ).order_by(Dialogue.created_at.desc()).all()


    new_dialogue = Dialogue(user_id=user_id, title="Новый диалог", total_tokens=0)
    db.session.add(new_dialogue)
    db.session.commit()

    return render_template('gpt_page_receive.html', 
                         form=form, 
                         dialogues=dialogues,  
                         current_dialogue=new_dialogue, 
                         messages=[])

@gpt.route('/api/gpt/message', methods=['POST'])
def gpt_message_receive():
    user_id = session.get('user_id')
    user_message = request.json.get('message')
    dialog_id = request.json.get('dialog_id')

    if not user_message:
        return jsonify({'response': 'No message provided'}), 400

    if user_id is None:
        messages = [{"role": "user", "text": user_message}]
        result = get_yandex_gpt_messages(messages)
        response_html = format_markdown(result[0])
        return jsonify({'response': response_html})

    dialogue = Dialogue.query.filter_by(id=dialog_id, user_id=user_id).first() if dialog_id else None
    if not dialogue:
        dialogue = Dialogue(user_id=user_id, title=user_message[:50], total_tokens=0)
        db.session.add(dialogue)
        db.session.commit()

    previous_messages = Message.query.filter_by(dialogue_id=dialogue.id).order_by(Message.id).all()
    
    message_history = []
    for msg in previous_messages:
        message_history.append({"role": "user", "text": msg.message})
        message_history.append({"role": "assistant", "text": msg.response})
    
    message_history.append({"role": "user", "text": user_message})

    response_text, total_tokens = get_yandex_gpt_messages(message_history)
    response_html = format_markdown(response_text)

    new_message = Message(
        dialogue_id=dialogue.id,
        message=user_message,
        response=response_html,
        token=total_tokens
    )
    db.session.add(new_message)
    
    if not dialogue.is_title_changed:
        dialogue.title = user_message[:50]
        dialogue.is_title_changed = True
    
    dialogue.total_tokens += total_tokens
    db.session.commit()

    print(response_html)

    return jsonify({
        'response': response_html,
        'dialog_id': dialogue.id,
        'dialog_title': dialogue.title
    })

@gpt.route('/gpt/<int:dialog_id>', methods=['GET'])
def get_dialog(dialog_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('Вы не зарегистрированы, поэтому вам недоступна поддержка контекста и сохранение чата с ChatGPT.')
        return render_template('gpt.html')

    current_dialogue = Dialogue.query.filter_by(id=dialog_id, user_id=user_id).first()
    if not current_dialogue:
        flash('Диалог не найден или у вас нет доступа к этому диалогу.')
        return render_template('gpt.html')

    other_dialogues = Dialogue.query.filter(
        Dialogue.id != dialog_id,
        Dialogue.user_id == user_id,
        Dialogue.is_title_changed == True  
    ).order_by(Dialogue.created_at.desc()).all()
    
    messages = Message.query.filter_by(dialogue_id=current_dialogue.id).order_by(Message.id).all()

    chat_messages = []
    for msg in messages:
        chat_messages.append({"role": "user", "text": msg.message})
        chat_messages.append({"role": "assistant", "text": msg.response})

    return render_template('gpt_page_receive.html', 
                         dialogues=other_dialogues, 
                         messages=chat_messages, 
                         current_dialogue=current_dialogue)