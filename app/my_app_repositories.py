import random
import threading
import multiprocessing
import logging
from threading import Thread
from queue import Queue
import time
logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)

def display(msg):
    threadname = threading.current_thread().name
    processname = multiprocessing.current_process().name
    logging.info(f'{processname}\{threadname}: {msg}')

# Producer
def create_work(queue, finished, max):
    #lock
    finished.put(False)
    # insert element in queue
    for item in range(max):
        value = random.randint(1, 100)
        client = 'Client ' + str(item)
        repository = 'http://github.com/repo' + str(value)
        my_request = (client, repository)
        queue.put(my_request)
        display(f'Producing {item}: {repository} ')
    finished.put(True)
    #unlock 
    display(f'The production of items from {0} to {max} has finished')

# Consumer
def perform_work(work, finished):
    counter = 0
    while True:
        if not work.empty():
            v = work.get()
            display(f'Consuming {counter}: {v}')
            print(f'Cloning repository {v[1]} from client {v[0]}')
            time.sleep(random.randint(1,5))
            counter += 1
        else:
            q = finished.get()
            if q == True:
                break
        display(f'The item {v} has consumed')

def main():
    max = 10
    work = Queue()
    finished = Queue()

    # Create the threads producer and consumer
    producer = Thread(target=create_work, args=[work, finished, max], daemon=True)
    consumer = Thread(target=perform_work, args=[work, finished], daemon=True)

    producer.start()
    consumer.start()

    producer.join()
    display('Producer has finished')

    consumer.join()
    display('Consumer has finished')

    display('Finished')


if __name__ == "__main__":
    main() 

