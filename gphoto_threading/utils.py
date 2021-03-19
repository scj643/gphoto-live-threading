import logging


class LoggerMixin(object):
    """
    From https://dane.engineering/post/python-mixins/
    """

    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
