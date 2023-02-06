__version__ = '0.1.0'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
