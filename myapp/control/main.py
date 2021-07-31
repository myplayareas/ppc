import functools
from flask import Blueprint

from flask import Flask
import threading
import multiprocessing
import logging
from threading import Thread
from queue import Queue
import time
from flask import redirect
import uuid
from functools import wraps
from flask import current_app, request, abort
from werkzeug.exceptions import HTTPException, InternalServerError
from myapp.config.db import get_db
import datetime
from myapp.utils.utilidades import display
from myapp.utils.utilidades import dictionaryWithAllCommmits
from myapp.utils.utilidades import create_work
from myapp.utils.utilidades import perform_work
from flask import url_for
from myapp.control.auth import login_required
from flask import render_template
from flask import flash
from myapp.services.repositorio import criar_repositorio
from myapp.utils.utilidades import create_new_thread_default
from myapp.services.repositorio import listar_repositorios_usuario
from myapp.services.repositorio import listar_repositorios
from myapp.services.repositorio import atualiza_repositorio

bp = Blueprint("main", __name__, url_prefix='/main') 

tasks = {}

# List of producers
list_of_producers = list()

# Lista da strings de repositorios
lista_de_repositorios = list()

link_processar_repositorios = ""

work = Queue()
finished = Queue()

consumer = None

def flask_async(f):
    """
    This decorator transforms a sync route to asynchronous by running it in a background thread.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        def task(app, environ):
            # Create a request context similar to that of the original request
            with app.request_context(environ):
                try:
                    # Run the route function and record the response
                    tasks[task_id]['result'] = f(*args, **kwargs)
                except HTTPException as e:
                    tasks[task_id]['result'] = current_app.handle_http_exception(e)
                except Exception as e:
                    # The function raised an exception, so we set a 500 error
                    tasks[task_id]['result'] = InternalServerError()
                    if current_app.debug:
                        # We want to find out if something happened so reraise
                        raise

        # Assign an id to the asynchronous task
        task_id = uuid.uuid4().hex

        # Record the task, and then launch it
        tasks[task_id] = {'task': threading.Thread(
            target=task, args=(current_app._get_current_object(), request.environ))}
        tasks[task_id]['task'].start()

        # Return a 202 response, with an id that the client can use to obtain task status
        return {'TaskId': task_id}, 202

    return wrapped

@bp.route("/")
@login_required
def index():
    lista_de_repositorios = listar_repositorios_usuario(1)
    return render_template('main/listar.html', my_link=link_processar_repositorios, my_repositories=lista_de_repositorios)

@bp.route('/foo')
@login_required
@flask_async
def foo():
    time.sleep(10)
    return {'Result': True}

@bp.route('/foo/<task_id>', methods=['GET'])
@login_required
def foo_results(task_id):
    """
        Return results of asynchronous task.
        If this request returns a 202 status code, it means that task hasn't finished yet.
        """
    task = tasks.get(task_id)
    if task is None:
        abort(404)
    if 'result' not in task:
        return {'TaskID': task_id}, 202
    return task['result']

def produzir_repositorios(repositorios, work, finished):
    for each in repositorios: 
        thread = create_new_thread_default(['client1', each, work, finished])
        list_of_producers.append(thread)
        criar_repositorio(each, each)
        
    return url_for('main.processar_em_background')

@bp.route("/criar", methods=["GET", "POST"])
@login_required
def criar():
    """Create a new repository for the current user."""
    if request.method == "POST":
        cadeia_de_repositorios = request.form["repositorios"]
        lista_de_repositorios = cadeia_de_repositorios.split(",")
        error = None
        error_processing_repository = None

        if len(lista_de_repositorios) == 0:
            error = "List is required."

        if error is not None:
            flash(error, 'danger')
        else:
            try:
                # Processa o repositorio para gerar a nuvem de arquivos mais modificados
                link_processar_repositorios = produzir_repositorios(lista_de_repositorios, work, finished)
                # Limpa a lista de string de repositórios
                lista_de_repositorios.clear()
            except Exception as e:
                error_processing_repository = "Erro na produção dos repositorios" + e
                if error_processing_repository is not None:
                    flash(error_processing_repository, 'danger')
                    return redirect(url_for("main.index"))
            message = "Repositórios criado com sucesso!"
            flash(message, 'success')
            return redirect(url_for("main.index"))

    return render_template("main/criar.html")

@bp.route("/processar")
@login_required
@flask_async
def processar_em_background():
    # Create the thread consumer repositories stored in the Queue
    consumer = Thread(target=perform_work, args=[work, finished], daemon=True)

    print('Start the consumer')
    # Start the consumer of queue of requests
    consumer.start()

    for each in list_of_producers:
        each.join()
        display('Producer ' + each.getName() + ' has finished with success!')
    list_of_producers.clear()

    consumer.join()
    display('Consumer has finished')
    display('Finished the main process.')

    return '<p> processamento dos repositórios foi concluído com sucesso!'

""" Mostra a lista de repositorios  """
@bp.route("/repositorios/usuario/<int:id>")
@login_required
def repositorios_usuarios(id):
    #Carrega repositorios registrados pelo usuario
    lista_repositorios = listar_repositorios_usuario(id)
    return render_template("main/repositorios_usuario.html", repositorios=lista_repositorios)