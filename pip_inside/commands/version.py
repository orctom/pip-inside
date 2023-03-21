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
