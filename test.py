import os, sys, inspect

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

    # graph object is created by the machine
    def show_graph(self, name: str):
        self.graph.draw('state' + name + '.png', prog='dot')

states=['0', '1']
transitions = [
    {'trigger': 'b', 'source': '0', 'dest': '0'},
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

model.b()
model.a()

for s in 'aabaabaaabb':
    p = callstr2(s)
    model.p()

