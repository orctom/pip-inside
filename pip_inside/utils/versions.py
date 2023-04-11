import contextlib
import os
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location

P = re.compile(r'__version__\s*=\s*[\'\"]([a-z0-9.-]+)[\'\"]')


def get_version_from_init(filepath: str, silent: bool = False):
    try:
        module_name = f"pi_inside.version.import.{os.path.dirname(filepath)}".replace('/', '.')
        s = spec_from_file_location(module_name, filepath)
        m = module_from_spec(s)
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull):
                sys.modules[module_name] = m
                try:
                    s.loader.exec_module(m)
                finally:
                    sys.modules.pop(module_name, None)
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
