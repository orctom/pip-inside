from importlib.util import module_from_spec, spec_from_file_location

import click

from pip_inside.utils.pyproject import PyProject


def handle_version(short: bool = False):
    pyproject = PyProject.from_toml()
    module = pyproject.get('project.name')
    s = spec_from_file_location(module, f"{module}/__init__.py")
    m = module_from_spec(s)
    s.loader.exec_module(m)
    version = m.__version__ if short else f"{module}: {m.__version__}"
    click.secho(version, fg='cyan')
