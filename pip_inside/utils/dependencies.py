import collections
import os
import shutil
import site
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set

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
        self.package.echo(self.prefix)


class Package:

    def __init__(self,
                 name: str,
                 *,
                 specs: str = None,
                 extras: str = None,
                 group: str = None,
                 version: str = None,
                 parent: 'Package' = None) -> None:
        self.name = name
        self.specs = specs
        self.extras = extras
        self.group = group
        self.version = version
        self.parent: 'Package' = parent
        self.children: List['Package'] = []
        self._hit: Optional[str] = None

    def get_ref_path(self) -> List[str]:
        paths = []
        parent = self.parent
        while parent is not None and parent.name != ROOT:
            paths.append(parent.name)
            parent = parent.parent
        paths.reverse()
        return paths

    def echo(self, prefix: Optional[str] = None):
        name = self.name_with_extras
        fg = get_name_fg_by_group(self.group)
        if self._hit and self._hit in name:
            i = name.index(self._hit)
            j = i + len(self._hit)
            name = (
                f"{click.style(name[:i], fg=fg)}"
                f"{click.style(name[i:j], fg=fg, reverse=True)}"
                f"{click.style(name[j:], fg=fg)}"
            )
        else:
            name = click.style(name, fg=fg)
        name = f"{prefix} {name}" if prefix else name
        required = f"required: {self.specs or '*'}"
        installed = f"installed: {self.version}" if self.version else click.style('[not installed]', fg='yellow')
        group = f"group: {click.style(self.group, fg=COLOR_OPTIONAL)}" if self.group not in (None, 'main') else None
        options = filter(None, (required, installed, group))
        click.echo(f"{name} [{', '.join(options)}]")

    def _search(self, search: str):
        if search:
            if search in self.name:
                self._hit = search
                for child in self.children:
                    child._hit = search
            for child in self.children:
                self._hit = child._search(search) or self._hit
        return self._hit

    def tree_list(self, skip='│', branch='├', last='└', hyphen='─', prefix='', search: Optional[str] = None) -> Generator[TreeEntry, None, None]:
        children = [child for child in self.children if child._hit is not None] if search else self.children
        n_children = len(children)
        for i, child in enumerate(children):
            if i < n_children - 1:
                next_prefix = ''.join([prefix, skip, '   '])
                fork = branch
            else:
                next_prefix = ''.join([prefix, '    '])
                fork = last

            yield TreeEntry(prefix=f"{prefix}{fork}{hyphen}{hyphen}", package=child)
            yield from child.tree_list(skip, branch, last, hyphen, next_prefix, search=search)

    @property
    def name_with_extras(self):
        return f"{self.name}[{''.join(self.extras)}]" if self.extras else self.name

    def __str__(self) -> str:
        if self.group:
            return f"{self.name_with_extras} [{self.group}] [required: {self.specs or '*'}, installed: {self.version}]"
        else:
            return f"{self.name_with_extras} [required: {self.specs or '*'}, installed: {self.version}]"

    def __repr__(self) -> str:
        return self.__str__()


class Dependencies:
    def __init__(self) -> None:
        self._distributions = Distributions()
        self._pyproject = PyProject.from_toml()
        self._cyclic_dendencies = []
        self._root: Package = Package(ROOT)
        self._root_non_dep: Package = Package(ROOT)
        self._direct_dependencies = {}

    def load_dependencies(self):
        def load_direct_dependencies():
            self._direct_dependencies.clear()
            for r, group in self._pyproject.get_dependencies_with_group().items():
                pkg = Package(r.key, extras=r.extras, specs=str(r.specifier), group=group, parent=self._root)
                self._direct_dependencies[r.key] = pkg

        load_direct_dependencies()
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
        def get_children():
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
                if parents is not None:
                    parents[name].add(pkg.name)
                self._load_children(child, exclusion, parents)

        def get_extras():
            extras = pkg.extras
            dist._dep_map.get(extras)
            if extras is None or len(extras) == 0 or len(dist._dep_map) == 0:
                return

            for extra in extras:
                for r in dist._dep_map.get(extra, []):
                    dep = self._direct_dependencies.get(r.name)
                    specs, group = (r.specs, None) if dep is None else (dep.specs or r.specs, dep.group)
                    child = Package(r.key, specs=specs, group=group, parent=pkg)
                    pkg.children.append(child)
                    if parents is not None:
                        parents[r.key].add(pkg.name)
                    self._load_children(child, exclusion, parents)

        dist = self._distributions.get(pkg.name)
        if dist is None:
            return
        pkg.version = dist.version
        get_children()
        get_extras()

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

    def print_dependencies(self, search: Optional[str] = None):
        if len(self._root.children) == 0:
            self.load_dependencies()
        self._print_dep_tree(self._root, search)

    def print_non_dependencies(self, search: Optional[str] = None):
        if len(self._root_non_dep.children) == 0:
            self.load_non_dependencies()
        self._print_dep_tree(self._root_non_dep, search)

    def _print_dep_tree(self, root: Package, search: Optional[str] = None):
        if self._cyclic_dendencies:
            click.secho('Cyclic dependencies:', fg='yellow')
            for path in self._cyclic_dendencies:
                click.secho(f"\t{path}", fg='yellow')
        key_main = click.style(COLOR_MAIN, fg=COLOR_MAIN)
        key_optional = click.style(COLOR_OPTIONAL, fg=COLOR_OPTIONAL)
        key_subs = click.style(COLOR_SUBS, fg=COLOR_SUBS)
        click.secho(f"Dependencies: (main: {key_main}, optional: {key_optional}, sub-dependencies: {key_subs})")
        for child in root.children:
            child._search(search)
            child_entries = list(child.tree_list(search=search))
            if not search or child._hit or child_entries:
                child.echo()
            for entry in child_entries:
                entry.echo()

    def get_unused_dependencies_for(self, require: Requirement) -> List[str]:
        def get_replyings(pkg: Package, _dep_name: str):
            _pkg_name = norm_name(pkg.name)
            if _pkg_name == _dep_name:
                return pkg.parent
            for pkg_child in pkg.children:
                return get_replyings(pkg_child, _dep_name)

        if len(self._root.children) == 0:
            self.load_dependencies()

        name = require.key
        unused = []
        for dep in self._distributions.get(name).requires():
            dep_name = norm_name(dep.name)
            replyings = [get_replyings(child, dep_name) for child in self._root.children]
            replyings = list(filter(None, replyings))
            if len(replyings) == 0:
                unused.append(dep_name)
        return unused
