from builtins import object

from Core import Event
from Core import Machine
from Core import State


class EventData(object):
    __slots__ = 'state', 'event', 'machine', 'model', 'args', 'kwargs'

    def __init__(self, state: State, event: Event, machine: Machine, model: object, args: list, kwargs: dict):
        """
            :param state   : The State from which the Event was triggered.
            :param event   : The triggering Event.
            :param machine : The current Machine instance.
            :param model   : The model/object the machine is bound to.
            :param args    : Optional positional arguments from trigger method
                             to store internally for possible later use.
            :param kwargs  : Optional keyword arguments from trigger method
                             to store internally for possible later use.
        """
        self.state = state
        self.event = event
        self.machine = machine
        self.model = model          # bug
        self.args = args
        self.kwargs = kwargs

    def update(self, model):
        """ Updates the current State to accurately reflect the Machine. """
        self.state = self.machine.get_state(model.state)

