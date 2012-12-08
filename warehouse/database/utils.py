def table_args(args):
    def wrapper(cls):
        targs = args
        bases = cls.__mro__[1:]

        for base in bases:
            if hasattr(base, "__table_args__"):
                targs = targs + base.__table_args__

        return targs
    return wrapper
