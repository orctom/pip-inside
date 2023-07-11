import os
import shutil
import subprocess
import sys
from typing import Optional

import click
from InquirerPy import inquirer
from pkg_resources import Requirement

from pip_inside.utils.pyproject import PyProject


def handle_add(name: str, group: Optional[str]):
    try:
        if os.environ.get('VIRTUAL_ENV') is None:
            proceed = inquirer.confirm(message='Not in virutal env, sure to proceed?', default=False).execute()
            if not proceed:
                return
        pyproject = PyProject.from_toml()
        require = Requirement(name)
        if not pyproject.add_dependency(require, group):
            click.secho("Skip, already installed as main dependency")
            return

        cmd = [shutil.which('python'), '-m', 'pip', 'install', str(require)]
        if subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout).returncode == 0:
            pyproject.flush()
    except subprocess.CalledProcessError:
        sys.exit(1)
