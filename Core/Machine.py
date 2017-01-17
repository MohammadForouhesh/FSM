from collections import OrderedDict
from collections import deque
from functools import partial
from six import string_types
from builtins import object

import inspect
import logging

from Core import EventData
from Core import State
from Core import Event
from Core import Transition
from StaticMethod import listify, get_trigger

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Machine(object):
    __slots__ = 'models', 'states', '_initial', 'send_event', 'auto_transitions','ignore_invalid_triggers',\
                'before_state_change', 'after_state_change', 'name', '_queued', '_transition_queue', '_initial',\
                'events', 'id',
                
    # Callback naming parameters
    callbacks = ['before', 'after', 'prepare', 'on_enter', 'on_exit']
    separator = '_'

    def __init__(self, model: object=None, states: State=None, initial:str=None, transitions: list=None,
                 send_event: bool=False, auto_transitions: bool=True,
                 ordered_transitions: bool=False, ignore_invalid_triggers: bool=None,
                 before_state_change: callable=None, after_state_change: callable=None, name: str=None,
                 queued: bool=False, add_self: bool=True, **kwargs: dict):

        try:
            super(Machine, self).__init__(**kwargs)
        except TypeError as e:
            raise MachineError('Passing arguments {0} caused an inheritance error: {1}'.format(kwargs.keys(), e))

        self.states = OrderedDict()
        self.events = {}
        self.send_event = send_event
        self.auto_transitions = auto_transitions
        self.ignore_invalid_triggers = ignore_invalid_triggers
        self.before_state_change = before_state_change
        self.after_state_change = after_state_change
        self.id = name + ": " if name is not None else ""
        self._queued = queued
        self._transition_queue = deque()
        self.models = []

        if model is None and add_self:
            model = self

        if model and initial is None:
            initial = 'initial'
            self.add_states(initial)
        self._initial = initial

        if states is not None:
            self.add_states(states)

        if transitions is not None:
            transitions = listify(transitions)
            for t in transitions:
                if isinstance(t, list):
                    self.add_transition(*t)
                else:
                    self.add_transition(**t)

        if ordered_transitions:
            self.add_ordered_transitions()

        if model:
            self.add_model(model)

    def add_model(self, model, initial=None):
        """ Register a model with the state machine, initializing triggers and callbacks. """
        models = listify(model)

        if initial is None:
            if self._initial is None:
                raise MachineError("No initial state configured for machine, must specify when adding model.")
            else:
                initial = self._initial

        for model in models:
            if model not in self.models:

                if hasattr(model, 'trigger'):
                    logger.warning("%sModel already contains an attribute 'trigger'. Skip method binding ",self.id)
                else:
                    model.trigger = partial(get_trigger, model)

                for trigger, _ in self.events.items():
                    self._add_trigger_to_model(trigger, model)

                for _, state in self.states.items():
                    self._add_model_to_state(state, model)

                self.set_state(initial, model=model)
                self.models.append(model)

    def remove_model(self, model):
        models = listify(model)

        for model in models:
            self.models.remove(model)

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

    @property
    def model(self):
        if len(self.models) == 1:
            return self.models[0]
        else:
            return self.models

    def is_state(self, state, model):
        """ Check whether the current state matches the named state. """
        return model.state == state

    def get_state(self, state):
        """ Return the State instance with the passed name. """
        if state not in self.states:
            raise ValueError("State '%s' is not a registered state." % state)
        return self.states[state]

    def set_state(self, state, model=None):
        """ Set the current state. """
        if isinstance(state, string_types):
            state = self.get_state(state)
        models = self.models if model is None else listify(model)
        for m in models:
            m.state = state.name

    def add_state(self, *args, **kwargs):
        """ Alias for add_states. """
        self.add_states(*args, **kwargs)

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
            for model in self.models:
                self._add_model_to_state(state, model)
        if self.auto_transitions:
            for s in self.states.keys():
                self.add_transition('to_%s' % s, '*', s)

    def _add_model_to_state(self, state, model):
        setattr(model, 'is_%s' % state.name,
                partial(self.is_state, state.name, model))
        enter_callback = 'on_enter_' + state.name
        if hasattr(model, enter_callback) and \
                inspect.ismethod(getattr(model, enter_callback)):
            state.add_callback('enter', enter_callback)
        exit_callback = 'on_exit_' + state.name
        if hasattr(model, exit_callback) and \
                inspect.ismethod(getattr(model, exit_callback)):
            state.add_callback('exit', exit_callback)

    def _add_trigger_to_model(self, trigger, model):
        trig_func = partial(self.events[trigger].trigger, model)
        setattr(model, trigger, trig_func)

    def get_triggers(self, *args):
        states = set(args)
        return [t for (t, ev) in self.events.items() if any(state in ev.transitions for state in states)]

    def add_transition(self, trigger: str, source: str, dest: str, conditions:(str or list)=None,
                       before:(str or list)=None, after:(str or list)=None,
                       prepare:(str or list)=None, **kwargs: dict):

        if trigger not in self.events:
            self.events[trigger] = self._create_event(trigger, self)
            for model in self.models:
                self._add_trigger_to_model(trigger, model)

        if isinstance(source, string_types):
            source = list(self.states.keys()) if source == '*' else [source]
        else:
            source = [s.name if self._has_state(s) else s for s in listify(source)]

        for s in source:
            if self._has_state(dest):
                dest = dest.name
            t = self._create_transition(s, dest, conditions, **kwargs)
            self.events[trigger].add_transition(t)

    def add_ordered_transitions(self, states: list=None, trigger: str='next_state',
                                loop: bool=True, loop_includes_initial: bool=True):

        if states is None:
            states = list(self.states.keys())
        if len(states) < 2:
            raise MachineError("with fewer than 2 states.")
        for i in range(1, len(states)):
            self.add_transition(trigger, states[i - 1], states[i])
        if loop:
            if not loop_includes_initial:
                states.remove(self._initial)
            self.add_transition(trigger, states[-1], states[0])

    def _callback(self, func: callable, event_data: EventData):
        if isinstance(func, string_types):
            func = getattr(event_data.model, func)

        if self.send_event:
            func(event_data)
        else:
            func(*event_data.args, **event_data.kwargs)

    def _has_state(self, s):
        if isinstance(s, State.State):
            if s in self.states.values():
                return True
            else:
                raise ValueError('State %s has not been added to the machine' % s.name)
        else:
            return False

    def _process(self, trigger):

        # default processing
        if not self.has_queue:
            if not self._transition_queue:
                return trigger()
            else:
                raise MachineError("Attempt to process events synchronously while transition queue is not empty!")

        self._transition_queue.append(trigger)
        if len(self._transition_queue) > 1:
            return True

        while self._transition_queue:
            try:
                self._transition_queue[0]()
                self._transition_queue.popleft()
            except Exception:
                self._transition_queue.clear()
                raise
        return True

    @classmethod
    def _identify_callback(cls, name):
        try:
            callback_type = cls.callbacks[[name.find(x) for x in cls.callbacks].index(0)]
        except ValueError:
            return None, None

        target = name[len(callback_type) + len(cls.separator):]

        if target == '' or name[len(callback_type)] != cls.separator:
            return None, None

        return callback_type, target

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError("{} does not exist".format(name))

        callback_type, target = self._identify_callback(name)

        if callback_type is not None:
            if callback_type in ['before', 'after', 'prepare']:
                if target not in self.events:
                    raise MachineError('Event "%s" is not registered.' % target)
                return partial(self.events[target].add_callback, callback_type)

            elif callback_type in ['on_enter', 'on_exit']:
                state = self.get_state(target)
                return partial(state.add_callback, callback_type[3:])

        raise AttributeError("{} does not exist".format(name))


class MachineError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
