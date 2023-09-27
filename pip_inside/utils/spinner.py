import threading

import click


class Spinner(threading.Thread):

    def __init__(self, msg: str, interval=0.25):
        super().__init__()
        click.secho(f"{msg}  ", nl=False, fg='bright_cyan')
        self.status = threading.Event()
        self.interval = interval
        self.daemon = True

    def stop(self):
        self.status.set()

    def is_stopped(self):
        return self.status.is_set()

    def cursors(self):
        while True:
            for cursor in '|/-\\':
                yield cursor

    def run(self):
        i = 0
        cursor = self.cursors()
        while not self.is_stopped():
            self.status.wait(self.interval)
            i += 1
            if i % 40 == 0:
                click.secho('\b..', nl=False, fg='bright_cyan')
            click.secho(f"\b{next(cursor)}", nl=False, fg='bright_cyan')
        click.secho('\b.', nl=True, fg='bright_cyan')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
