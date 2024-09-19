__version__ = '0.2.7'

class Aborted(RuntimeError):
    """When command should abort the process, by design"""
