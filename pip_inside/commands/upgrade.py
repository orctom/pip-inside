import shutil
import subprocess
import sys
from pathlib import Path

from .version import handle_version


def handle_upgrade():
    try:
        cmd = [(Path(shutil.which('pip-inside')).parent / 'python').as_posix(), '-m', 'pip', 'install', '-U', 'pip', 'pip-inside']
        subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
        handle_version()
    except subprocess.CalledProcessError:
        sys.exit(1)
