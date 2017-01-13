from Core.EventData import EventData
from Core.Machine import Machine
from Extensions.Nesting.FuctionWrapper import FunctionWrapper
from Extensions.Nesting.NestedEvent import NestedEvent
from Extensions.Nesting.NestedTransition import NestedTransition
from Extensions.Nesting.NestingState import NestedState
from StaticMethod import listify


from six import string_types
import copy
from functools import partial

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class HierarchicalMachine(Machine):

    def __init__(self, *args, **kwargs):
        self._buffered_transitions = []
        super(HierarchicalMachine, self).__init__(*args, **kwargs)

    def add_model(self, model):
        super(HierarchicalMachine, self).add_model(model)
        models = listify(model)
        for m in models:
            if hasattr(m, 'to'):
                logger.warn("%sModel already has a 'to'-method. It will NOT be overwritten by NestedMachine", self.id)
            else:
                to_func = partial(self.to, m)
                setattr(m, 'to', to_func)

    # Instead of creating transitions directly, Machine now use a factory method which can be overridden
    @staticmethod
    def _create_transition(*args, **kwargs):
        return NestedTransition(*args, **kwargs)

    @staticmethod
    def _create_event(*args, **kwargs):
        return NestedEvent(*args, **kwargs)

    @staticmethod
    def _create_state(*args, **kwargs):
        return NestedState(*args, **kwargs)

    def is_state(self, state_name, model, allow_substates=False):
        if not allow_substates:
            return model.state == state_name

        temp_state = self.get_state(model.state)
        while not temp_state.name == state_name and temp_state.level > 0:
            temp_state = temp_state.parent

        return temp_state.name == state_name

    def traverse(self, states, on_enter=None, on_exit=None,
                 ignore_invalid_triggers=None, parent=None, remap={}):
        states = listify(states)
        new_states = []
        ignore = ignore_invalid_triggers
        if ignore is None:
            ignore = self.ignore_invalid_triggers
        for state in states:
            tmp_states = []
            # other state representations are handled almost like in the base class but a parent parameter is added
            if isinstance(state, string_types):
                if state in remap:
                    continue
                tmp_states.append(self._create_state(state, on_enter=on_enter, on_exit=on_exit, parent=parent,
                                  ignore_invalid_triggers=ignore))
            elif isinstance(state, dict):
                if state['name'] in remap:
                    continue
                state = copy.deepcopy(state)
                if 'ignore_invalid_triggers' not in state:
                    state['ignore_invalid_triggers'] = ignore
                state['parent'] = parent

                if 'children' in state:
                    # Concat the state names with the current scope. The scope is the concatenation of all
                    # previous parents. Call traverse again to check for more nested states.
                    p = self._create_state(state['name'], on_enter=on_enter, on_exit=on_exit,
                                           ignore_invalid_triggers=ignore, parent=parent,
                                           initial=state.get('initial', None))
                    nested = self.traverse(state['children'], on_enter=on_enter, on_exit=on_exit,
                                           ignore_invalid_triggers=ignore,
                                           parent=p, remap=state.get('remap', {}))
                    tmp_states.append(p)
                    tmp_states.extend(nested)
                else:
                    tmp_states.insert(0, self._create_state(**state))
            elif isinstance(state, HierarchicalMachine):
                # copy only states not mentioned in remap
                copied_states = [s for s in state.states.values() if s.name not in remap]
                # inner_states are the root states of the passed machine
                # which have be attached to the parent
                inner_states = [s for s in copied_states if s.level == 0]
                for s in inner_states:
                    s.parent = parent
                tmp_states.extend(copied_states)
                for trigger, event in state.events.items():
                    if trigger.startswith('to_'):
                        path = trigger[3:].split(NestedState.separator)
                        # do not copy auto_transitions since they would not be valid anymore;
                        # trigger and destination do not exist in the new environment
                        if path[0] in remap:
                            continue
                        ppath = parent.name.split(NestedState.separator)
                        path = ['to_' + ppath[0]] + ppath[1:] + path
                        trigger = '.'.join(path)
                    # adjust all transition start and end points to new state names
                    for transitions in event.transitions.values():
                        for transition in transitions:
                            src = transition.source
                            # transitions from remapped states will be filtered to prevent
                            # unexpected behaviour in the parent machine
                            if src in remap:
                                continue
                            dst = parent.name + NestedState.separator + transition.dest\
                                if transition.dest not in remap else remap[transition.dest]
                            conditions = []
                            unless = []
                            for c in transition.conditions:
                                conditions.append(c.func) if c.target else unless.append(c.func)
                            self._buffered_transitions.append({'trigger': trigger,
                                                               'source': parent.name + NestedState.separator + src,
                                                               'dest': dst,
                                                               'conditions': conditions,
                                                               'unless': unless,
                                                               'prepare': transition.prepare,
                                                               'before': transition.before,
                                                               'after': transition.after})

            elif isinstance(state, NestedState):
                tmp_states.append(state)
            else:
                raise ValueError("%s cannot be added to the machine since its type is not known." % state)
            new_states.extend(tmp_states)

        duplicate_check = []
        for s in new_states:
            if s.name in duplicate_check:
                state_names = [s.name for s in new_states]
                raise ValueError("State %s cannot be added since it is already in state list %s." % (s.name, state_names))
            else:
                duplicate_check.append(s.name)
        return new_states

    def add_states(self, states, *args, **kwargs):
        # preprocess states to flatten the configuration and resolve nesting
        new_states = self.traverse(states, *args, **kwargs)
        super(HierarchicalMachine, self).add_states(new_states, *args, **kwargs)

        # for t in self._buffered_transitions:
        #     print(t['trigger'])
        while len(self._buffered_transitions) > 0:
            args = self._buffered_transitions.pop()
            self.add_transition(**args)

    def get_triggers(self, *args):
        # add parents to state set
        states = []
        for state in args:
            s = self.get_state(state)
            while s.parent:
                states.append(s.parent.name)
                s = s.parent
        states.extend(args)
        return super(HierarchicalMachine, self).get_triggers(*states)

    def add_transition(self, trigger, source, dest, conditions=None,
                       unless=None, before=None, after=None, prepare=None, **kwargs):
        if isinstance(source, string_types):
            source = [x.name for x in self.states.values()] if source == '*' else [source]

        # FunctionWrappers are only necessary if a custom separator is used
        if trigger not in self.events:
            self.events[trigger] = self._create_event(trigger, self)
            for model in self.models:
                self._add_trigger_to_model(trigger, model)
        super(HierarchicalMachine, self).add_transition(trigger, source, dest, conditions=conditions, unless=unless,
                                                        prepare=prepare, before=before, after=after, **kwargs)

    def _add_trigger_to_model(self, trigger, model):
        if trigger.startswith('to_') and NestedState.separator != '_':
            path = trigger[3:].split(NestedState.separator)
            print(path)
            trig_func = partial(self.events[trigger].trigger, model)
            if hasattr(model, 'to_' + path[0]):
                t = getattr(model, 'to_' + path[0])
                t.add(trig_func, path[1:])
            else:
                t = FunctionWrapper(trig_func, path[1:])
                setattr(model, 'to_' + path[0], t)
        else:
            super(HierarchicalMachine, self)._add_trigger_to_model(trigger, model)

    def on_enter(self, state_name, callback):
        self.get_state(state_name).add_callback('enter', callback)

    def on_exit(self, state_name, callback):
        self.get_state(state_name).add_callback('exit', callback)

    def to(self, model, state_name, *args, **kwargs):
        event = EventData(self.get_state(model.state), None, self,
                          model, args=args, kwargs=kwargs)
        self._create_transition(model.state, state_name).execute(event)