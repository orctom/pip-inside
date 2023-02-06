import subprocess
import sys
from typing import Optional

import click

from pip_inside.utils.pyproject import PyProject


def handle_add(name: str, group: Optional[str]):
    try:
        pyproject = PyProject.from_toml()
        name_installed = pyproject.find_dependency(name, group)
        if name_installed:
            if name_installed == name:
                click.secho("Skip, already installed")
            else:
                pyproject.remove_dependency(name_installed, group)
        cmd = [sys.executable, '-m', 'pip', 'install', name]
        subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
        pyproject.add_dependency(name, group)
        pyproject.flush()
    except subprocess.CalledProcessError:
        pass
