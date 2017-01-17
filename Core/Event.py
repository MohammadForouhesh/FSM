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
        self.name = name
        self.machine = machine
        self.transitions = defaultdict(list)

    def add_transition(self, transition: Transition):
        self.transitions[transition.source].append(transition)

    def trigger(self, model, *args, **kwargs):
        f = partial(self._trigger, model, *args, **kwargs)
        return self.machine._process(f)

    def _trigger(self, model, *args, **kwargs) -> bool:
        state = self.machine.get_state(model.state)
        if state.name not in self.transitions:
            msg = "%sCan't trigger event %s from state %s!" % (self.machine.id, self.name,
                                                               state.name)
            if state.ignore_invalid_triggers:
                logger.warning(msg)
                return False
            else:
                raise Machine.MachineError(msg)
        event = EventData.EventData(state, self, self.machine, model)
        for t in self.transitions[state.name]:
            # event.transition = t
            event.kwargs = t
            if t.execute(event):
                return True
        return False

    def add_callback(self, trigger: str, func: str):
        for t in itertools.chain(*self.transitions.values()):
            t.add_callback(trigger, func)