import sys

from socketserver import BaseRequestHandler, BaseServer, ThreadingUDPServer, ThreadingTCPServer

# Windows can't import unix socket servers
if sys.platform != 'win32':
    from socketserver import ThreadingUnixStreamServer
from typing import Union, Text, Callable, Any, Optional, Tuple
from queue import Queue
import os


def unlink_socket(socket_name):
    try:
        os.unlink(socket_name)
    except OSError:
        pass


class QueuedServerMixin:
    """
    A mixin that provides a server object with a queue property
    """
    queue = None  # type: Optional[Queue]


class QueuedBaseServer(BaseServer, QueuedServerMixin):
    def __init__(self, server_address: Any, request_handler: Callable[..., BaseRequestHandler]):
        super().__init__(server_address, request_handler)


if sys.platform != 'win32':
    class QueuedThreadingUnixStreamServer(QueuedServerMixin, ThreadingUnixStreamServer):
        def __init__(self, server_address: Union[Text, bytes], handler: Callable[..., BaseRequestHandler]):
            unlink_socket(server_address)
            super().__init__(server_address, handler)
            self.queue = Queue()
else:
    class QueuedThreadingUnixStreamServer:
        def __init__(self):
            raise NotImplementedError("Windows can't use Unix sockets")


class QueuedThreadingTCPServer(QueuedServerMixin, ThreadingTCPServer):
    def __init__(self, server_address: Tuple[str, int], handler: Callable[..., BaseRequestHandler]):
        super().__init__(server_address, handler)
        self.queue = Queue()
