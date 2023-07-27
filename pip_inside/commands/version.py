import os

import click

from pip_inside.utils import misc, versions
from pip_inside.utils.pyproject import PyProject


def handle_version(short: bool = False):
    pyproject = PyProject.from_toml()
    module = pyproject.get('project.name')
    filepath = f"{misc.norm_module(module)}/__init__.py"
    ver = versions.get_version_from_init(filepath)
    version = ver if short else f"{module}: {ver}"
    click.secho(version, fg='bright_cyan')


def handle_update_version(version: str):
    if not version:
        return

    pyproject = PyProject.from_toml()
    module = pyproject.get('project.name')
    module_name = misc.norm_module(module)
    filepath = f"{module_name}/__init__.py"
    os.makedirs(module_name, exist_ok=True)
    msg = versions.set_version_in_init(filepath, version)
    click.secho(msg, fg='bright_cyan')
