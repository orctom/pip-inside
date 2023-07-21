import os
import shutil
import subprocess
import sys

import click
from InquirerPy import inquirer
from pkg_resources import Requirement

from pip_inside.utils.dependencies import Dependencies
from pip_inside.utils.pyproject import PyProject


def handle_remove(name: str, group):
    if os.environ.get('VIRTUAL_ENV') is None:
        proceed = inquirer.confirm(message='Not in virutal env, sure to proceed?', default=False).execute()
        if not proceed:
            return
    try:
        pyproject = PyProject.from_toml()
        require = Requirement(name)
        if pyproject.remove_dependency(require, group):
            pyproject.flush()
            deps = Dependencies().get_unused_dependencies_for(require)
            cmd = [shutil.which('python'), '-m', 'pip', 'uninstall', require.key, *deps, '-y']
            subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
        else:
            click.secho(f"Package: [{require.key}] not found in group: [{group}]", fg='yellow')
    except subprocess.CalledProcessError:
        sys.exit(1)
