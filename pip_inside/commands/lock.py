import collections

import click
import tomlkit

from pip_inside.utils.dependencies import Dependencies, Package


def handle_lock():
    dependencies = Dependencies().load_dependencies()
    requirements = collections.defaultdict(tomlkit.array)
    for child in dependencies._root.children:
        requirements[child.group].add_line(f"{child.name}=={child.version}")
        for group, dep in _find_installed_child(child):
            requirements[group or child.group].add_line(dep)
    requirements = {
        group: deps.multiline(True)
        for group, deps in requirements.items()
    }
    with open('pi.lock', 'w') as f:
        tomlkit.dump(requirements, f)
    click.secho(f"Generated pi.lock", fg='bright_cyan')


def _find_installed_child(pkg: Package):
    for child in pkg.children:
        yield child.group, f"{child.name}=={child.version}"
        for group, dep in _find_installed_child(child):
            yield group or child.group, dep
