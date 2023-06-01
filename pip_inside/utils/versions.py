import re

P = re.compile(r'__version__\s*=\s*[\'\"]([a-z0-9.-]+)[\'\"]')


def get_version_from_init(filepath: str, silent: bool = False):
    text = open(filepath).read()
    m = P.search(text)
    if m is None:
        if silent:
            return None
        else:
            raise ValueError(f"'__version__' not defined in '{filepath}'")
    return m.groups()[0]
