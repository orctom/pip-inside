import os
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import click
import tomlkit
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from pip_inside import Aborted
from pip_inside.utils import licenses, misc, packages, versions


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
    write_resource('.gitignore')
    write_resource('.dockerignore')
    write_root_module_with_version(meta)


def check_pyproject_toml():
    if not os.path.exists('pyproject.toml'):
        return

    try:
        with open('pyproject.toml', 'r') as f:
            data = tomlkit.load(f)
        build_system = data.get('build_system')
        if build_system is not None:
            if build_system.get('build-backend') == 'flit_core.buildapi':
                raise Aborted("Skip, 'pyproject.toml' file already exists")
            else:
                raise Aborted("Skip, 'pyproject.toml' file already exists with unsupported 'build-system', only supports 'flit_core.buildapi'")
    except Aborted as e:
        raise e
    except Exception as e:
        raise Aborted(f"Skip, 'pyproject.toml' already exists, and failed to load: {e}")


def collect_metadata():
    defaults = get_defaults()
    name = inquirer.text(message="Name:", default=defaults.name, mandatory=True).execute()
    description = inquirer.text(message="Description:").execute()
    version = inquirer.text(message="Version:", default=defaults.version, mandatory=True).execute()
    author = inquirer.text(message="Author name:", default=defaults.author_name).execute()
    email = inquirer.text(message="Author email:", default=defaults.author_email).execute()

    license_choices = [Choice('skip')] + [Choice(value=n, name=f"{n} ({d})") for n, d in licenses.LICENSES.items()]
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
    name = packages.prompt_a_package()
    while name is not None:
        dependencies.append(name)
        name = packages.prompt_a_package(True)
    return dependencies


def get_defaults():
    author_name, author_email = get_default_author()
    return SimpleNamespace(
        name=os.path.basename(os.getcwd()).lower(),
        version='0.1.0',
        author_name=author_name,
        author_email=author_email,
        requires_python='>=3.10',
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
    pi_table = tomlkit.table()
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
    if meta.license != 'skip':
        license_inline.update({'file': 'LICENSE'})
        project_table.add('license', license_inline)
        pi_table.add('license-expression', meta.license)
    project_table.add('dynamic', ["version"])
    project_table.add('requires-python', meta.requires_python)

    dependencies = tomlkit.array()
    dependencies.extend(meta.dependencies)
    project_table.add('dependencies', dependencies.multiline(True))

    optional_dependencies = tomlkit.table()
    optional_dependencies.add('dev', tomlkit.array('["ruff",]').multiline(True))
    project_table.add('optional-dependencies', optional_dependencies)

    if meta.homepage:
        urls_table = tomlkit.table()
        urls_table.add('homepage', meta.homepage)
        project_table.add('urls', urls_table)

    toml.add('project', project_table)
    toml.add('build-system', get_build_system_table())
    toml.add('tool', get_tool_table(pi_table, meta))
    return toml


def get_build_system_table():
    table = tomlkit.table()
    table.add('requires', ["flit_core>=3.8.0,<4"])
    table.add('build-backend', 'flit_core.buildapi')
    return table


def get_tool_table(pi_table, meta):
    table = tomlkit.table(True)
    table.add('pi', pi_table)
    table.add('pytest', get_pytest_table(meta))
    table.add('autopep8', get_autopep8_table(meta))
    table.add('ruff', get_ruff_table(meta))
    return table


def get_pytest_table(meta):
    table = tomlkit.table(True)
    table_options = tomlkit.table()
    table_options.add('minversion', '7.0')
    table_options.add('addopts', '-ra -q -s')
    table_options.add('testpaths', ["tests"])
    table.add('ini_options', table_options)
    return table


def get_pytest_options_table(meta):
    table = tomlkit.table()
    table.add('minversion', '7.0')
    table.add('addopts', '-ra -q -s')
    table.add('testpaths', ["tests"])
    return table


def get_autopep8_table(meta):
    table = tomlkit.table()
    table.add('max_line_length', 135)
    table.add('in-place', True)
    table.add('recursive', True)
    table.add('aggressive', 3)
    return table


def get_ruff_table(meta):
    def get_target_version():
        if meta and meta.requires_python:
            p = re.compile('\D')
            return f"py{p.sub('', meta.requires_python)}"
        return None
    table = tomlkit.table()
    exclude = tomlkit.array()
    exclude.extend([
        ".bzr",
        ".direnv",
        ".eggs",
        ".git",
        ".git-rewrite",
        ".hg",
        ".mypy_cache",
        ".nox",
        ".pants.d",
        ".pytype",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pypackages__",
        "_build",
        "buck-out",
        "build",
        "dist",
        "node_modules",
        "venv",
        "data",
        ".vscode",
        ".ipynb_checkpoints",
    ])
    table.add('exclude', exclude.multiline(True))
    table.add('line-length', 135)
    target_version = get_target_version()
    if target_version:
        table.add('target-version', target_version)

    table_lint = tomlkit.table()
    table_lint.add('select', ["E4", "E7", "E9", "F"])
    table_lint.add('ignore', [])
    table_lint.add('fixable', ["ALL"])
    table_lint.add('unfixable', [])
    table_lint.add('dummy-variable-rgx', '^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$')
    table.add('lint', table_lint)

    table_format = tomlkit.table()
    table_format.add('quote-style', 'double')
    table_format.add('indent-style', 'space')
    table_format.add('skip-magic-trailing-comma', False)
    table_format.add('line-ending', 'auto')
    table.add('format', table_format)

    return table


def write_toml(toml):
    with open('pyproject.toml', 'w') as f:
        tomlkit.dump(toml, f)
        click.secho("Added 'pyproject.toml'", fg='bright_cyan')


def write_readme(meta):
    if os.path.exists('README.md'):
        return
    with open('README.md', 'w') as f:
        f.write(f"# {meta.name}\n\n {meta.description}\n")
        click.secho("Added 'README.md'", fg='bright_cyan')


def write_license(meta):
    if os.path.exists('LICENSE') or meta.license == 'skip':
        return
    license_file = licenses.get_file(meta.license)
    with license_file.open() as f_in, open('LICENSE', 'w') as f_out:
        year = date.today().year
        f_out.write(f_in.read().format(year=year, author=meta.author))
        click.secho("Added 'LICENSE'", fg='bright_cyan')


def write_resource(filename: str):
    target = Path(filename)
    if target.exists():
        return
    src = Path(__file__).parent / 'resources' / filename
    shutil.copyfile(src, target)
    click.secho(f"Added '{filename}'", fg='bright_cyan')


def write_root_module_with_version(meta):
    module_name = misc.norm_module(meta.name)
    os.makedirs(module_name, exist_ok=True)
    filepath = f"{module_name}/__init__.py"
    msg = versions.set_version_in_init(filepath, meta.version)
    click.secho(msg, fg='bright_cyan')
