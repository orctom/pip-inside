__version__ = '0.1.16'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
