import threading

import click


class Spinner(threading.Thread):

    def __init__(self, msg: str, interval=0.25):
        super().__init__()
        click.secho(f"{msg} ", nl=False, fg='bright_cyan')
        self.status = threading.Event()
        self.interval = interval
        self.daemon = True

    def stop(self):
        self.status.set()

    def is_stopped(self):
        return self.status.isSet()

    def run(self):
        while not self.is_stopped():
            click.secho('.', nl=False, fg='bright_cyan')
            self.status.wait(self.interval)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        click.secho('\b', fg='bright_cyan')
