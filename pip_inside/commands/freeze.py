import collections

import click
import tomlkit

from pip_inside.utils.dependencies import Package


def handle_freeze():
    pkg = Package.from_project()
    dependencies = collections.defaultdict(list)
    for child in pkg.children:
        dependencies[child.group].append(f"{child.name}=={child.version}")
        for group, dep in _find_installed_child(child):
            dependencies[group or child.group].append(dep)
    with open('pi.lock', 'w') as f:
        tomlkit.dump(dependencies, f)
    click.secho(f"Generated pi.lock", fg='bright_cyan')


def _find_installed_child(pkg: Package):
    for child in pkg.children:
        yield child.group, f"{child.name}=={child.version}"
        for group, dep in _find_installed_child(child):
            yield group or child.group, dep
