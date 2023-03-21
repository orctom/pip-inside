import re
from importlib.util import module_from_spec, spec_from_file_location

P = re.compile(r'__version__\s*=\s*[\'\"]([a-z0-9.-]+)[\'\"]')


def get_version_from_init(filepath: str, silent: bool = False):
    try:
        s = spec_from_file_location('hello', filepath)
        m = module_from_spec(s)
        s.loader.exec_module(m)
        return m.__version__
    except ModuleNotFoundError:  # incase running `pi` outside project's venv
        text = open(filepath).read()
        m = P.search(text)
        if m is None:
            if silent:
                return None
            else:
                raise ValueError("'__version__' not defined in 'pyproject.toml'")
        return m.groups()[0]
