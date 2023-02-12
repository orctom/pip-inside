import os
import shutil
import signal
import sys
import venv
from pathlib import Path

import click
import pexpect

from pip_inside import Aborted


def handle_shell():
    if os.name != "posix":
        raise Aborted(f"Sorry, only supports *nix, : {os.name}")

    _create_venv()
    _spaw_new_shell()


def _create_venv():
    if os.path.exists('.venv'):
        return
    name = Path(os.getcwd()).name
    venv.create('.venv', with_pip=True, prompt=name)


def _spaw_new_shell():
    def resize(*args, **kwargs) -> None:
        terminal = shutil.get_terminal_size()
        p.setwinsize(terminal.lines, terminal.columns)

    shell = os.environ.get("SHELL")
    terminal = shutil.get_terminal_size()
    p = pexpect.spawn(shell, ['-i'], dimensions=(terminal.lines, terminal.columns))
    if shell.endswith('/zsh'):
        p.setecho(False)
    p.sendline('source .venv/bin/activate')
    signal.signal(signal.SIGWINCH, resize)
    p.interact(escape_character=None)
    p.close()
    sys.exit(p.exitstatus)
