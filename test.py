import os, sys, inspect
from pprint import pprint

from IPython.core.display import display, Image

from Extensions.Diagrams.GraphMachine import GraphMachine
cmd_folder = os.path.realpath(
    os.path.dirname(
        os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


states=['00', '01', '10', '11']
transitions = [
    {'trigger': 'darja', 'source': '00', 'dest': '00'},
    {'trigger': 'add_one', 'source': '00', 'dest': '01'},
    {'trigger': 'add_two', 'source': '00', 'dest': '10'},
    {'trigger': 'darja', 'source': '01', 'dest': '01'},
    {'trigger': 'add_one', 'source': '01', 'dest': '10'},
    {'trigger': 'add_two', 'source': '01', 'dest': '11'},
    {'trigger': 'darja', 'source': '10', 'dest': '10'},
    {'trigger': 'add_one', 'source': '10', 'dest': '11'},
    {'trigger': 'add_two', 'source': '10', 'dest': '00'},
    {'trigger': 'darja', 'source': '11', 'dest': '11'},
    {'trigger': 'add_one', 'source': '11', 'dest': '00'},
    {'trigger': 'add_two', 'source': '11', 'dest': '01'}
]

machine = GraphMachine(states=states,
                       transitions=transitions,
                       initial='00',
                       title="transient",
                       show_conditions=True)

machine.graph.draw('state.png', prog='dot')
display(Image('state.png'))

print(machine.events)

print(machine.darja())

print(machine.is_state('00'))
