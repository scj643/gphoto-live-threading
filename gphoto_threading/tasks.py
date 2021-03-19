import gphoto2 as gp
from gphoto_threading.utils import LoggerMixin


class TaskHandler(LoggerMixin):
    CMD_PREFIX = None

    def __init__(self, command: str, camera: gp.Camera):
        self.command = command
        self.camera = camera
        self.config = None
        self.run()

    def get_config(self) -> None:
        """
        Grab the config from the camera.
        """
        while not self.config:
            # noinspection PyArgumentList
            self.config = self.camera.get_config()

    def run(self):
        raise NotImplemented


class ChoiceBaseTaskHandler(TaskHandler):
    def parse_config_named(self, config_name):
        conf = self.config.get_child_by_name(config_name)
        c_list = [x for x in conf.get_choices()]
        current = conf.get_value()
        current_pos = c_list.index(current)
        if self.command[1] == '+':
            current_pos += 1
            if current_pos <= len(c_list):
                conf.set_value(c_list[current_pos])
                self.camera.set_config(self.config)
        elif self.command[1] == '-':
            current_pos -= 1
            if current_pos >= 0:
                conf.set_value(c_list[current_pos])
                self.camera.set_config(self.config)


class IsoTaskHandler(ChoiceBaseTaskHandler):
    CMD_PREFIX = 'i'

    def run(self):
        self.get_config()
        self.parse_config_named('iso')


class FstopTaskHandler(ChoiceBaseTaskHandler):
    CMD_PREFIX = 's'

    def run(self):
        self.get_config()
        self.parse_config_named('f-number')


class FocusTaskHandler(TaskHandler):
    CMD_PREFIX = 'f'

    def run(self):
        self.get_config()
        focus = self.config.get_child_by_name('autofocusdrive')
        focus.set_value(not bool(focus.get_value()))
        try:
            self.camera.set_config(self.config)
        except gp.GPhoto2Error as e:
            if e.code == -1:
                self.logger.info("Failed to focus")
            else:
                raise e


class TaskHandlerManager(object):
    TASK_HANDLERS = [FocusTaskHandler, IsoTaskHandler, FstopTaskHandler]

    def __init__(self, cmd: str):
        """
        Manage the task handlers
        :param cmd: cmd to pass to the handler (this includes the prefix)
        """
        self.handler = None
        self.cmd = cmd
        self.handler = self.find_handler()

    def find_handler(self):
        matches = [x for x in self.TASK_HANDLERS if self.cmd.startswith(x.CMD_PREFIX)]
        if len(matches) == 0:
            raise ValueError(f"No handler for {self.cmd}")
        else:
            matches.sort()
            # return the last match so that if there is a case where there are multiple matches.
            return matches[-1]

    def run_handler(self, camera: gp.Camera):
        self.handler(self.cmd, camera)
