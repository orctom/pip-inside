__version__ = '0.1.8'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
