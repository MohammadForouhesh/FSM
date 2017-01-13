import logging

from StaticMethod import listify

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from builtins import object

from Core import EventData
from Core.Condition import Condition


class Transition(object):
    __slots__ = 'source', 'dest', 'conditions', 'unless', 'before', 'after', 'prepare'

    def __init__(self, source: str, dest: str, conditions:(str or list) =None):
        self.source = source
        self.dest = dest

        self.conditions = []
        if conditions is not None:
            for c in listify(conditions):
                self.conditions.append(Condition(c))

    def execute(self, event_data: EventData):
        machine = event_data.machine

        for c in self.conditions:
            if not c.check(event_data):
                return False

        self._change_state(event_data)

        return True

    def _change_state(self, event_data: EventData):
        event_data.machine.get_state(self.source).exit(event_data)
        event_data.machine.set_state(self.dest, event_data.model)
        event_data.update(event_data.model)
        event_data.machine.get_state(self.dest).enter(event_data)
