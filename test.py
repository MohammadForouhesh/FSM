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


states=['000', '001', '010', '011', '100', '101', '110', '111']
transitions = [
    {'trigger': 'add_zero', 'source': '000', 'dest': '100'},
    {'trigger': 'add_one', 'source': '000', 'dest': '001'},
    {'trigger': 'add_zero', 'source': '001', 'dest': '101'},
    {'trigger': 'add_one', 'source': '001', 'dest': '010'},
    {'trigger': 'add_zero', 'source': '010', 'dest': '110'},
    {'trigger': 'add_one', 'source': '010', 'dest': '011'},
    {'trigger': 'add_zero', 'source': '011', 'dest': '111'},
    {'trigger': 'add_one', 'source': '011', 'dest': '000'},
    {'trigger': 'add_zero', 'source': '100', 'dest': '000'},
    {'trigger': 'add_one', 'source': '100', 'dest': '101'},
    {'trigger': 'add_zero', 'source': '101', 'dest': '001'},
    {'trigger': 'add_one', 'source': '101', 'dest': '110'},
    {'trigger': 'add_zero', 'source': '110', 'dest': '010'},
    {'trigger': 'add_one', 'source': '110', 'dest': '111'},
    {'trigger': 'add_zero', 'source': '111', 'dest': '011'},
    {'trigger': 'add_one', 'source': '111', 'dest': '100'},
]

model = Matter()
machine = GraphMachine(model=model,
                       states=states,
                       transitions=transitions,
                       initial='000',
                       title="transient",
                       show_conditions=True)

print(machine.is_state('000', model=model))