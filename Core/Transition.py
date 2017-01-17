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
        logger.debug("%sInitiating transition from state %s to state %s...",
                     event_data.machine.id, self.source, self.dest)
        machine = event_data.machine

        for c in self.conditions:
            if not c.check(event_data):
                logger.debug("%sTransition condition failed: %s() does not " +
                             "return %s. Transition halted.", event_data.machine.id, c.func, c.target)
                return False
        self._change_state(event_data)
        return True

    def _change_state(self, event_data: EventData):
        event_data.machine.get_state(self.source).exit(event_data)
        event_data.machine.set_state(self.dest, event_data.model)
        event_data.update(event_data.model)
        event_data.machine.get_state(self.dest).enter(event_data)

    def add_callback(self, trigger: str, func: str):
        callback_list = getattr(self, trigger)
        callback_list.append(func)
