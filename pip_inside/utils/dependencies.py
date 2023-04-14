import collections
import os
import shutil
import site
from pathlib import Path
from typing import Dict, List, Optional, Set

import click
from pkg_resources import Distribution, Requirement, find_distributions

from .misc import norm_name
from .pyproject import PyProject

ROOT = 'root'
DEPENDENCIES_COMMON = [
    'pip', 'certifi', 'setuptools', 'ipython', 'poetry', 'requests', 'idna', 'urllib3', 'wheel', 'tomlkit', 'pip-inside',
]
COLOR_MAIN = 'blue'
COLOR_OPTIONAL = 'green'
COLOR_SUBS = 'white'


def get_name_fg_by_group(group):
    if group is None:
        return COLOR_SUBS
    return COLOR_MAIN if group == 'main' else COLOR_OPTIONAL


def get_site_package_path():
    env_root = Path(shutil.which('python')).parent.parent
    paths = site.getsitepackages(prefixes=[env_root])
    path = paths[0]
    if os.path.exists(path):
        return path

    return next((env_root / 'lib').glob('python*')) / 'site-packages'


class Distributions:
    def __init__(self) -> None:
        self._distributions = self._find_distributions()

    def _find_distributions(self) -> Dict[str, Distribution]:
        distributions: Dict[str, Distribution] = {}
        site_package_path = get_site_package_path()
        for dist in find_distributions(site_package_path):
            distributions[dist.key] = dist
        return distributions

    def get_all(self) -> List[Distribution]:
        return list(self._distributions.values())

    def get(self, name) -> Distribution:
        return self._distributions.get(norm_name(name))


class TreeEntry:
    def __init__(self, prefix, package: 'Package') -> None:
        self.prefix = prefix
        self.package = package

    def __str__(self):
        return f"{self.prefix} {self.package}"

    def echo(self):
        name = click.style(self.package.name, fg=get_name_fg_by_group(self.package.group))
        installed = f"installed: {self.package.version}" if self.package.version else click.style('[not installed]', fg='yellow')
        click.echo(f"{self.prefix} {name} [required: {self.package.specs or '*'}, {installed}]")


class Package:

    def __init__(self,
                 name: str,
                 *,
                 specs: str = None,
                 group: str = None,
                 version: str = None,
                 parent: 'Package' = None) -> None:
        self.name = name
        self.specs = specs
        self.group = group
        self.version = version
        self.parent: 'Package' = parent
        self.children: List['Package'] = []

    def get_ref_path(self) -> List[str]:
        paths = []
        parent = self.parent
        while parent is not None and parent.name != ROOT:
            paths.append(parent.name)
            parent = parent.parent
        paths.reverse()
        return paths

    def echo(self):
        name = click.style(self.name, fg=get_name_fg_by_group(self.group))
        installed = f"installed: {self.version}" if self.version else click.style('[not installed]', fg='yellow')
        click.echo(f"{name} [required: {self.specs or '*'}, {installed}]")

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

    def __str__(self) -> str:
        if self.group:
            return f"{self.name} [{self.group}] [required: {self.specs or '*'}, installed: {self.version}]"
        else:
            return f"{self.name} [required: {self.specs or '*'}, installed: {self.version}]"

    def __repr__(self) -> str:
        return self.__str__()


class Dependencies:
    def __init__(self) -> None:
        self._distributions = Distributions()
        self._pyproject = PyProject.from_toml()
        self._cyclic_dendencies = []
        self._root: Package = Package(ROOT)
        self._root_non_dep: Package = Package(ROOT)
        self._direct_dependencies = {
            r.key: Package(r.key, specs=str(r.specifier), group=group, parent=self._root)
            for r, group in self._pyproject.get_dependencies_with_group().items()
        }

    def load_dependencies(self):
        self._root.children.clear()
        for child in self._direct_dependencies.values():
            self._root.children.append(child)
            self._load_children(child)
        return self

    def load_non_dependencies(self):
        if len(self._root.children) == 0:
            self.load_dependencies()

        self._root_non_dep.children.clear()
        project_name = self._pyproject.get('project.name')
        dependencies_project = self._get_all_project_dependencies()
        exclusion = set([project_name] + dependencies_project)
        parents = collections.defaultdict(set)
        for dist in self._distributions.get_all():
            name = norm_name(dist.key)
            if name in exclusion:
                continue
            child = Package(name, parent=self._root_non_dep)
            self._root_non_dep.children.append(child)
            parents[name].add(ROOT)
            self._load_children(child, exclusion, parents)
        self._root_non_dep.children = [child for child in self._root_non_dep.children if parents.get(child.name) == {ROOT}]
        return self

    def _load_children(self, pkg: Package, exclusion: Optional[Set[str]] = None, parents: Optional[Dict[str, Set[str]]] = None):
        dist = self._distributions.get(pkg.name)
        if dist is None:
            return
        pkg.version = dist.version
        for r in dist.requires():
            name, specs_r = norm_name(r.name), str(r.specifier)
            if exclusion is not None and name in exclusion:
                continue
            ref_path = pkg.get_ref_path()
            if name in ref_path:
                self._cyclic_dendencies.append(f"{' -> '.join(ref_path)} -> {pkg.name} -> {name}")
                continue

            dep = self._direct_dependencies.get(name)
            specs, group = (specs_r, None) if dep is None else (dep.specs or specs_r, dep.group)
            child = Package(name, specs=specs, group=group, parent=pkg)
            pkg.children.append(child)
            self._load_children(child, exclusion, parents)
            if parents is not None:
                parents[name].add(pkg.name)

    def _get_all_project_dependencies(self, exclusions: Optional[List[str]] = None) -> List[str]:
        def pkg_deps(pkg: Package):
            name = norm_name(pkg.name)
            if exclusions and (name in exclusions or pkg.name in exclusions):
                return
            yield norm_name(pkg.name)
            for pkg_child in pkg.children:
                yield from pkg_deps(pkg_child)
        dependencies = list()
        for child in self._root.children:
            for name in pkg_deps(child):
                dependencies.append(name)
        return dependencies

    def print_dependencies(self):
        if len(self._root.children) == 0:
            self.load_dependencies()
        self._print_dep_tree(self._root)

    def print_non_dependencies(self):
        if len(self._root_non_dep.children) == 0:
            self.load_non_dependencies()
        self._print_dep_tree(self._root_non_dep)

    def _print_dep_tree(self, root: Package):
        if self._cyclic_dendencies:
            click.secho('Cyclic dependencies:', fg='yellow')
            for path in self._cyclic_dendencies:
                click.secho(f"\t{path}", fg='yellow')
        key_main = click.style(COLOR_MAIN, fg=COLOR_MAIN)
        key_optional = click.style(COLOR_OPTIONAL, fg=COLOR_OPTIONAL)
        key_subs = click.style(COLOR_SUBS, fg=COLOR_SUBS)
        click.secho(f"Dependencies: (main: {key_main}, optional: {key_optional}, sub-dependencies: {key_subs})")
        for child in root.children:
            child.echo()
            for entry in child.tree_list():
                entry.echo()

    def get_unused_dependencies_for(self, require: Requirement) -> List[str]:
        name = require.key
        other_in_use = set(self._get_all_project_dependencies(exclusions=[name]))
        children = {norm_name(r.name) for r in self._distributions.get(name).requires()}
        return list(children - other_in_use)
