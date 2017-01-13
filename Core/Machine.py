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
    __slots__ = 'models', 'states', '_initial', 'send_event','ignore_invalid_triggers',\
                'name', '_queued', '_transition_queue', '_initial',\
                'events', 'id',
                
    # Callback naming parameters
    callbacks = ['before', 'after', 'prepare', 'on_enter', 'on_exit']
    separator = '_'

    def __init__(self, model: object, states: State=None, initial:str=None, transitions: list=None,
                 send_event: bool=False, ignore_invalid_triggers: bool=None, name: str=None,
                 queued: bool=False):
        """
            :param model                  : The object(s) whose states we want to manage. If None,
                                            the current Machine instance will be used the model (i.e., all
                                            triggering events will be attached to the Machine itself).
            :param states                 : A list of valid states. Each element can be either a
                                            string or a State instance. If string, a new generic State
                                            instance will be created that has the same name as the string.
            :param initial                : The initial state of the Machine.
            :param transitions            : An optional list of transitions. Each element
                                            is a dictionary of named arguments to be passed onto the
                                            Transition initializer.
            :param send_event             : When True, any arguments passed to trigger
                                            methods will be wrapped in an EventData object, allowing
                                            indirect and encapsulated access to data. When False, all
                                            positional and keyword arguments will be passed directly to all
                                            callback methods.
            :param ignore_invalid_triggers: when True, any calls to trigger methods
                                            that are not valid for the present state (e.g., calling an
                                            a_to_b() trigger when the current state is c) will be silently
                                            ignored rather than raising an invalid transition exception.
            :param name                   : If a name is set, it will be used as a prefix for logger output
            :param queued                 : When True, processes transitions sequentially. A trigger
                                            executed in a state callback function will be queued and executed 
                                            later. Due to the nature of the queued processing, all transitions will
                                            _always_ return True since conditional checks cannot be conducted at 
                                            queueing time.
        """

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
        self.models = []

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
        """ Add new state(s).
            :param states                   : a list, a State instance, the
                                              name of a new state, or a dict with keywords to pass on to the
                                              State initializer. If a list, each element can be of any of the
                                              latter three types.
            :param on_enter                 : callbacks to trigger when the state is
                                              entered. Only valid if first argument is string.
            :param on_exit                  : callbacks to trigger when the state is
                                              exited. Only valid if first argument is string.
            :param ignore_invalid_triggers  : when True, any calls to trigger methods
                                              that are not valid for the present state (e.g., calling an
                                              a_to_b() trigger when the current state is c) will be silently
                                              ignored rather than raising an invalid transition exception.
                                              Note that this argument takes precedence over the same
                                              argument defined at the Machine level, and is in turn
                                              overridden by any ignore_invalid_triggers explicitly
                                              passed in an individual state's initialization arguments.
        """

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
        # Add automatic transitions after all states have been created

    def _add_model_to_state(self, state, model):
        setattr(model, 'is_%s' % state.name,
                partial(self.is_state, state.name, model))
        #  Add enter/exit callbacks if there are existing bound methods
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

    def add_transition(self, trigger: str, source: str, dest: str, conditions:(str or list)=None):
        """ Create a new Transition instance and add it to the internal list.

            :param trigger    : The name of the method that will trigger the
                                transition. This will be attached to the currently specified
                                model (e.g., passing trigger='advance' will create a new
                                advance() method in the model that triggers the transition.)
            :param source     : The name of the source state--i.e., the state we
                                are transitioning away from.
            :param dest       : The name of the destination State--i.e., the state
                                we are transitioning into.
            :param conditions : Condition(s) that must pass in order
                                for the transition to take place. Either a list providing the
                                name of a callable, or a list of callables. For the transition
                                to occur, ALL callables must return True.
        """
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
            t = self._create_transition(s, dest, conditions)
            self.events[trigger].add_transition(t)

    def _callback(self, func: callable, event_data: EventData):
        """ Trigger a callback function, possibly wrapping it in an EventData instance.
            func        : The callback function.
            event_data  : An EventData instance to pass to the
                          callback (if event sending is enabled) or to extract arguments
                          from (if event sending is disabled).
        """
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
                # if trigger raises an Error, it has to be handled by the Machine.process caller
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

    @classmethod
    def _identify_callback(cls, name):
        try:
            callback_type = cls.callbacks[[name.find(x) for x in cls.callbacks].index(0)]
        except ValueError:
            return None, None

        # Extract the target by cutting the string after the type and separator
        target = name[len(callback_type) + len(cls.separator):]

        # Make sure there is actually a target to avoid index error and enforce _ as a separator
        if target == '' or name[len(callback_type)] != cls.separator:
            return None, None

        return callback_type, target

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError("{} does not exist".format(name))

        # Could be a callback
        callback_type, target = self._identify_callback(name)

        if callback_type is not None:
            if callback_type in ['before', 'after', 'prepare']:
                if target not in self.events:
                    raise MachineError('Event "%s" is not registered.' % target)
                return partial(self.events[target].add_callback, callback_type)

            elif callback_type in ['on_enter', 'on_exit']:
                state = self.get_state(target)
                return partial(state.add_callback, callback_type[3:])

        # Nothing matched
        raise AttributeError("{} does not exist".format(name))


class MachineError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
