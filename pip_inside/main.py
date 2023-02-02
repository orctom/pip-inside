from typing import List

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from .commands.add import handle_add
from .commands.init import handle_init
from .commands.install import handle_install
from .commands.remove import handle_remove
from .utils import packages, pyproject

FIGLET = """
  _____  _____
 |_____]   |
 |       __|__   pip-inside

"""


@click.group()
def cli():
    try:
        pyproject.load()
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
def init():
    """Init project in current directory"""
    try:
        handle_init()
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('--group', default='main', help='dependency group')
@click.option('-i', 'interactive', is_flag=True, default=False, help="interactive mode")
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def add(name, group, interactive: bool, v: bool):
    """Add a package as project dependency"""
    try:
        click.secho(f"name: {name}, interactive: {interactive}")
        if interactive:
            if name is None:
                name = inquirer.text(message="package name:").execute()
            pkgs = packages.search(name)
            choices = [Choice(value=pkg.name, name=pkg.desc) for pkg in pkgs]
            name = inquirer.select(
                message="Select the package:",
                choices=choices,
                vi_mode=True,
                wrap_lines=True,
                mandatory=True,
            ).execute()

        handle_add(name, group)
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('--group', default='main', show_default=True, help='dependency group')
def remove(name, group):
    """Remove a package from project dependencies"""
    try:
        if name is None:
            name = inquirer.text(message="package name:").execute()
        handle_remove(name, group)
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
@click.option('--groups', multiple=True, default=['main'], show_default=True, help='dependency groups')
def install(groups: List[str]):
    """Install project dependencies by groups"""
    try:
        if len(groups) == 1:
            groups = groups[0].split(',')
        elif len(groups) == 0:
            groups = ['main']
        handle_install(groups)
    except Exception as e:
        click.secho(e, fg='red')


if __name__ == "__main__":
    click.secho(FIGLET, fg='green')
    cli()
