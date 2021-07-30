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

bp = Blueprint("main", __name__)

tasks = {}

list_of_repositories = ['https://github.com/armandossrecife/restapi.git', 'https://github.com/armandossrecife/sysweb.git', 
'https://github.com/armandossrecife/spoon-example.git']

# List of producers
list_of_producers = list()

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

@bp.route('/foo')
@flask_async
def foo():
    time.sleep(10)
    return {'Result': True}

@bp.route('/foo/<task_id>', methods=['GET'])
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

@bp.route("/produzir")
def produzir_repositorios():
    # Create the threads producer to insert requests in the Queue
    c1 = Thread(target=create_work, args=['client1', list_of_repositories[0], work, finished], daemon=True)
    c2 = Thread(target=create_work, args=['client2', list_of_repositories[1], work, finished], daemon=True)
    c3 = Thread(target=create_work, args=['client3', list_of_repositories[2], work, finished], daemon=True)
    
    list_of_producers.append(c1)
    list_of_producers.append(c2)
    list_of_producers.append(c3)
    
    print('Start all clients')
    # Start the request for each client
    for each in list_of_producers:
        each.start()

    return '<p> Criada requisição de repositórios. <a href="/processar">Processar repositórios</a>'

@bp.route("/processar")
@flask_async
def processar_em_background():
    repositorios_concatenados = ""
    for each in list_of_repositories:
        repositorios_concatenados = repositorios_concatenados + each + ", "
    
    final = "[" + repositorios_concatenados + "]"

    # Create the thread consumer repositories stored in the Queue
    consumer = Thread(target=perform_work, args=[work, finished], daemon=True)

    print('Start the consumer')
    # Start the consumer of queue of requests
    consumer.start()

    for each in list_of_producers:
        each.join()
        display('Producer ' + each.getName() + ' has finished with success!')

    consumer.join()
    display('Consumer has finished')

    display('Finished the main process.')

    return '<p> Lista de repositórios: ' + final