import logging
from functools import partial

from Core.Diagrams.TransitionGraphSupport import TransitionGraphSupport

from Core.Diagrams.Graph import Graph
from Core.Machine import Machine

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GraphMachine(Machine):
    _pickle_blacklist = ['graph']

    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k not in self._pickle_blacklist}

    def __setstate__(self, state):
        self.__dict__.update(state)
        for model in self.models:
            graph = self._get_graph(model, title=self.title)
            self.set_node_style(graph, model.state, 'active')

    def __init__(self, *args, **kwargs):
        # remove graph config from keywords
        self.title = kwargs.pop('title', 'State Machine')
        self.show_conditions = kwargs.pop('show_conditions', False)
        super(GraphMachine, self).__init__(*args, **kwargs)

        # Create graph at beginning
        for model in self.models:
            if hasattr(model, 'get_graph'):
                raise AttributeError('Model already has a get_graph attribute.')
            setattr(model, 'get_graph', partial(self._get_graph, model))
            model.get_graph()
            self.set_node_state(model.graph, self.initial, 'active')
        # if model is not the machine
        if not hasattr(self, 'get_graph'):
            setattr(self, 'get_graph', self.get_combined_graph)

    def _get_graph(self, model, title=None, force_new=False):
        if title is None:
            title = self.title
        if not hasattr(model, 'graph') or force_new:
            model.graph = Graph(self).get_graph(title)
        return model.graph

    def get_combined_graph(self, title=None, force_new=False):
        logger.info('Returning graph of the first model. In future releases, this ' +
                    'method will return a combined graph of all models.')
        return self._get_graph(next(iter(self.models)), title, force_new)

    def set_edge_state(self, graph, edge_from, edge_to, state='default'):
        """ Mark a node as active by changing the attributes """
        edge = graph.get_edge(edge_from, edge_to)

        # Reset all the edges
        for e in graph.edges_iter():
            self.set_edge_style(graph, e, 'default')
        self.set_edge_style(graph, edge, state)

    def add_states(self, *args, **kwargs):
        super(GraphMachine, self).add_states(*args, **kwargs)
        for model in self.models:
            if hasattr(model, 'graph'):
                model.get_graph(force_new=True)

    def add_transition(self, *args, **kwargs):
        super(GraphMachine, self).add_transition(*args, **kwargs)
        for model in self.models:
            if hasattr(model, 'graph'):
                model.get_graph(force_new=True)

    def set_node_state(self, graph, node_name, state='default', reset=False):
        if reset:
            for n in graph.nodes_iter():
                self.set_node_style(graph, n, 'default')
        if graph.has_node(node_name):
            node = graph.get_node(node_name)
            func = self.set_node_style
        func(graph, node, state)

    @staticmethod
    def set_node_style(graph, node_name, style='default'):
        node = graph.get_node(node_name)
        style_attr = graph.style_attributes.get('node', {}).get(style)
        node.attr.update(style_attr)

    @staticmethod
    def set_edge_style(graph, edge, style='default'):
        style_attr = graph.style_attributes.get('edge', {}).get(style)
        edge.attr.update(style_attr)

    @staticmethod
    def set_graph_style(graph, item, style='default'):
        style_attr = graph.style_attributes.get('node', {}).get(style)
        item.graph_attr.update(style_attr)

    @staticmethod
    def _create_transition(*args, **kwargs):
        return TransitionGraphSupport(*args, **kwargs)
