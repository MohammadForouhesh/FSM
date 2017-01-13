

class FunctionWrapper(object):
    def __init__(self, func, path):
        if len(path) > 0:
            self.add(func, path)
            self._func = None
        else:
            self._func = func

    def add(self, func, path):
        if len(path) > 0:
            name = path[0]
            if name[0].isdigit():
                name = 's' + name
            if hasattr(self, name):
                getattr(self, name).add(func, path[1:])
            else:
                x = FunctionWrapper(func, path[1:])
                setattr(self, name, x)
        else:
            self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)