from builtins import object

from Core import Event
from Core import Machine
from Core import State


class EventData(object):
    __slots__ = 'state', 'event', 'machine', 'model', 'args', 'kwargs'

    def __init__(self, state: State, event: Event, machine: Machine, model: object):
        self.state = state
        self.event = event
        self.machine = machine
        self.model = model

    def update(self, model):
        """ Updates the current State to accurately reflect the Machine. """
        self.state = self.machine.get_state(model.state)

