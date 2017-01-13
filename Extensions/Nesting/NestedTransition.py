from Core.Transition import Transition

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NestedTransition(Transition):

    def execute(self, event_data):
        dest_state = event_data.machine.get_state(self.dest)
        while dest_state.initial:
            dest_state = event_data.machine.get_state(dest_state.initial)
        self.dest = dest_state.name
        return super(NestedTransition, self).execute(event_data)

    # The actual state change method 'execute' in Transition was restructured to allow overriding
    def _change_state(self, event_data):
        machine = event_data.machine
        model = event_data.model
        dest_state = machine.get_state(self.dest)
        source_state = machine.get_state(model.state)
        lvl = source_state.exit_nested(event_data, dest_state)
        event_data.machine.set_state(self.dest, model)
        event_data.update(model)
        dest_state.enter_nested(event_data, lvl)
