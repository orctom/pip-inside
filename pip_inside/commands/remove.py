import os
import shutil
import subprocess
import sys

import click
from InquirerPy import inquirer

from pip_inside.utils.dependencies import Dependencies
from pip_inside.utils.markers import Requirement
from pip_inside.utils.pyproject import PyProject

from . import P_SEP


def handle_remove(names: str, group):
    if os.environ.get('VIRTUAL_ENV') is None:
        proceed = inquirer.confirm(message='Not in virutal env, sure to proceed?', default=False).execute()
        if not proceed:
            return
    try:
        pyproject = PyProject.from_toml()
        names = P_SEP.split(names)
        removes = []
        for name in names:
            require = Requirement(name)
            if pyproject.remove_dependency(require, group):
                removes.append(require.key)
                removes.extend(Dependencies().get_unused_dependencies_for(require))
            else:
                click.secho(f"Package: [{require.key}] not found in group: [{group}]", fg='yellow')
        if len(removes) > 0:
            pyproject.flush()
            cmd = [shutil.which('python'), '-m', 'pip', 'uninstall', ' '.join(removes), '-y']
            if subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout).returncode == 1:
                sys.exit(1)
    except subprocess.CalledProcessError:
        sys.exit(1)
