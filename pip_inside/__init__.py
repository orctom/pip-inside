__version__ = '0.2.6'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
