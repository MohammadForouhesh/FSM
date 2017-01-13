
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
            """
            :param func  : Name of the condition-checking callable
            :param target: Indicates the target state--i.e., when True,
                           the condition-checking callback should return True to pass,
                           and when False, the callback should return False to pass.
            """
            self.func = func
            self.target = target

    def check(self, event_data: EventData):
        """ Check whether the condition passes.
            :param event_data: An EventData instance to pass to the
                               condition (if event sending is enabled) or to extract arguments
                               from (if event sending is disabled). Also contains the data
                               model attached to the current machine which is used to invoke
                               the condition.
            :return: Method :)
        """
        predicate = getattr(event_data.model, self.func) if isinstance(self.func, string_types) else self.func

        if event_data.machine.send_event:
            return predicate(event_data) == self.target
        else:
            return predicate() == self.target
