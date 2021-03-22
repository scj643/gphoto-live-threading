from threading import Thread
from gphoto_threading.handlers import CameraSocketHandler, CameraUDPServer
from gphoto_threading.tasks import TaskHandlerManager
from gphoto_threading.servers import QueuedThreadingUnixStreamServer, QueuedThreadingTCPServer
import argparse
import logging

SOCKET_PATH = '/tmp/gphoto.soc'

parser = argparse.ArgumentParser()

output_group = parser.add_mutually_exclusive_group()

output_group.add_argument('-u', '--udp', help="Output video to udp", action='store_true')
output_group.add_argument('-t', '--tcp', help="Output video over TCP", action='store_true')

parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
parser.add_argument('--debug', help="Do not show the input loop for debugging reasons.", action='store_true')

if __name__ == '__main__':
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if args.udp:
        server = CameraUDPServer(('127.0.0.1', 8833))
        server_thread = Thread(target=server.run, name='live_thread')
    elif args.tcp:
        server = QueuedThreadingTCPServer(('127.0.0.1', 8833), CameraSocketHandler)
        server_thread = Thread(target=server.serve_forever, name='live_thread')
    else:
        raise ValueError("No valid output set.")
    server_thread.daemon = True
    server_thread.start()
    while True:
        if not args.debug:
            try:
                input_task = input('config task: ')
                try:
                    if input_task == 'exit':
                        logging.info("Exiting")
                        server.queue.put('exit')
                        server_thread.join(10)
                        exit(0)
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
