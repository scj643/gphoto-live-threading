import gphoto2 as gp
from typing import Any, Tuple
from gphoto_threading.servers import QueuedBaseServer, BaseRequestHandler
from gphoto_threading.tasks import TaskHandlerManager
from gphoto_threading.utils import LoggerMixin
from queue import Empty
import time
import socket
from queue import Queue


class QueueRequestHandler(BaseRequestHandler):
    """
    A special handler that allows us to type hint that we have a queue object in the server
    """

    def __init__(self, request: Any, client_address: Any, server: QueuedBaseServer):
        super().__init__(request, client_address, server)
        self.server = server  # type: QueuedBaseServer


class BaseCameraHandler(LoggerMixin):
    camera = None
    broken = None

    def init_camera(self):
        gp.check_result(gp.use_python_logging())
        self.broken = False
        self.get_camera()

    def get_camera(self):
        self.logger.info("Getting camera list")
        camera_list = list(gp.Camera.autodetect())
        self.camera = gp.Camera()
        port_info_list = gp.PortInfoList()
        port_info_list.load()
        self.logger.debug("Excluding iPhones from the camera list")
        non_iphone = [x for x in camera_list if 'Apple' not in x[0]]
        if len(non_iphone) < 1:
            raise ValueError("No cameras attached")
        idx = port_info_list.lookup_path(non_iphone[0][1])

        self.camera.set_port_info(port_info_list[idx])
        self.logger.debug(f"Initializing camera {non_iphone[0]}")
        self.camera.init()
        self.logger.debug(f"Initialized camera {non_iphone[0]}")

        # Start live view
        # This should be replaced with proper calls
        self.camera.capture_preview()

    def camera_loop(self):
        # If we aren't broken stay in the loop
        while not self.broken:
            try:
                try:
                    self.handle_tasks()
                except Empty:
                    pass
                if not self.broken:
                    data = self.camera_live_data()
                    self.handle_data(data)
            except BrokenPipeError:
                self.logger.info("Broken Pipe")
                self.broken = True
            # except gp.GPhoto2Error as e:
            #     self.logger.info("Gphoto2 Error")
            #     broken = True
            except ConnectionResetError:
                self.logger.info("ConnectionResetError")
                self.broken = True

    def camera_live_data(self):
        try:
            p = self.camera.capture_preview()
            data = memoryview(p.get_data_and_size())
            return data
        except gp.GPhoto2Error as e:
            if e.code == -110:
                self.logger.warning(e)
            self.logger.warning("Failed to get camera data")
            self.logger.debug(e)

    def finish(self):
        if self.camera:
            self.camera.exit()

    def handle_data(self, data):
        raise NotImplementedError("Subclass this to handle requests")

    def handle_tasks(self):
        """
        This should be using a queue that is read from.
        If it's empty continue.
        :return:
        """
        raise NotImplementedError("Subclass this to handle tasks")


class CameraSocketHandler(QueueRequestHandler, BaseCameraHandler, LoggerMixin):
    def handle(self) -> None:
        self.init_camera()
        self.camera_loop()
        self.camera.exit()

    def handle_data(self, data):
        if data:
            self.request.sendall(data)
        time.sleep(0.01)

    def handle_tasks(self):
        task = self.server.queue.get_nowait()
        if isinstance(task, TaskHandlerManager):
            task.run_handler(self.camera)
        elif isinstance(task, str):
            if task == 'exit':
                self.broken = True
        self.server.queue.task_done()


class CameraUDPServer(BaseCameraHandler):
    def __init__(self, server_address: Tuple[str, int]):
        self.queue = Queue()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = server_address

    def run(self):
        self.sock.setblocking(False)
        self.init_camera()
        self.camera_loop()
        self.logger.info('Closing')
        self.sock.close()
        self.camera.exit()

    def handle_data(self, data):
        if data:
            self.sock.sendto(data, self.server_address)
        time.sleep(0.02)

    def handle_tasks(self):
        task = self.queue.get_nowait()
        if isinstance(task, TaskHandlerManager):
            task.run_handler(self.camera)
        elif isinstance(task, str):
            if task == 'exit':
                self.broken = True
        self.queue.task_done()
