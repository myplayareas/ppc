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
import datetime
from flask import url_for
from myapp.control.auth import login_required
from flask import render_template
from flask import flash
from myapp.utils import utilidades
from myapp.services import repositorios
from flask import jsonify
from flask import g

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
    lista_de_repositorios = repositorios.listar_repositorios_usuario(g.user['id'])
    print(f'Fila de reposit??rios: {work.queue}')

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

def produzir_repositorios(lista_de_repositorios, work, finished):
    client = g.user['id']
    for each in lista_de_repositorios: 
        thread = utilidades.create_new_thread_default([client, each, work, finished])
        list_of_producers.append(thread)
        repositorios.criar_repositorio(utilidades.pega_nome_repositorio(each), each, g.user['id'])
        
    return url_for('main.processar_em_background')

def repositorios_ja_existem(lista_de_repositorios, user_id):
    lista_de_repositorios_ja_existem = list()
    try: 
        for each in lista_de_repositorios:
            resultado = repositorios.buscar_repositorio_por_nome_e_usuario(utilidades.pega_nome_repositorio(each), user_id)
            if len(resultado) > 0:
                lista_de_repositorios_ja_existem.append( resultado )
    except Exception as e:
        print(f'Erro ao consultar repositorio no banco: {e}')
    return lista_de_repositorios_ja_existem

@bp.route("/criar", methods=["GET", "POST"])
@login_required
def criar():
    """Create a new repository for the current user."""
    if request.method == "POST":
        error = None
        error_processing_repository = None
        cadeia_de_repositorios = request.form["repositorios"]

        # Nenhum repositorio foi passado
        if len(cadeia_de_repositorios) == 0:
            error = "List of repositories is required."
            flash(error, 'danger')
            return render_template("main/criar.html")
        else:
            lista_de_repositorios = cadeia_de_repositorios.split(",")
            testa_repositorios = repositorios_ja_existem(lista_de_repositorios, g.user['id'])

        # Checa se ja existe algum repositorio no banco
        if len(testa_repositorios) > 0: 
            lista = list()
            for each in testa_repositorios:
                lista.append(each[0]['name'])

            error = f'O(s) repositorio(s) {lista} j?? foi(for??o) cadastrado(s) no banco!'
            flash(error, 'danger')
            return render_template("main/criar.html")

        try:
            # Produtor que enfileira o repositorio na lista de repositorios
            link_processar_repositorios = produzir_repositorios(lista_de_repositorios, work, finished)
            # Limpa a lista de string de reposit??rios
            lista_de_repositorios.clear()
        except Exception as e:
            error_processing_repository = "Erro na produ????o dos repositorios" + str(e)
            if error_processing_repository is not None:
                flash(error_processing_repository, 'danger')
                return redirect(url_for("main.index"))
        
        message = "Reposit??rio(s) criado(s) com sucesso!"
        flash(message, 'success')
        return redirect(url_for("main.index"))

    return render_template("main/criar.html")

@bp.route("/processar")
@login_required
@flask_async
def processar_em_background():
    # Create the thread consumer repositories stored in the Queue
    consumer = Thread(target=utilidades.perform_work, args=[current_app._get_current_object(), work, finished], daemon=True)

    print('Start the consumer')
    # Start the consumer of queue of requests
    consumer.start()

    if len(list_of_producers) > 0:
        for each in list_of_producers:
            each.join()
            utilidades.display('Producer ' + each.getName() + ' has finished with success!')
        list_of_producers.clear()

    consumer.join()
    utilidades.display('Consumer has finished')
    utilidades.display('Finished the main process.')

    return '<p> processamento dos reposit??rios foi conclu??do com sucesso!'

""" Mostra a lista de repositorios  """
@bp.route("/repositorios/usuario/<int:id>")
@login_required
def repositorios_usuarios(id):
    #Carrega repositorios registrados pelo usuario
    lista_repositorios = repositorios.listar_repositorios_usuario(id)
    return render_template("main/repositorios_usuario.html", repositorios=lista_repositorios)

@bp.context_processor
def utility_processor():
    def status_repositorio(status):
        valor = ''
        try:
            lista_de_status = list()
            lista_de_status = ['Erro','Registrado', 'Analisado']
            valor = lista_de_status[status]
        except Exception as e:
            utilidades.display('Erro de status: valor ' + valor + ' - status:  ' + str(status) + ' - ' + str(e))
        return valor
    return dict(status_repositorio=status_repositorio)
    
@bp.route("/repositorio/<int:id>/analisado", methods=["GET"])
@login_required
def visualizar_analise_repositorio(id):
    repositorio = repositorios.buscar_repositorio_por_id(id)
    link = repositorio[0]['link']
    name = repositorio[0]['name']
    creation_date = repositorio[0]['creation_date']
    analysis_date = repositorio[0]['analysis_date']
    status = repositorio[0]['analysed']

    relative_path = 'repositories' + '/' + str(g.user['id']) + '/' + name + '.json'
    relative_path_file_name = url_for('static', filename=relative_path)

    return render_template("main/analisado.html", my_link=link, my_name=name, my_creation_date=creation_date,
                                my_analysis_date=analysis_date, my_status=status,
                                my_relative_path_file_name=relative_path_file_name)