import functools
from flask import Blueprint

from flask import Flask
import threading
import multiprocessing
import logging
from threading import Thread
from queue import Queue
import time
from pydriller import Repository
from flask import redirect
import time
import uuid
from functools import wraps
from flask import current_app, request, abort
from werkzeug.exceptions import HTTPException, InternalServerError
from myapp.config.db import get_db
import datetime

logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

bp = Blueprint("main", __name__)

tasks = {}

list_of_repositories = ['https://github.com/armandossrecife/restapi.git', 'https://github.com/armandossrecife/sysweb.git', 
'https://github.com/armandossrecife/spoon-example.git']

# List of producers
list_of_producers = list()

work = Queue()
finished = Queue()

consumer = None

def display(msg):
    threadname = threading.current_thread().name
    processname = multiprocessing.current_process().name
    logging.info(f'{processname}\{threadname}: {msg}')

# List all Commits from Authors
# return a dictionary like this: hash, author, date, list of files in commit
# dictionary = {'hash': ['author', 'date of commit', [file1, file2, ...]]}
def dictionaryWithAllCommmits(repository):
    dictionaryAux = {}
    try: 
        for commit in Repository(repository).traverse_commits():
            commitAuthorNameFormatted = '{}'.format(commit.author.name)
            commitAuthorDateFormatted = '{}'.format(commit.author_date)
            listFilesModifiedInCommit = []
            for modification in commit.modified_files:
                itemMofied = '{}'.format(modification.filename)
                listFilesModifiedInCommit.append(itemMofied)
            dictionaryAux[commit.hash] = [commitAuthorNameFormatted, commitAuthorDateFormatted, listFilesModifiedInCommit] 
    except Exception as e:
        display(f'Error during processing dictionaryWithAllCommmits in {repository}')
        dictionaryAux = None
    return dictionaryAux

# Producer: the client send a request to the queue
def create_work(client, repository, queue, finished):
    #lock
    finished.put(False)
    # insert element in queue
    my_request = (client, repository)
    queue.put(my_request)
    display(f'Producing request from client {client} and {repository} ')
    finished.put(True)
    #unlock 
    display(f'The request {my_request} has finished')

def create_new_thread(repository):
    thread = Thread(target=dictionaryWithAllCommmits, args=[repository], daemon=True) 
    display('It was created a new Thread ' + thread.getName() + ' to process repository ' + repository)
    thread.start()
    thread.join()
    display('Thread ' + thread.getName() + ' finished processing of repository ' + repository)

# Consumer - For each request inserted in the Queue the consumer fire one thread to process each repository stored in the Queue
def perform_work(work, finished):
    counter = 0
    while True:
        if not work.empty():
            v = work.get()
            display(f'Consuming {counter}: {v}')
            print(f'Cloning repository {v[1]} from client {v[0]}')
            create_new_thread(v[1])
            counter += 1
        else:
            q = finished.get()
            if q == True:
                break
        display(f'The item {v} has consumed with success!')

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

def inserir_repositorio(name, link):
    # Conecta com o banco para inserir um novo repositorio
    db = get_db()
    query_insert = "INSERT INTO repository (name, link, user_id, creation_date, analysis_date, analysed) VALUES (?, ?, ?, ?, ?, ?)"
    db.execute(
        query_insert,(name, link, 1, datetime.datetime.now(), datetime.datetime.now(), 1),
    )

@bp.route("/criar")
def criar():
    # Create the threads producer to insert requests in the Queue
    c1 = Thread(target=create_work, args=['client1', list_of_repositories[0],  work, finished], daemon=True)
    c2 = Thread(target=create_work, args=['client2', list_of_repositories[1], work, finished], daemon=True)
    c3 = Thread(target=create_work, args=['client3', list_of_repositories[2], work, finished], daemon=True)
    
    list_of_producers.append(c1)
    list_of_producers.append(c2)
    list_of_producers.append(c3)
    
    print('Start all clients')
    # Start the request for each client
    for each in list_of_producers:
        each.start()

    return '<p> Criada requisição de repositórios. <a href="/listar">Listar</a>'

def listar_repositorios():
    db = get_db()
    query = "select * from repository where user_id = ?"
    repositorios = db.execute( query , (id,) ).fetchall()

@bp.route("/listar")
@flask_async
def listar():
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