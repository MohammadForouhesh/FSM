from Extensions.Diagrams.Diagram import Diagram
try:
    import pygraphviz as pgv
except:
    pgv = None


class Graph(Diagram):

    machine_attributes = {'directed': True,'strict': False,'rankdir': 'LR', 'ratio': '0.3'}

    style_attributes = {
        'node': {
            'default': {'shape': 'circle','height': '1.2','style': 'filled','fillcolor': 'white','color': 'black',},
            'active': {'color': 'red','fillcolor': 'darksalmon','shape': 'doublecircle'},
            'previous': {'color': 'blue','fillcolor': 'azure2',}},
        'edge': {
            'default': {'color': 'black',},
            'previous': {'color': 'blue',}
        }
    }

    def __init__(self, *args, **kwargs):
        self.seen = []
        super(Graph, self).__init__(*args, **kwargs)

    def _add_nodes(self, states, container):
        # to be able to process children recursively as well as the state dict of a machine
        states = states.values() if isinstance(states, dict) else states
        for state in states:
            if state.name in self.seen:
                continue
            elif hasattr(state, 'children') and len(state.children) > 0:
                self.seen.append(state.name)
                sub = container.add_subgraph(name="cluster_" + state.name,\
                                             label=state.name, rank='same', color='black')
                self._add_nodes(state.children, sub)
            else:
                shape = self.style_attributes['node']['default']['shape']
                self.seen.append(state.name)
                container.add_node(n=state.name, shape=shape)

    def _add_edges(self, events, container):
        for event in events.values():
            label = str(event.name)

            for transitions in event.transitions.items():
                src = self.machine.get_state(transitions[0])
                ltail = ''
                if hasattr(src, 'children') and len(src.children) > 0:
                    ltail = 'cluster_' + src.name
                    src = src.children[0]
                    while len(src.children) > 0:
                        src = src.children[0]

                for t in transitions[1]:
                    dst = self.machine.get_state(t.dest)
                    edge_label = self._transition_label(label, t)
                    lhead = ''

                    if hasattr(dst, 'children') and len(dst.children) > 0:
                        lhead = 'cluster_' + dst.name
                        dst = dst.children[0]
                        while len(dst.children) > 0:
                            dst = dst.children[0]

                    # special case in which parent to first child edge is resolved to a self reference.
                    # will be omitted for now. I have not found a solution for how to fix this yet since having
                    # cluster to node edges is a bit messy with dot.
                    if dst.name == src.name and transitions[0] != t.dest:
                        continue
                    elif container.has_edge(src.name, dst.name):
                        edge = container.get_edge(src.name, dst.name)
                        edge.attr['label'] = edge.attr['label'] + ' | ' + edge_label
                    else:
                        container.add_edge(src.name, dst.name, label=edge_label, ltail=ltail, lhead=lhead)

    def rep(self, f):
        return f.__name__ if callable(f) else f

    def _transition_label(self, edge_label, tran):
        if self.machine.show_conditions and tran.conditions:
            return '{edge_label} [{conditions}]'.format(
                edge_label=edge_label,
                conditions=' & '.join(
                    self.rep(c.func) if c.target else '!' + self.rep(c.func)
                    for c in tran.conditions
                ),
            )
        return edge_label

    def get_graph(self, title=None):
        """ Generate a DOT graph with pygraphviz, returns an AGraph object
        Args:
            title (string): Optional title for the graph.
        """
        if not pgv:
            raise Exception('AGraph diagram requires pygraphviz')

        if title is False:
            title = ''

        fsm_graph = pgv.AGraph(label=title, compound=True, **self.machine_attributes)
        fsm_graph.node_attr.update(self.style_attributes['node']['default'])

        # For each state, draw a circle
        self._add_nodes(self.machine.states, fsm_graph)

        self._add_edges(self.machine.events, fsm_graph)

        setattr(fsm_graph, 'style_attributes', self.style_attributes)

        return fsm_graph

