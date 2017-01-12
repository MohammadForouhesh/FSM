
class Transition:
    __slots__ = 'source', 'dest', 'conditions', 'unless', 'before', 'after', 'prepare'

    def __init__(self, source: str, dest: str, conditions:(str or list)=None, unless:(str or list) =None, before:(str or list) =None,
                 after:(str or list) =None, prepare:(str or list)=None):
        """
        Args:
            :param source     : The name of the source State.
            :param dest       : The name of the destination State.
            :param conditions : Condition(s) that must pass in order for
                                the transition to take place. Either a string providing the
                                name of a callable, or a list of callables. For the transition
                                to occur, ALL callables must return True.
            :param unless     : Condition(s) that must return False in order
                for the transition to occur. Behaves just like conditions arg
                otherwise.
            :param before     : callbacks to trigger before the
                transition.
            :param after      : callbacks to trigger after the transition.
            :param prepare    : callbacks to trigger before conditions are checked
        """
        self.source = source
        self.dest = dest
        self.conditions = conditions
        self.unless = unless
        self.prepare = [] if prepare is None else listify(prepare)
        self.before = [] if before is None else listify(before)
        self.after = [] if after is None else listify(after)