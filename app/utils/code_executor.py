import subprocess
import tempfile
import os
import ast
import time
import resource
import fcntl
import jedi
import shutil
from flask import request
from ..extensions import socketio
from typing import Dict, List, Any

# словарь для хранения ответов пользователя на запросы ввода
pending_inputs = {}

# TODO заменить на Redis для распределённых окружениях
running_processes = {}


class IntellisenseProvider:
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'collections',
        'itertools', 'functools', 'string', 'json',
        'typing', 're', 'time', 'array', 'statistics'
    }

    _jedi_initialized = False

    @classmethod
    def _initialize_jedi(cls):
        if not cls._jedi_initialized:
            # Настраиваем директорию кэша
            cache_dir = os.environ.get('JEDI_CACHE_DIR', '/tmp/jedi')
            
            os.makedirs(cache_dir, exist_ok=True)
            
            jedi.settings.cache_directory = cache_dir
            jedi.settings.fast_parser = True
            
            try:
                for filename in os.listdir(cache_dir):
                    filepath = os.path.join(cache_dir, filename)
                    if os.path.isfile(filepath):
                        try:
                            os.unlink(filepath)
                        except OSError:
                            pass
            except OSError:
                pass  
                
            cls._jedi_initialized = True

    @classmethod
    def filter_completion(cls, completion) -> bool:
        if any(keyword in completion.name.lower() for keyword in ['/', '\\', 'path', 'system', 'os', 'sys']):
            return False
        if completion.type == 'module':
            module_name = completion.name.split('.')[0]
            return module_name in cls.ALLOWED_MODULES
        if completion.name.startswith('_'):
            return False
        return True

    @classmethod
    def get_suggestions(cls, text: str, position: Dict[str, int]) -> List[Dict[str, Any]]:
        try:
            cls._initialize_jedi()

            lines = text.split("\n")
            line_num = position["lineNumber"] - 1
            column = position["column"]

            if line_num < 0 or line_num >= len(lines):
                return []
            
            column = max(0, min(column, len(lines[line_num])))
            current_line = lines[line_num][:column]

            if 'import' in current_line or 'from' in current_line:
                return [
                    {
                        'label': module,
                        'kind': 1,
                        'detail': 'module',
                        'documentation': f'Safe module: {module}',
                        'insertText': module
                    }
                    for module in cls.ALLOWED_MODULES
                    if module.startswith(current_line.split()[-1])
                ]

            script = jedi.Script(code=text, path='<memory>')
            completions = script.complete(line=line_num + 1, column=column)
            
            suggestions = []
            for c in completions:
                if not cls.filter_completion(c):
                    continue
                    
                try:
                    doc = c.docstring(raw=True) or ''
                except Exception as e:
                    print(f"Error getting docstring for {c.name}: {e}")
                    doc = ""

                suggestion = {
                    'label': c.name,
                    'kind': 1,
                    'detail': c.type,
                    'documentation': doc,
                    'insertText': c.name
                }
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            print(f"Jedi completion error: {str(e)}")
            return []

def preexec_function():
    """Ограничение ресурсов для подпроцесса"""
    os.setsid()
    mem_limit = 256 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
    cpu_limit = 5
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))

def check_forbidden_operations(code: str) -> bool:
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'pathlib', 
        'socket', 'requests', 'urllib', 'ftplib'
    }
    FORBIDDEN_CALLS = {
        'eval', 'exec', 'open', '__import__', 
        'globals', 'locals', 'compile'
    }
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    module_name = name.name.split('.')[0]
                    if module_name in FORBIDDEN_MODULES:
                        return False
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in FORBIDDEN_MODULES:
                    return False
                for name in node.names:
                    if name.name in FORBIDDEN_CALLS:
                        return False
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in FORBIDDEN_CALLS:
                        return False
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in FORBIDDEN_CALLS:
                        return False
        return True
    except SyntaxError:
        return False

def execute_code(code: str, sid: str):
    if not check_forbidden_operations(code):
        socketio.emit('execution_output', {'error': "Security Error: Forbidden operations detected"}, room=sid)
        return

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        modified_code = (
            "import sys\n"
            "import builtins\n"
            "def custom_input(prompt=\"\"):\n"
            "    sys.stdout.write(prompt)\n"
            "    sys.stdout.flush()\n"
            "    print(\"<<<INPUT_REQUEST>>>\", flush=True)\n"
            "    return sys.stdin.readline().rstrip(\"\\n\")\n"
            "builtins.input = custom_input\n"
        ) + code
        temp_file.write(modified_code)
        temp_file_path = temp_file.name

    try:
        start_time = time.time()
        process = subprocess.Popen(
            ['python3', '-u', temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            preexec_fn=preexec_function
        )
        flags = fcntl.fcntl(process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        flags_err = fcntl.fcntl(process.stderr, fcntl.F_GETFL)
        fcntl.fcntl(process.stderr, fcntl.F_SETFL, flags_err | os.O_NONBLOCK)
        running_processes[sid] = process

        while True:
            try:
                line = process.stdout.readline()
            except Exception:
                line = None
            if line:
                if "<<<INPUT_REQUEST>>>" in line:
                    prompt = line.replace("<<<INPUT_REQUEST>>>", "")
                    socketio.emit('execution_input_request', {'prompt': prompt}, room=sid)
                    while sid not in pending_inputs:
                        time.sleep(0.1)
                    user_input = pending_inputs.pop(sid)
                    process.stdin.write(user_input + "\n")
                    process.stdin.flush()
                else:
                    socketio.emit('execution_output', {'output': line}, room=sid)
            if process.poll() is not None:
                break
            time.sleep(0.05)

        try:
            error_output = process.stderr.read()
        except Exception:
            error_output = ''
        process.wait()
        execution_time = time.time() - start_time

        if process.returncode is not None and process.returncode < 0:
            return

        if error_output:
            socketio.emit('execution_output', {'error': error_output}, room=sid)
        else:
            socketio.emit('execution_output', {
                'execution_time': f"{execution_time:.2f}s",
                'status': 'success'
            }, room=sid)
    except Exception as e:
        socketio.emit('execution_output', {'error': f"Execution error: {str(e)}"}, room=sid)
    finally:
        if sid in running_processes:
            del running_processes[sid]
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@socketio.on('input_response')
def handle_input_response(data):
    sid = data.get('sid') or request.sid
    pending_inputs[sid] = data.get('input', '')