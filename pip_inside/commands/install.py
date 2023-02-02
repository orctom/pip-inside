import subprocess
import sys
from typing import List

import click

from pip_inside.utils import pyproject


def handle_install(groups: List[str]):
    try:
        dependencies = []
        for group in groups:
            deps = pyproject.get_dependencies(group)
            if deps is None:
                click.secho(f"Dependencies group: {group} not found in pyproject.toml", fg='yellow')
                continue
            dependencies.extend(deps)
        if len(dependencies) == 0:
            click.secho('Nothing to install, no dependencies specified in pyproject.toml')
            return
        cmd = [sys.executable, '-m', 'pip', 'install', *dependencies]
        subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
    except subprocess.CalledProcessError:
        pass
