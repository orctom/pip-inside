import os
import shlex
import shutil
import subprocess
import sys
from typing import Optional

import click
from InquirerPy import inquirer

from pip_inside.utils.markers import Requirement
from pip_inside.utils.pyproject import PyProject

from . import P_SEP


def handle_add(names: str, group: Optional[str]):
    try:
        if os.environ.get('VIRTUAL_ENV') is None:
            proceed = inquirer.confirm(message='Not in virutal env, sure to proceed?', default=False).execute()
            if not proceed:
                return
        pyproject = PyProject.from_toml()
        names = P_SEP.split(names)
        requires = []
        for name in names:
            require = Requirement(name)
            if not pyproject.add_dependency(require, group):
                click.secho("Skip, already installed as main dependency")
                continue
            requires.append(require)

        cmd = shlex.split(f"{shutil.which('python')} -m pip install {' '.join([str(r) for r in requires])}")
        if subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout).returncode == 1:
            sys.exit(1)
        pyproject.flush()
    except subprocess.CalledProcessError:
        sys.exit(1)
