__version__ = '0.2.10'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
