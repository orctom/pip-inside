import subprocess
import sys

import click

from pip_inside.utils.pyproject import PyProject


def handle_remove(name, group):
    try:
        pyproject = PyProject.from_toml()
        if pyproject.remove_dependency(name, group):
            pyproject.flush()
            cmd = [sys.executable, '-m', 'pip', 'uninstall', name, '-y']
            subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
        else:
            click.secho(f"Package: [{name}] not found in group: [{group}]", fg='yellow')
    except subprocess.CalledProcessError:
        pass


