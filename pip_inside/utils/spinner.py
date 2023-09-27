import threading

import click


class Spinner(threading.Thread):

    CURSORS_0 = '▁▂▃▄▅▆▇█'
    CURSORS_1 = '⣾⣷⣯⣟⡿⢿⣻⣽'

    def __init__(self, msg: str, interval=0.25):
        super().__init__()
        click.secho(f"{msg}   ", nl=False, fg='bright_cyan')
        self.status = threading.Event()
        self.interval = interval
        self.daemon = True

    def stop(self):
        self.status.set()

    def is_stopped(self):
        return self.status.is_set()

    def cursors(self, chars):
        while True:
            for cursor in chars:
                yield cursor

    def run(self):
        i = 0
        c0, c1 = self.cursors(self.CURSORS_0), self.cursors(self.CURSORS_1)
        p = ' '
        while not self.is_stopped():
            self.status.wait(self.interval)
            i += 1
            if i % 8 == 0:
                p = f"{p}{next(c0)}" if p == self.CURSORS_0[-1] else f"{next(c0)}"
                click.secho(f"\b\b{p} ", nl=False, fg='bright_cyan')
            click.secho(f"\b{next(c1)}", nl=False, fg='bright_cyan')
        click.secho(' ', nl=True, fg='bright_cyan')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
