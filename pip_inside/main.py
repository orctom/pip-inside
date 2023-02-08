from typing import List

import click
from InquirerPy import inquirer

from . import Aborted, __version__
from .commands.add import handle_add
from .commands.build import handle_build
from .commands.init import handle_init
from .commands.install import handle_install
from .commands.list import handle_list
from .commands.publish import handle_publish
from .commands.remove import handle_remove
from .commands.version import handle_version
from .utils import packages, version_specifies


@click.group(invoke_without_command=True)
@click.option('-V', '--version', is_flag=True, default=False, help="show version of this tool")
@click.pass_context
def cli(ctx, version: bool):
    if ctx.invoked_subcommand:
        return
    if version:
        click.secho(f"pip-inside: {__version__}")
    else:
        click.secho(ctx.get_help())


@cli.command()
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def init(v: bool):
    """Init project in current directory"""
    try:
        handle_init()
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('--group', default='main', help='dependency group')
@click.option('-i', 'interactive', is_flag=True, default=False, help="interactive mode")
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def add(name, group, interactive: bool, v: bool):
    """Add a package as project dependency"""
    try:
        if name:
            if interactive and version_specifies.ver_has_spec(name) :
                interactive = False
                click.secho('Off interactive mode, found version specifier in package name', fg='yellow')
        else:
            interactive = True

        if not interactive:
            handle_add(name, group)
            return

        name = packages.prompt_a_package()
        while name is not None:
            handle_add(name, group)
            name = packages.prompt_a_package(True)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('--group', default='main', show_default=True, help='dependency group')
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def remove(name, group, v: bool):
    """Remove a package from project dependencies"""
    try:
        if name is None:
            name = inquirer.text(message="package name:").execute()
        handle_remove(name, group)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('--groups', multiple=True, default=['main'], show_default=True, help='dependency groups')
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def install(groups: List[str], v: bool):
    """Install project dependencies by groups"""
    try:
        if len(groups) == 1:
            groups = groups[0].split(',')
        elif len(groups) == 0:
            groups = ['main']
        handle_install(groups)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('--dist', default='dist', show_default=True, help='build target directory')
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def build(dist: str, v: bool):
    """Build the wheel and sdist"""
    try:
        handle_build(dist)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('-r', '--repository', default='pypi', show_default=True, help='target repository')
@click.option('--dist', default='dist', show_default=True, help='build target directory')
@click.option('-i', 'interactive', is_flag=True, default=False, help="interactive mode")
@click.option('-v', 'v', is_flag=True, default=False, help="verbovse")
def publish(repository: str, dist: str, interactive: bool, v: bool):
    """Publish the wheel and sdist to remote repository"""
    try:
        handle_publish(repository, dist=dist, interactive=interactive)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('--unused', is_flag=True, default=False, help="only show unused dependencies")
def list(unused: bool):
    """Show dependency tree"""
    try:
        handle_list(unused)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')


@cli.command()
@click.option('-s', '--short', is_flag=True, default=False, help="show short version")
def version(short: bool):
    """Show version of current project"""
    try:
        handle_version(short)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')


if __name__ == "__main__":
    cli()
