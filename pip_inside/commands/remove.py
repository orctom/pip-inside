import subprocess
import sys

import click

from pip_inside.utils import pyproject


def handle_remove(name, group):
    try:
        if pyproject.remove_dependency(name, group):
            pyproject.flush()
            cmd = [sys.executable, '-m', 'pip', 'uninstall', name, '-y']
            subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
        else:
            click.secho(f"package: [{name}] not found in group: [{group}]", fg='yellow')
    except subprocess.CalledProcessError:
        pass


