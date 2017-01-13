import os, sys, inspect
from pprint import pprint

from Extensions.Diagrams.GraphMachine import GraphMachine
cmd_folder = os.path.realpath(
    os.path.dirname(
        os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class Matter(object):
    def is_valid(self):
        return True

    def is_not_valid(self):
        return False

    def is_also_valid(self):
        return True

    def satisfaction(self, stream: str) -> bool:
        pass

    # graph object is created by the machine
    def show_graph(self, name: str):
        self.graph.draw('state' + name + '.png', prog='dot')

states=[str(0), str(1)]
transitions = [
    {'trigger': 'c, b', 'source': '0', 'dest': '0'},
    {'trigger': 'a', 'source': '1', 'dest': '0'},
    {'trigger': 'a', 'source': '0', 'dest': '1'}
]

model = Matter()
machine = GraphMachine(model=model,
                       states=states,
                       transitions=transitions,
                       auto_transitions=False,
                       initial='0',
                       title="transient",
                       show_conditions=True)

model.a()
model.a()