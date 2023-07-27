import shutil
from typing import List

import click
from InquirerPy import inquirer

from . import Aborted, __version__


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
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def init(v: bool):
    """Init project in current directory"""
    try:
        from .commands.init import handle_init
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
@click.option('-G', '--group', default='main', help='dependency group')
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def add(name, group, v: bool):
    """Add a package as project dependency"""
    try:
        from .commands.add import handle_add
        from .utils.packages import prompt_a_package
        click.secho(f"[python] {shutil.which('python')}", fg='cyan')
        if name:
            handle_add(name, group)
        else:
            name = prompt_a_package()
            while name is not None:
                handle_add(name, group)
                name = prompt_a_package(True)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.argument('name', required=False, type=str)
@click.option('-G', '--group', default='main', show_default=True, help='dependency group')
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def remove(name, group, v: bool):
    """Remove a package from project dependencies"""
    try:
        from .commands.remove import handle_remove
        click.secho(f"[python] {shutil.which('python')}", fg='cyan')
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
@click.option('-G', '--groups', multiple=True, default=['main'], show_default=True, help='dependency groups')
@click.option('-A', '--all', is_flag=True, default=False, help="all groups")
@click.option('-q', 'q', is_flag=True, default=False, help="quiet")
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def install(groups: List[str], all: bool, q: bool, v: bool):
    """Install project dependencies by groups"""
    try:
        from .commands.install import handle_install
        click.secho(f"[python] {shutil.which('python')}", fg='cyan')
        if len(groups) == 1:
            groups = groups[0].split(',')
        elif len(groups) == 0:
            groups = ['main']
        if all:
            groups = ['_all_']
        handle_install(groups, quiet=q)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('--dist', default='dist', show_default=True, help='build target directory')
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def build(dist: str, v: bool):
    """Build the wheel and sdist"""
    try:
        from .commands.build import handle_build
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
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def publish(repository: str, dist: str, interactive: bool, v: bool):
    """Publish the wheel and sdist to remote repository"""
    try:
        from .commands.publish import handle_publish
        handle_publish(repository, dist=dist, interactive=interactive)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def shell(v: bool):
    """Ensure '.venv' virtualenv, and new shell into it"""
    try:
        from .commands.shell import handle_shell
        handle_shell()
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('--unused', is_flag=True, default=False, help="only show unused dependencies")
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def show(unused: bool, v: bool):
    """Show dependency tree"""
    try:
        from .commands.show import handle_show
        click.secho(f"[python] {shutil.which('python')}", fg='cyan')
        handle_show(unused)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
def lock(v: bool):
    """Create or update version lock file 'pi.lock'"""
    try:
        from .commands.lock import handle_lock
        click.secho(f"[python] {shutil.which('python')}", fg='cyan')
        handle_lock()
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


@cli.command()
@click.option('-s', '--short', is_flag=True, default=False, help="show short version")
@click.option('-v', 'v', is_flag=True, default=False, help="verbose")
@click.argument('version', required=False)
def version(short: bool, v: bool, version: str):
    """Show version of current project"""
    try:
        from .commands.version import handle_update_version, handle_version
        if version is None:
            handle_version(short)
        else:
            handle_update_version(version)
    except Aborted as e:
        click.secho(e, fg='yellow')
    except Exception as e:
        click.secho(e, fg='red')
        if v:
            import traceback
            click.secho(traceback.format_exc(), fg='red')


if __name__ == "__main__":
    cli()
