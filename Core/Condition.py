
from six import string_types
from builtins import object

from Core import EventData


class Condition(object):
    """
        This class should not be initialized or called from outside a
        Transition instance, and exists at module level.      
    """
    __slots__ = 'func', 'target'

    def __init__(self, func: str, target: bool=True):
            self.func = func
            self.target = target

    def check(self, event_data: EventData):
        predicate = getattr(event_data.model, self.func) if isinstance(self.func, string_types) else self.func

        if event_data.machine.send_event:
            return predicate(event_data) == self.target
        else:
            return predicate() == self.target
