
def listify(obj):
    if obj is None:
        return []
    else:
        return obj if isinstance(obj, (list, tuple, type(None)))else [obj]


def get_trigger(model, trigger_name, *args, **kwargs):
    func = getattr(model, trigger_name, None)
    if func:
        return func(*args, **kwargs)
    raise AttributeError("Model has no trigger named %s" % trigger_name)
