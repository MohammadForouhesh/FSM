from Core.Transition import Transition


class TransitionGraphSupport(Transition):

    def _change_state(self, event_data):
        machine = event_data.machine
        model = event_data.model
        dest = machine.get_state(self.dest)

        # Mark the previous node and path used
        if self.source is not None:
            source = machine.get_state(self.source)
            machine.set_node_state(model.graph, source.name,
                                   state='previous')

            if hasattr(source, 'children'):
                while len(source.children) > 0:
                    source = source.children[0]
                while len(dest.children) > 0:
                    dest = dest.children[0]
            if model.graph.has_edge(source.name, dest.name):
                machine.set_edge_state(model.graph, source.name,
                                       dest.name, state='previous')

        # Mark the active node
        machine.set_node_state(model.graph, dest.name,
                               state='active', reset=True)

        super(TransitionGraphSupport, self)._change_state(event_data)