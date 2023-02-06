from typing import List

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from . import Aborted, __version__
from .commands.add import handle_add
from .commands.build import handle_build
from .commands.init import handle_init
from .commands.install import handle_install
from .commands.publish import handle_publish
from .commands.remove import handle_remove
from .commands.version import handle_version
from .utils import packages, spinner, version_specifies


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

        prompt = "Add a package (leave blank to exit):"
        while True:
            name = inquirer.text(message=prompt).execute()
            if not name:
                return

            with spinner.Spinner(f"Searching for {name}"):
                pkgs = packages.search(name)
            name = inquirer.select(
                message="Select the package:",
                choices=[Choice(value=pkg.name, name=pkg.desc) for pkg in pkgs],
                vi_mode=True,
                wrap_lines=True,
                mandatory=True,
            ).execute()

            with spinner.Spinner(f"Fetching version list for {name}"):
                versions = packages.versions(name)
            if versions:
                version = inquirer.fuzzy(
                    message="Select the version:",
                    choices=['[set manually]'] + versions[:15],
                    vi_mode=True,
                    wrap_lines=True,
                    mandatory=True,
                ).execute()
                if version == '[set manually]':
                    version = inquirer.text(message="Version:", completer={v: None for v in versions[:15]}).execute().strip()
            else:
                click.secho('Failed to fetch version list, please set version menually', fg='cyan')
                version = inquirer.text(message="Version:").execute().strip()
            if version:
                name = f"{name}{version}" if version_specifies.has_ver_spec(version) else f"{name}=={version}"
            handle_add(name, group)
            prompt = "Add another package (leave blank to exit):"
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
