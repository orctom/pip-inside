import shutil
import subprocess
import sys
from pathlib import Path


def handle_upgrade():
    try:
        for cmd in [
            [shutil.which('python'), '-m', 'pip', 'install', '-U', 'pip'],
            [(Path(shutil.which('pip-inside')).parent / 'python').as_posix(), '-m', 'pip', 'install', '-U', 'pip', 'pip-inside'],
        ]:
            subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout)
    except subprocess.CalledProcessError:
        sys.exit(1)
