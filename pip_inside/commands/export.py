import collections

import click

from pip_inside.utils.dependencies import Dependencies, Package


def handle_export():
    dependencies = Dependencies().load_dependencies()
    requirements = collections.defaultdict(list)
    for child in dependencies._root.children:
        requirements[child.group].append(f"{child.name}=={child.version}" if child.version else child.name)
        for group, dep in _find_installed_child(child):
            requirements[group or child.group].append(dep)

    for group, deps in requirements.items():
        filename = 'requirements.txt' if group == 'main' else f"requirements-{group}.txt"
        with open(filename, 'w') as f:
            for dep in deps:
                f.write(f"{dep}\n")
        click.secho(f"Updated {filename}", fg='bright_cyan')


def _find_installed_child(pkg: Package):
    for child in pkg.children:
        yield child.group, f"{child.name}=={child.version}"
        for group, dep in _find_installed_child(child):
            yield group or child.group, dep
