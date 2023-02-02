import subprocess
import sys
from typing import Optional

import click

from pip_inside.utils import pyproject, version_specifies


def handle_add(name: str, group: Optional[str]):
    if version_specifies.has_version_specifier(name):
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', name]
            subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
            pyproject.add_dependency(name, group)
            pyproject.flush()
        except subprocess.CalledProcessError:
            pass
    else:
        click.echo(f"search and select for {name}")


