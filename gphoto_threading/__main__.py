from threading import Thread
from gphoto_threading.handlers import CameraSocketHandler, CameraUDPServer
from gphoto_threading.tasks import TaskHandlerManager
from gphoto_threading.servers import QueuedThreadingUnixStreamServer, QueuedThreadingTCPServer
import logging

SOCKET_PATH = '/tmp/gphoto.soc'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    udp = True
    debug = False
    if udp:
        server = CameraUDPServer(('127.0.0.1', 8833))
        server_thread = Thread(target=server.run, name='live_thread')
    else:
        server = QueuedThreadingTCPServer(('127.0.0.1', 8833), CameraSocketHandler)
        server_thread = Thread(target=server.serve_forever, name='live_thread')
    server_thread.daemon = True
    server_thread.start()
    while True:
        if not debug:
            try:
                input_task = input('config task: ')
                try:
                    task_handler = TaskHandlerManager(input_task)
                    server.queue.put(task_handler)
                except ValueError:
                    print(f'Task with prefix for {input_task} does not exist')
                except KeyboardInterrupt:
                    logging.info("Exiting")
                    server.queue.put('exit')
                    server_thread.join(10)
                    exit(0)
            except KeyboardInterrupt:
                logging.info("Exiting")
                server.queue.put('exit')
                server_thread.join(10)
                exit(0)
