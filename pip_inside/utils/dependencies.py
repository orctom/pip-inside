import collections
from typing import Dict, List, Set

import click
import pkg_resources

from .pyproject import PyProject

ROOT = 'root'
DEPENDENCIES_COMMON = [
    'pip', 'packaging', 'certifi', 'setuptools', 'ipython', 'tqdm',
    'requests', 'urllib3', 'wheel', 'tomlkit', 'pip-inside',
]
COLOR_MAIN = 'blue'
COLOR_OPTIONAL = 'magenta'
COLOR_SUBS = 'white'


def get_name_fg_by_group(group):
    if group is None:
        return COLOR_SUBS
    return COLOR_MAIN if group == 'main' else COLOR_OPTIONAL


class TreeEntry:
    def __init__(self, prefix, package: 'Package') -> None:
        self.prefix = prefix
        self.package = package

    def __str__(self):
        return f"{self.prefix} {self.package}"

    def echo(self):
        name = click.style(self.package.name, fg=get_name_fg_by_group(self.package.group))
        click.echo(f"{self.prefix} {name} [required: {self.package.specs or '*'}, installed: {self.package.version}]")

class Package:
    NAMES: Dict[str, 'Package'] = {}
    PARENTS: Dict[str, Set[str]] = collections.defaultdict(set)
    PYPROJECT = PyProject.from_toml()
    PROJECT_DEPENDENCIES = {
        r.key: (str(r.specifier), group)
        for r, group in PYPROJECT.get_dependencies_with_group().items()
    }
    CYCLIC_DENDENCIES = []

    def __init__(self,name: str, *, specs: str = None, group: str = None, version: str = None, parent: 'Package' = None) -> None:
        self.name = name
        self.specs = specs
        self.group = group
        self.version = version
        self.parent: 'Package' = parent
        self.children: List['Package'] = []
        self.load()

    def load(self):
        if self.name == ROOT:
            return
        try:
            dist = pkg_resources.get_distribution(self.name)
            self.version = dist.version
            for r in dist.requires():
                name, specs_r = r.name.lower().replace('_', '-'), str(r.specifier)
                parent_paths = self.get_parent_path()
                if name in parent_paths:
                    self.CYCLIC_DENDENCIES.append(f"{' -> '.join(parent_paths)} -> {self.name} -> {name}")
                    continue

                specs_p, group = self.PROJECT_DEPENDENCIES.get(name, (None, None))
                self.children.append(Package(name, specs=specs_p or specs_r, group=group, parent=self))
                self.PARENTS[name].add(self.name)
        except pkg_resources.DistributionNotFound:
            self.version = '[not installed]'

    def get_parent_path(self) -> List[str]:
        paths = []
        parent = self.parent
        while parent is not None and parent.name != ROOT:
            paths.append(parent.name)
            parent = parent.parent
        paths.reverse()
        return paths

    def __str__(self) -> str:
        if self.group:
            return f"{self.name} [{self.group}] [required: {self.specs or '*'}, installed: {self.version}]"
        else:
            return f"{self.name} [required: {self.specs or '*'}, installed: {self.version}]"

    def __repr__(self) -> str:
        return self.__str__()

    def echo(self):
        name = click.style(self.name, fg=get_name_fg_by_group(self.group))
        click.echo(f"{name} [required: {self.specs or '*'}, installed: {self.version}]")

    @classmethod
    def from_project(cls):
        root = Package(ROOT)
        for name, (specs, group) in cls.PROJECT_DEPENDENCIES.items():
            root.children.append(Package(name, specs=specs, group=group, parent=root))
            cls.PARENTS[name].add(ROOT)
        return root

    @classmethod
    def from_unused(cls):
        project_name = cls.PYPROJECT.get('project.name')
        dependencies_project = list(cls.PROJECT_DEPENDENCIES.keys())
        exclusion = set([project_name] + DEPENDENCIES_COMMON + dependencies_project)
        root = Package(ROOT)
        for dist in pkg_resources.working_set:
            name = dist.key.lower().replace('_', '-')
            if name in exclusion:
                continue
            root.children.append(Package(name, parent=root))
            cls.PARENTS[name].add(ROOT)
        root.children = [child for child in root.children if len(cls.PARENTS.get(child.name)) == 1]
        return root

    @classmethod
    def get_unused_sub_dependencies(cls, name: str):
        dist = pkg_resources.get_distribution(name)
        return [
            r.key
            for r in dist.requires()
            if r.key not in cls.PROJECT_DEPENDENCIES and r.key not in DEPENDENCIES_COMMON
        ]

    def tree_list(self, skip='│', branch='├', last='└', hyphen='─', prefix='') -> str:
        n_children = len(self.children)
        for i, child in enumerate(self.children):
            if i < n_children - 1:
                next_prefix = ''.join([prefix, skip, '   '])
                fork = branch
            else:
                next_prefix = ''.join([prefix, '    '])
                fork = last

            yield TreeEntry(prefix=f"{prefix}{fork}{hyphen}{hyphen}", package=child)
            yield from child.tree_list(skip, branch, last, hyphen, next_prefix)

    def print_dependencies(self):
        if self.CYCLIC_DENDENCIES:
            click.secho('Cyclic dependencies:', fg='yellow')
            for path in self.CYCLIC_DENDENCIES:
                click.secho(f"\t{path}", fg='yellow')
        key_main = click.style(COLOR_MAIN, fg=COLOR_MAIN)
        key_optional = click.style(COLOR_OPTIONAL, fg=COLOR_OPTIONAL)
        key_subs = click.style(COLOR_SUBS, fg=COLOR_SUBS)
        click.secho(f"Dependencies: (main: {key_main}, optional: {key_optional}, sub-dependencies: {key_subs})")
        for child in self.children:
            child.echo()
            for entry in child.tree_list(prefix='   '):
                entry.echo()
