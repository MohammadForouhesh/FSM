from Core.Event import Event
from Core.EventData import EventData
from Core.Machine import MachineError

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class NestedEvent(Event):

    def _trigger(self, model, *args, **kwargs):
        tmp = self.machine.get_state(model.state)
        while tmp.parent and tmp.name not in self.transitions:
            tmp = tmp.parent
        if tmp.name not in self.transitions:
            msg = "%sCan't trigger event %s from state %s!" % (self.machine.id, self.name,
                                                               model.state)
            if self.machine.get_state(model.state).ignore_invalid_triggers:
                logger.warning(msg)
            else:
                raise MachineError(msg)
        event = EventData(self.machine.get_state(model.state), self, self.machine,
                          model, args=args, kwargs=kwargs)
        for t in self.transitions[tmp.name]:
            event.transition = t
            if t.execute(event):
                return True
        return False

