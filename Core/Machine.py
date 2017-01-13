from collections import OrderedDict
from collections import deque
from six import string_types
from builtins import object

import inspect
import logging

from Core import State
from Core import Event
from Core import Transition
from StaticMethod import listify, get_trigger

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Machine(object):
    __slots__ = 'models', 'states', '_initial', 'current_state', 'send_event','ignore_invalid_triggers',\
                'name', '_queued', '_transition_queue', '_initial',\
                'events', 'id',

    def __init__(self, states: list, initial: str, transitions: list,
                 send_event: bool=False, ignore_invalid_triggers: bool=None, name: str=None,
                 queued: bool=False):

        try:
            super(Machine, self).__init__()
        except TypeError as e:
            raise MachineError("")

        self.states = OrderedDict()
        self.events = {}
        self.send_event = send_event
        self.ignore_invalid_triggers = ignore_invalid_triggers
        self.id = name + ": " if name is not None else ""
        self._queued = queued
        self._transition_queue = deque()
        self._initial = initial
        self.add_states(states)

        self.current_state = self.states.get(self._initial)

        if transitions is not None:
            transitions = listify(transitions)
            for t in transitions:
                if isinstance(t, list):
                    self.add_transition(*t)
                else:
                    self.add_transition(**t)

    @staticmethod
    def _create_transition(*args, **kwargs):
        return Transition.Transition(*args, **kwargs)

    @staticmethod
    def _create_event(*args, **kwargs):
        return Event.Event(*args, **kwargs)

    @property
    def initial(self):
        """ Return the initial state. """
        return self._initial

    @property
    def has_queue(self):
        """ Return boolean indicating if machine has queue or not """
        return self._queued

    def is_state(self, state):
        """ Check whether the current state matches the named state. """
        return state in self.states

    def get_state(self, state):
        """ Return the State instance with the passed name. """
        if state not in self.states:
            raise ValueError("State '%s' is not a registered state." % state.name)
        return self.states[state]

    def set_state(self, state):
        """ Set the current state. """
        if isinstance(state, string_types):
            state = self.get_state(state)

    def add_states(self, states: (list or str or dict or State), on_enter: (str or list)=None,
                   on_exit: (str or list)=None, ignore_invalid_triggers: bool=None):
        ignore = ignore_invalid_triggers
        if ignore is None:
            ignore = self.ignore_invalid_triggers

        states = listify(states)
        for state in states:
            if isinstance(state, string_types):
                state = State.State(state, on_enter=on_enter, on_exit=on_exit, ignore_invalid_triggers=ignore)
            elif isinstance(state, dict):
                if 'ignore_invalid_triggers' not in state:
                    state['ignore_invalid_triggers'] = ignore
                state = State.State(**state)
            self.states[state.name] = state

    def get_triggers(self, *args):
        states = set(args)
        return [t for (t, ev) in self.events.items() if any(state in ev.transitions for state in states)]

    def add_transition(self, trigger: str, source: str, dest: str, conditions:(str or list)=None):
        if trigger not in self.events:
            self.events[trigger] = self._create_event(trigger, self)

        if isinstance(source, string_types):
            source = list(self.states.keys()) if source == '*' else [source]
        else:
            source = [s.name if self._has_state(s) else s for s in listify(source)]
        for s in source:
            if self._has_state(dest):
                dest = dest.name
            t = self._create_transition(s, dest, conditions)
            self.events[trigger].add_transition(t)

    def _has_state(self, s):
        if isinstance(s, State.State):
            if s in self.states.values():
                return True
            else:
                raise ValueError('State %s has not been added to the machine' % s.name)
        else:
            return False

    def _process(self, next_state: State,  trigger: callable):

        # default processing
        if not self.has_queue:
            if not self._transition_queue:
                # if trigger raises an Error, it has to be handled by the Machine.process caller
                self.current_state = next_state
                return trigger()
            else:
                raise MachineError("transition queue is not empty!")

        # process queued events
        self._transition_queue.append(trigger)
        # another entry in the queue implies a running transition; skip immediate execution
        if len(self._transition_queue) > 1:
            return True

        # execute as long as transition queue is not empty
        while self._transition_queue:
            try:
                self._transition_queue[0]()
                self._transition_queue.popleft()
            except Exception:
                # if a transition raises an exception, clear queue and delegate exception handling
                self._transition_queue.clear()
                raise
        return True
        # 3123123
# 123123


class MachineError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
