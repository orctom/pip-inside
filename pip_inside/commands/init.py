import os
import pathlib
import subprocess
import sys
from datetime import date
from types import SimpleNamespace

import click
import tomlkit
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from pip_inside import Aborted
from pip_inside.utils import packages, spinner, version_specifies
from pip_inside.utils.licenses import LICENSES


def handle_init():
    click.echo(f"Initializing project in {os.getcwd()}")
    check_pyproject_toml()
    meta = collect_metadata()
    toml = build_toml(meta)

    click.secho(tomlkit.dumps(toml), fg='blue')
    proceed = inquirer.confirm(message="Proceed?", default=True).execute()
    if not proceed:
        return

    write_toml(toml)
    write_readme(meta)
    write_license(meta)
    write_root_module_with_version(meta)


def check_pyproject_toml():
    if not os.path.exists('pyproject.toml'):
        return

    try:
        with open('pyproject.toml', 'r') as f:
            data = tomlkit.load(f)
        if 'build-system' in data:
            raise Aborted(f"Skip, 'pyproject.toml' file with 'build-system' already exists")
    except Exception as e:
        raise Aborted(f"Skip, 'pyproject.toml' already exists, and failed to load: {e}")


def collect_metadata():
    defaults = get_defaults()
    name = inquirer.text(message="Name:", default=defaults.name, mandatory=True).execute()
    description = inquirer.text(message="Description:").execute()
    version = inquirer.text(message="Version:", default=defaults.version, mandatory=True).execute()
    author = inquirer.text(message="Author name:", default=defaults.author_name).execute()
    email = inquirer.text(message="Author email:", default=defaults.author_email).execute()

    license_choices = [Choice('skip')] + [Choice(value=n, name=f"{n} ({d})") for n, d in LICENSES.items()]
    license_name = inquirer.fuzzy(message="License:", choices=license_choices, vi_mode=True, wrap_lines=True).execute()
    requires_python = inquirer.text(message="requires-python:", default=defaults.requires_python, mandatory=True).execute()
    homepage = inquirer.text(message="Home page:").execute()
    dependencies = []

    if inquirer.confirm(message="Add dependencies?", default=True).execute():
        dependencies = collect_dependencies()

    return SimpleNamespace(
        name=name,
        description=description,
        version=version,
        author=author,
        email=email,
        license=license_name,
        requires_python=requires_python,
        homepage=homepage,
        dependencies=dependencies
    )


def collect_dependencies():
    dependencies = []
    prompt = "Add a package (leave blank to continue):"
    while True:
        name = inquirer.text(message=prompt).execute()
        if not name:
            break

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
        dependencies.append(name)
        prompt = "Add another package (leave blank to continue):"
    return dependencies


def get_defaults():
    author_name, author_email = get_default_author()
    return SimpleNamespace(
        name=os.path.basename(os.getcwd()).lower(),
        version='0.1.0',
        author_name=author_name,
        author_email=author_email,
        requires_python='>=3.8',
    )


def get_default_author():
    try:
        cmd = ['git', 'config', '-l']
        git_configs = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        values = dict(s.split('=', 1) for s in git_configs.splitlines())
        return values.get('user.name'), values.get('user.email')
    except Exception:
        return None, None


def build_toml(meta):
    toml = tomlkit.document()
    project_table = tomlkit.table()
    project_table.add('name', meta.name)
    project_table.add('description', meta.description)
    if meta.author or meta.email:
        authors_list = tomlkit.array()
        author_inline = tomlkit.inline_table()
        author_inline.update({'name': meta.author or '', 'email': meta.email or ''})
        authors_list.append(author_inline)
        project_table.add('authors', authors_list)
    project_table.add('readme', 'README.md')
    license_inline = tomlkit.inline_table()
    license_inline.update({'file': 'LICENSE'})
    project_table.add('license', license_inline)
    project_table.add('dynamic', tomlkit.array('["version"]'))
    project_table.add('requires-python', meta.requires_python)
    dependencies_list = tomlkit.array()
    dependencies_list.extend(meta.dependencies)
    project_table.add('dependencies', dependencies_list)
    toml.add('project', project_table)

    if meta.homepage:
        urls_table = tomlkit.table()
        urls_table.add('homepage', meta.homepage)
        project_table.add('url', urls_table)

    build_system_table = tomlkit.table()
    build_system_table.add('requires', tomlkit.array('["flit_core>=3.8.0,<4"]'))
    build_system_table.add('build-backend', 'flit_core.buildapi')
    toml.add('build-system', build_system_table)

    return toml


def write_toml(toml):
    with open('pyproject.toml', 'w') as f:
        tomlkit.dump(toml, f)
        click.secho(f"Added 'pyproject.toml'", fg='cyan')


def write_readme(meta):
    if os.path.exists('README.md'):
        return
    with open('README.md', 'w') as f:
        f.write(f"# {meta.name}\n\n {meta.description}\n")
        click.secho(f"Added 'README.md'", fg='cyan')


def write_license(meta):
    if os.path.exists('LICENSE') or meta.license == 'skip':
        return
    licenses_dir = pathlib.Path(__file__).parent / 'licenses'
    year = date.today().year
    with (licenses_dir / f"{meta.license}.txt").open() as f_in, open('LICENSE', 'w') as f_out:
        content = f_in.read().format(year=year, author=meta.author)
        f_out.write(content)
        click.secho(f"Added 'LICENSE'", fg='cyan')


def write_root_module_with_version(meta):
    module_name = meta.name.lower().replace('-', '_')
    os.makedirs(module_name, exist_ok=True)
    with open(f"{module_name}/__init__.py", 'w') as f:
        f.write(f"__version__ = '{meta.version}'")
        click.secho(f"Added '{module_name}/__init__.py'", fg='cyan')
