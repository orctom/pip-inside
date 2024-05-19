import threading
import time
from typing import List, Optional

import click


class Spinner(threading.Thread):

    LINE_CLEAR = '\x1b[2K'
    FRAMES = [
        '_________________',
        '\\________________',
        '|\\_______________',
        '_|\\______________',
        '__|\\_____________',
        '___|\\____________',
        '____|\\___________',
        '_____|\\__________',
        '______|\\_________',
        '_______|\\________',
        '________|\\_______',
        '_________|\\______',
        '__________|\\_____',
        '___________|\\____',
        '____________|\\___',
        '_____________|\\__',
        '______________|\\_',
        '_______________|\\',
        '________________|',
        '_________________',
        '_________________',
        '________________/',
        '_______________/|',
        '______________/|_',
        '_____________/|__',
        '____________/|___',
        '___________/|____',
        '__________/|_____',
        '_________/|______',
        '________/|_______',
        '_______/|________',
        '______/|_________',
        '_____/|__________',
        '____/|___________',
        '___/|____________',
        '__/|_____________',
        '_/|______________',
        '/|_______________',
        '|________________',
        '_________________',
    ]

    def __init__(self, msg: str, *, ps='>', done: str = '️ ', interval=0.1, frames: Optional[List[str]] = None):
        super().__init__()
        self.msg = msg
        self.status = threading.Event()
        self.ps = ps
        self.done = done
        self.interval = interval
        self.frames = frames or self.FRAMES
        self.daemon = True

    def stop(self):
        self.status.set()

    def is_stopped(self):
        return self.status.is_set()

    def cursors(self):
        while True:
            for cursor in self.frames:
                yield cursor

    def write(self, text):
        click.secho(f"{self.LINE_CLEAR}\r{self.ps} {text}", nl=True, fg='bright_cyan')

    def run(self):
        start = time.time()
        cursors = self.cursors()
        while not self.is_stopped():
            self.status.wait(self.interval)
            took = pretty_time_delta(time.time() - start)
            p = f"{self.LINE_CLEAR}\r{self.ps} {self.msg} [{took}] {next(cursors)}"
            click.secho(p, nl=False, fg='cyan')
        click.secho(self.done, nl=True, fg='cyan')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        time.sleep(0.1)


def pretty_time_delta(seconds):
    if seconds is None:
        return '-'
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    seconds, _ = divmod(seconds, 1)
    if days > 0:
        return f'{int(days)}d, {int(hours)}h, {int(minutes)}m, {int(seconds)}s'
    elif hours > 0:
        return f'{int(hours)}h, {int(minutes)}m, {int(seconds)}s'
    elif minutes > 0:
        return f'{int(minutes)}m, {int(seconds)}s'
    return f'{int(seconds)}s'
