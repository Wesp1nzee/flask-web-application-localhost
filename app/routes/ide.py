from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from ..utils.code_executor import execute_code, IntellisenseProvider, running_processes
from concurrent.futures import ThreadPoolExecutor
from ..extensions import socketio
from ..utils.utils_auth import get_yandex_gpt_messages
import os
import signal
import time

ide = Blueprint('ide', __name__, template_folder='templates')
ide.static_folder = 'static'

executor = ThreadPoolExecutor()

@ide.route('/ide')
def open_ide():
    return render_template('ide.html')

@ide.route('/api/get-help', methods=['POST'])
def get_code_help():
    print('/api/get-help')
    try:
        data = request.json
        code = data.get('code', '')
        error = data.get('error', '')
        
        message = {
            "role": "user",
            "text": f"Проанализируй этот Python код и ошибку. Объясни что не так и как это исправить:\n\nКод:\n{code}\n\nОшибка:\n{error}"
        }
        
        response_text, total_tokens = get_yandex_gpt_messages([message])

        print('response_text, total_tokens')
        
        return jsonify({
            'success': True,
            'explanation': response_text,
            'tokens_used': total_tokens
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@socketio.on('execute')
def handle_execution(data):
    code = data.get('code', '')
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        emit('execution_output', {
            'error': f"Syntax Error: {str(e)}\nLine {e.lineno}, Column {e.offset}\n{e.text}\n{'^':>{e.offset}}"
        })
        return

    executor.submit(execute_code, code, request.sid)

@socketio.on('cancel_execution')
def cancel_execution():
    sid = request.sid
    process = running_processes.get(sid)
    if process:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            print(f"Error terminating process group: {e}")
        time.sleep(0.2)
        if process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except Exception as e:
                print(f"Error killing process group: {e}")
        emit('execution_output', {'error': 'Execution cancelled by user.'}, room=sid)
    else:
        emit('execution_output', {'error': 'No running process found.'}, room=sid)

@socketio.on('stdin_input')
def handle_stdin_input(data):
    sid = request.sid
    process = running_processes.get(sid)
    if process and process.stdin:
        input_value = data.get('text', '')
        try:
            process.stdin.write(input_value.encode())
            process.stdin.flush()
        except Exception as e:
            emit('execution_output', {'error': f"Error sending input: {str(e)}"}, room=sid)

@socketio.on('completion')
def handle_completion(data):
    text = data.get('text', '')
    position = data.get('position', {})
    
    if any(keyword in text.lower() for keyword in [
        'import os', 'import sys', 'import subprocess', 
        'eval(', 'exec(', '__import__', 'open('
    ]):
        emit('completion_result', {'suggestions': []})
        return
        
    suggestions = IntellisenseProvider.get_suggestions(text, position)
    emit('completion_result', {'suggestions': suggestions})

@socketio.on('lint')
def handle_linting(data):
    code = data.get('code', '')
    try:
        compile(code, '<string>', 'exec')
        emit('lint_result', {'valid': True})
    except SyntaxError as e:
        emit('lint_result', {
            'valid': False,
            'error': str(e),
            'line': e.lineno,
            'column': e.offset
        })