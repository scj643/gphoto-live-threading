import gphoto2 as gp
from gphoto_threading.utils import LoggerMixin

USE_SINGLE_SET = True


class TaskHandler(LoggerMixin):
    CMD_PREFIX = None

    def __init__(self, command: str, camera: gp.Camera, handler):
        self.command = command
        self.camera = camera
        self.handler = handler
        self.config = None
        self.run()

    def set_config(self, config_name, conf):
        if USE_SINGLE_SET:
            self.camera.set_single_config(config_name, conf)
        else:
            self.camera.set_config(self.config)

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
            if current_pos <= len(c_list) - 1:
                conf.set_value(c_list[current_pos])
                self.set_config(config_name, conf)
                self.logger.debug(f'Set value of {config_name} to {c_list[current_pos]}')
            else:
                self.logger.info(f"Value of {config_name} can not go higher")
        elif self.command[1] == '-':
            current_pos -= 1
            if current_pos >= 0:
                conf.set_value(c_list[current_pos])
                self.set_config(config_name, conf)
                self.logger.debug(f'Set value of {config_name} to {c_list[current_pos]}')
            else:
                self.logger.info(f"Value of {config_name} can not go lower")


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


class ShutterToggleTaskHandler(TaskHandler):
    CMD_PREFIX = 't'

    def run(self):
        if self.handler.shutter_up:
            self.camera.exit()
            self.handler.shutter_up = False
            self.handler.get_camera()
        else:
            self.handler.raise_shutter()


class FocusTaskHandler(TaskHandler):
    CMD_PREFIX = 'f'

    def run(self):
        self.get_config()
        focus = self.config.get_child_by_name('autofocusdrive')
        focus.set_value(not bool(focus.get_value()))
        try:
            self.set_config('autofocusdrive', focus)
        except gp.GPhoto2Error as e:
            if e.code == -1:
                self.logger.info("Failed to focus")
            else:
                raise e


class CustomValueTaskHandler(TaskHandler):
    CMD_PREFIX = 'c'

    def run(self):
        self.get_config()
        args = self.command.split(' ')
        if len(args) == 2:
            try:
                conf = self.config.get_child_by_name(args[1])
                self.logger.info(f"Config {args[1]} is {conf.get_value()}")
            except gp.GPhoto2Error as e:
                if e.code == -2:
                    self.logger.info(f"Config {args[1]} does not exist")

        if len(args) == 3:
            try:
                set_value = args[2]
                conf = self.config.get_child_by_name(args[1])
                if conf.get_type() == gp.GP_WIDGET_RANGE:
                    set_value = float(set_value)
                    value_range = conf.get_range()
                    if not value_range[0] <= set_value <= value_range[1] and set_value % value_range[2]:
                        self.logger.info(f"Config {args[1]} was not in range.")
                        return
                conf.set_value(set_value)
                self.set_config(args[1], conf)
            except gp.GPhoto2Error as e:
                if e.code == -2:
                    self.logger.info(f"Config {args[1]} does not exist")


class TaskHandlerManager(object):
    TASK_HANDLERS = [FocusTaskHandler, IsoTaskHandler, FstopTaskHandler, CustomValueTaskHandler,
                     ShutterToggleTaskHandler]

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

    def run_handler(self, camera: gp.Camera, handler):
        self.handler(self.cmd, camera, handler)
