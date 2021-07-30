import functools
from flask import Blueprint
import threading
import multiprocessing
import logging
from threading import Thread
import time
import datetime
from pydriller import Repository

logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

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

