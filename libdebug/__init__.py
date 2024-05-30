try:
    from rich.traceback import install
except ImportError:
    pass
else:
    install()

__all__ = ["debugger", "libcontext"]
