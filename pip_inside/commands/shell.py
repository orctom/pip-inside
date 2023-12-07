import os
import shutil
import signal
import sys
import venv
from pathlib import Path

import pexpect

from pip_inside import Aborted
from pip_inside.utils.misc import P_KV_SEP


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
    _write_conda_activate_into_activate()
    return True


def _write_conda_activate_into_activate():
    """fix PS1 conda env name"""
    if (conda_env := _find_conda_env()) is None:
        return
    with open('.venv/bin/activate', 'a+') as f:
        f.seek(0)
        lines = f.readlines()
        lines.insert(0, f"conda activate {conda_env}\n")
        f.truncate(0)
        for line in lines:
            f.write(line)


def _spaw_new_shell(is_1st_time: bool):
    if os.environ.get('VIRTUAL_ENV') is not None:
        return
    def resize(*args, **kwargs) -> None:
        terminal = shutil.get_terminal_size()
        p.setwinsize(terminal.lines, terminal.columns)

    shell = os.environ.get("SHELL")
    terminal = shutil.get_terminal_size()
    p = pexpect.spawn(shell, ['-i'], dimensions=(terminal.lines, terminal.columns))
    if shell is None:
        p.sendline('. .venv/bin/activate')
    else:
        if shell.endswith('/zsh'):
            p.setecho(False)
        if (conda_env := _find_conda_env()) is not None:
            p.sendline(f"conda activate {conda_env}")
        p.sendline('source .venv/bin/activate')
    if is_1st_time:
        p.sendline('pip install -U pip')
    signal.signal(signal.SIGWINCH, resize)
    p.interact(escape_character=None)
    p.close()
    sys.exit(p.exitstatus)


def _find_conda_env():
    try:
        with open('.venv/pyvenv.cfg') as f:
            values = dict(P_KV_SEP.split(x.strip()) for x in f.readlines())
            home = values.get('home')
            if home is None or 'conda' not in home:
                return None
            return home[:-4] if home.endswith('/bin') else home
    except Exception:
        return None
