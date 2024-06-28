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
            if subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout).returncode == 1:
                sys.exit(1)
    except subprocess.CalledProcessError:
        sys.exit(1)
