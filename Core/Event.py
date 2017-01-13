from collections import defaultdict
from functools import partial

import itertools
import logging

from Core import Machine
from Core import Transition
from Core import EventData

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Event(object):
    __slots__ = 'name', 'machine', 'transitions'

    def __init__(self, name: str, machine: Machine):
        """
            :param name    : The name of the event, which is also the name of the
                      triggering callable (e.g., 'advance' implies an advance()
                      method).
            :param machine : The current Machine instance.
        """
        self.name = name
        self.machine = machine
        self.transitions = defaultdict(list)

    def add_transition(self, transition: Transition):
        """ Add a transition to the list of potential transitions.
            :param transition : The Transition instance to add to the
                                list.
        """
        self.transitions[transition.source].append(transition)

    def trigger(self, *args, **kwargs):
        f = partial(self._trigger, self.machine, *args, **kwargs)
        return self.machine._process(f)

    def _trigger(self, *args, **kwargs) -> bool:
        """ Serially execute all transitions that match the current state,
            halting as soon as one successfully completes.
        
            args and kwargs: Optional positional or named arguments that will
                             be passed onto the EventData object, enabling arbitrary state
                             information to be passed on to downstream triggered functions.
            returns        : boolean indicating whether or not a transition was
                             successfully executed (True if successful, False if not).
        """
        state = self.machine.current_state
        if state.name not in self.transitions:
            msg = "%sCan't trigger event %s from state %s!" % (self.machine.id, self.name, state.name)
            if state.ignore_invalid_triggers:
                logger.warning(msg)
                return False
            else:
                raise Machine.MachineError(msg)
        event = EventData.EventData(state, self, self.machine, self.machine, args=args, kwargs=kwargs)
        for t in self.transitions[state.name]:
            # event.transition = t
            event.kwargs = t
            if t.execute(event):
                return True
        return False

    def add_callback(self, trigger: str, func: str):
        """ Add a new before or after callback to all available transitions.
        
            trigger  : The type of triggering event. Must be one of
                       'before', 'after' or 'prepare'.
            func     : The name of the callback function.
        """
        for t in itertools.chain(*self.transitions.values()):
            t.add_callback(trigger, func)