__version__ = '0.2.2'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
