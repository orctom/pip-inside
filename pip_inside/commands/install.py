import itertools
import os
import shutil
import subprocess
import sys
from typing import List

import click
import tomlkit

from pip_inside.utils.pyproject import PyProject


def handle_install(groups: List[str]):
    _install_from_pi_lock(groups) or _install_from_pyproject_toml(groups)


def _install_from_pi_lock(groups: List[str]):
    if not os.path.exists('pi.lock'):
        return False
    try:
        with open('pi.lock', 'r') as f:
            data = tomlkit.load(f)

        deps = list(itertools.chain(*[data.get(group, []) for group in groups]))
        cmd = [shutil.which('python'), '-m', 'pip', 'install', *deps]
        subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
    except subprocess.CalledProcessError:
        pass


def _install_from_pyproject_toml(groups: List[str]):
    try:
        pyproject = PyProject.from_toml()
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
        cmd = [shutil.which('python'), '-m', 'pip', 'install', *dependencies]
        subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
    except subprocess.CalledProcessError:
        pass
