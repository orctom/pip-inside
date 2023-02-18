import os
import shutil
import signal
import sys
import venv
from pathlib import Path

import pexpect

from pip_inside import Aborted


def handle_shell():
    if os.name != "posix":
        raise Aborted(f"Sorry, only supports *nix, : {os.name}")

    created = _create_venv()
    _spaw_new_shell(created)


def _create_venv():
    if os.path.exists('.venv'):
        return False
    name = Path(os.getcwd()).name
    venv.create('.venv', with_pip=True, prompt=name)
    return True


def _spaw_new_shell(is_1st_time: bool):
    if os.environ.get('VIRTUAL_ENV') is not None:
        return
    def resize(*args, **kwargs) -> None:
        terminal = shutil.get_terminal_size()
        p.setwinsize(terminal.lines, terminal.columns)

    shell = os.environ.get("SHELL")
    terminal = shutil.get_terminal_size()
    p = pexpect.spawn(shell, ['-i'], dimensions=(terminal.lines, terminal.columns))
    if shell.endswith('/zsh'):
        p.setecho(False)
    p.sendline('source .venv/bin/activate')
    if is_1st_time:
        p.sendline('pip install -U pip')
    signal.signal(signal.SIGWINCH, resize)
    p.interact(escape_character=None)
    p.close()
    sys.exit(p.exitstatus)
