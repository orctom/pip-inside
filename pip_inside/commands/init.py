import click
from InquirerPy import inquirer


def handle_init():
    click.echo('init')
    name = inquirer.text(message="Project name:", mandatory=True).execute()
