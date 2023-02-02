import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from .commands.add import handle_add
from .commands.init import handle_init
from .commands.remove import handle_remove
from .utils import packages, pyproject


@click.group()
def cli():
    try:
        pyproject.load()
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
def init():
    """create pyproject.toml in current directory"""
    try:
        handle_init()
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('--group', default='main')
@click.option('-i', 'interactive', is_flag=True, default=False, help="interactive")
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def add(name, group, interactive: bool, v: bool):
    """add package as dependency"""
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
@click.option('--group', default='main')
def remove(name, group):
    """remove a dependency"""
    try:
        if name is None:
            name = inquirer.text(message="package name:").execute()
        handle_remove(name, group)
    except Exception as e:
        click.secho(e, fg='red')


if __name__ == "__main__":
    cli()
