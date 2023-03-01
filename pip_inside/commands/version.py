import re
from importlib.util import module_from_spec, spec_from_file_location

import click

from pip_inside.utils import misc
from pip_inside.utils.pyproject import PyProject


def handle_version(short: bool = False):
    pyproject = PyProject.from_toml()
    module = pyproject.get('project.name')
    filepath = f"{misc.norm_module(module)}/__init__.py"
    try:
        s = spec_from_file_location('hello', filepath)
        m = module_from_spec(s)
        s.loader.exec_module(m)
        ver = m.__version__
    except ModuleNotFoundError:  # incase running `pi` outside project's venv
        text = open(filepath).read()
        p = re.compile(r'__version__\s*=\s*[\'\"]([a-z0-9.-]+)[\'\"]')
        m = p.search(text)
        if m is None:
            raise ValueError("'__version__' not defined in 'pyproject.toml'")
        ver = m.groups()[0]
    version = ver if short else f"{module}: {ver}"
    click.secho(version, fg='bright_cyan')
