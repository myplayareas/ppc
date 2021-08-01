import functools
from flask import Blueprint
import threading
import multiprocessing
import logging
from threading import Thread
import time
import datetime
from pydriller import Repository
from flask import Flask
from myapp.services.repositorio import atualiza_repositorio
from flask import current_app

logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

def atualizar_repositorio(app, repository):
    try:
        with app.app_context():
            atualiza_repositorio(repository, 2)
    except Exception as e:
        display(f'Error during access data base to update in {repository} error: {e}')

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
        display(f'Error during processing dictionaryWithAllCommmits in {repository} error: {e}')
        dictionaryAux = None
    return dictionaryAux

# Producer: the client send a request to the queue
def create_work(client, repository, queue, finished):
    #lock
    finished.put(False)
    # insert element in queue
    my_request = (client, repository)
    queue.put(my_request)
    display(f'Producing request from client {client} and {repository} to enqueue')
    finished.put(True)
    #unlock 
    display(f'The request {my_request} has done')

def create_new_thread_banco(app, repository):
    thread = Thread(target=atualizar_repositorio, args=[app, repository], daemon=True)
    display('It was created a new Thread ' + thread.getName() + ' to access database to update repository ' + repository)
    thread.start()
    thread.join()
    display('Thread ' + thread.getName() + ' save ' + repository + 'in the database')

def create_new_thread(repository):
    thread = Thread(target=dictionaryWithAllCommmits, args=[repository], daemon=True) 
    display('It was created a new Thread ' + thread.getName() + ' to analyse repository ' + repository)
    thread.start()
    thread.join()
    display('Thread ' + thread.getName() + ' finished analysing of repository ' + repository)
    
def create_new_thread_default(argumentos):
    thread = Thread(target=create_work, args=[argumentos[0], argumentos[1], argumentos[2], argumentos[3]], daemon=True)
    display('It was created a new Thread ' + thread.getName() + ' to enqueue repository ' + argumentos[1])
    thread.start()
    display('Thread ' + thread.getName() + ' finished enqueueing of repository ' + argumentos[1])
    return thread

# Consumer - For each request inserted in the Queue the consumer fire one thread to process each repository stored in the Queue
def perform_work(app, work, finished):
    counter = 0
    v =  None
    while True:
        if not work.empty():
            v = work.get()
            display(f'Consuming {counter}: {v}')
            print(f'Cloning repository {v[1]} from client {v[0]}')
            create_new_thread(v[1])
            create_new_thread_banco(app, v[1])
            counter += 1
        else:
            q = finished.get()
            display(f'There is no itens to consume!')
            if q == True:
                break
        if v is not None: 
            display(f'The item {v} has consumed with success!')