
import logging

from Core.State import State

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# Added parent and children parameter children is a list of NestedStates
# and parent is the full name of the parent e.g. Foo_Bar_Baz.
class NestedState(State):
    separator = '_'

    def __init__(self, name, on_enter=None, on_exit=None, ignore_invalid_triggers=None, parent=None, initial=None):
        self._name = name
        self._initial = initial
        self._parent = None
        self.parent = parent
        super(NestedState, self).__init__(name=name, on_enter=on_enter, on_exit=on_exit,
                                          ignore_invalid_triggers=ignore_invalid_triggers)
        self.children = []

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        if value is not None:
            self._parent = value
            self._parent.children.append(self)

    @property
    def initial(self):
        return self.name + NestedState.separator + self._initial if self._initial else None

    @property
    def level(self):
        return self.parent.level + 1 if self.parent is not None else 0

    @property
    def name(self):
        return (self.parent.name + NestedState.separator + self._name) if self.parent else self._name

    @name.setter
    def name(self, value):
        self._name = value

    def exit_nested(self, event_data, target_state):
        if self.level > target_state.level:
            self.exit(event_data)
            return self.parent.exit_nested(event_data, target_state)
        elif self.level <= target_state.level:
            tmp_state = target_state
            while self.level != tmp_state.level:
                tmp_state = tmp_state.parent
            tmp_self = self
            while tmp_self.level > 0 and tmp_state.parent.name != tmp_self.parent.name:
                tmp_self.exit(event_data)
                tmp_self = tmp_self.parent
                tmp_state = tmp_state.parent
            if tmp_self != tmp_state:
                tmp_self.exit(event_data)
                return tmp_self.level
            else:
                return tmp_self.level + 1

    def enter_nested(self, event_data, level=None):
        if level is not None and level <= self.level:
            if level != self.level:
                self.parent.enter_nested(event_data, level)
            self.enter(event_data)

