import abc


class Diagram(object, metaclass=abc.ABCMeta):

    def __init__(self, machine):
        self.machine = machine

    @abc.abstractmethod
    def get_graph(self):
        raise Exception('Abstract base Diagram.get_graph called!')
