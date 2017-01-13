import logging

from StaticMethod import listify

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from builtins import object

from Core import EventData
from Core.Condition import Condition


class Transition(object):
    __slots__ = 'source', 'dest', 'conditions', 'unless', 'before', 'after', 'prepare'

    def __init__(self, source: str, dest: str, conditions:(str or list) =None,
                 unless:(str or list) =None, before:(str or list) =None,
                 after:(str or list) =None, prepare:(str or list)=None):
        """
        Args:
            :param source     : The name of the source State.
            :param dest       : The name of the destination State.
            :param conditions : Condition(s) that must pass in order for
                                the transition to take place. Either a string providing the
                                name of a callable, or a list of callables. For the transition
                                to occur, ALL callables must return True.
            :param unless     : Condition(s) that must return False in order
                for the transition to occur. Behaves just like conditions arg
                otherwise.
            :param before     : callbacks to trigger before the
                transition.
            :param after      : callbacks to trigger after the transition.
            :param prepare    : callbacks to trigger before conditions are checked
        """
        self.source = source
        self.dest = dest
        self.prepare = [] if prepare is None else listify(prepare)
        self.before = [] if before is None else listify(before)
        self.after = [] if after is None else listify(after)

        self.conditions = []
        if conditions is not None:
            for c in listify(conditions):
                self.conditions.append(Condition(c))
        if unless is not None:
            for u in listify(unless):
                self.conditions.append(Condition(u, target=False))

    def execute(self, event_data: EventData):
        """ Execute the transition.
            :param event_data: An instance of class EventData.
            :returns    : boolean indicating whether or not the transition was
                          successfully executed (True if successful, False if not).
        """
        logger.debug("%sInitiating transition from state %s to state %s...",
                     event_data.machine.id, self.source, self.dest)
        machine = event_data.machine

        for func in self.prepare:
            machine._callback(func, event_data)
            logger.debug("Executed callback '%s' before conditions." % func)

        for c in self.conditions:
            if not c.check(event_data):
                logger.debug("%sTransition condition failed: %s() does not " +
                             "return %s. Transition halted.", event_data.machine.id, c.func, c.target)
                return False
        for func in self.before:
            machine._callback(func, event_data)
            logger.debug("%sExecuted callback '%s' before transition.", event_data.machine.id, func)

        self._change_state(event_data)

        for func in self.after:
            machine._callback(func, event_data)
            logger.debug("%sExecuted callback '%s' after transition.", event_data.machine.id, func)
        return True

    def _change_state(self, event_data: EventData):
        event_data.machine.get_state(self.source).exit(event_data)
        event_data.machine.set_state(self.dest, event_data.model)
        event_data.update(event_data.model)
        event_data.machine.get_state(self.dest).enter(event_data)

    def add_callback(self, trigger: str, func: str):
        """ Add a new before, after, or prepare callback.
            :param trigger: The type of triggering event. Must be one of'before', 'after' or 'prepare'.
            :param func   : The name of the callback function.
        """
        callback_list = getattr(self, trigger)
        callback_list.append(func)
