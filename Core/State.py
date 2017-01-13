from builtins import object
import logging

from Core import EventData
from StaticMethod import listify

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class State(object):
    def __init__(self, name: str, on_enter:(str or list) =None, on_exit:(str or list) =None,
                 ignore_invalid_triggers: bool =False):

        self.name = name
        self.on_enter = listify(on_enter) if on_enter else []
        self.on_exit = listify(on_exit) if on_exit else []
        self.ignore_invalid_triggers = ignore_invalid_triggers

    def __str__(self):
        return str(self.name) + "*/*" + str(self.ignore_invalid_triggers) + "*/*" + str(self.on_enter) + "*/*" +\
                str(self.on_exit)
