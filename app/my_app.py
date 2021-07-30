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
        queue.put(value)
        display(f'Producing {item}: {value} ')
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
            counter += 1
        else:
            q = finished.get()
            if q == True:
                break
        display(f'The item {counter-1} has consumed')

def main():
    max = 50
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

