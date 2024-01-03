import os
from typing import Any, Dict, List, Optional, Union

import tomlkit

from pip_inside import Aborted
from pip_inside.utils import markers
from pip_inside.utils.markers import Requirement

from .misc import norm_module


class PyProject:
    def __init__(self, path='pyproject.toml') -> None:
        self.path = path
        self._meta: tomlkit.TOMLDocument = tomlkit.TOMLDocument()
        self._dependencies: Dict[str, List[Requirement]] = {}

    @classmethod
    def from_toml(cls, path='pyproject.toml'):
        pyproject = cls(path)
        pyproject.load()
        return pyproject

    def _load_dependencies(self):
        key_main = 'project.dependencies'
        key_optionals = 'project.optional-dependencies'
        self._dependencies['main'] = [Requirement(dep) for dep in self.get(key_main, default=[])]
        for key, deps in self.get(key_optionals, default={}).items():
            self._dependencies[key] = [Requirement(dep) for dep in deps]

    def _dump_dependencies(self):
        for key, requires in self._dependencies.items():
            deps = tomlkit.array()
            for r in requires:
                deps.add_line(str(r))
            deps = deps.multiline(True)
            if key == 'main':
                self.set('project.dependencies', deps)
            else:
                self.set(f"project.optional-dependencies.{key}", deps)

    def validate(self):
        def check_exists(attr: str, msg: Optional[str] = None):
            if self.get(attr) is None:
                msg = f", {msg}" if msg else ''
                raise Aborted(f"Unsupported pyproject.toml, expecting: '{attr}' {msg}")
        def check_not_exists(attr: str, msg: Optional[str] = None):
            if self.get(attr) is not None:
                msg = f", {msg}" if msg else ''
                raise Aborted(f"Unsupported pyproject.toml, unexpected: '{attr}' {msg}")
        def check_equals(attr: str, val: Any, msg: Optional[str] = None):
            if self.get(attr) != val:
                msg = f", {msg}" if msg else ''
                raise Aborted(f"Unsupported pyproject.toml, expecting `{attr} = {val}` {msg}")

        if len(self._meta) == 0:
            return
        check_exists('project.name')
        check_not_exists('project.version', f"should be defined in {norm_module(self.get('project.name'))}/__init__.py")
        check_equals('project.dynamic', ['version'])
        check_exists('project.requires-python')
        check_exists('build-system')
        check_equals('build-system.build-backend', 'flit_core.buildapi', 'only supports `flit_core` backend')

    def load(self):
        if not os.path.exists(self.path):
            raise ValueError(f"'{self.path}' not found")

        with open(self.path, 'r') as f:
            self._meta = tomlkit.load(f)
        self.validate()
        self._load_dependencies()

    def flush(self):
        self._dump_dependencies()
        with open(self.path, "w") as f:
            tomlkit.dump(self._meta, f)

    def update(self, key: str, value: Union[str, int, float, dict, list]):
        data = self._meta
        attrs = key.split('.')
        for attr in attrs[:-1]:
            data = data.setdefault(attr, {})
        data[attrs[-1]] = value

    def get(self, key: str, *, create_if_missing: bool = False, default = None):
        data = self._meta
        attrs = key.split('.')

        for attr in attrs[:-1]:
            if create_if_missing:
                data = data.setdefault(attr, {})
            else:
                data = data.get(attr)
                if data is None:
                    return default
        return data.setdefault(attrs[-1], default) if create_if_missing else data.get(attrs[-1], default)

    def set(self, key: str, value: Union[str, int, float, dict, list], *, create_if_missing: bool = True):
        data = self._meta
        attrs = key.split('.')

        for attr in attrs[:-1]:
            if create_if_missing:
                data = data.setdefault(attr, {})
            else:
                data = data.get(attr)
                if data is None:
                    return False
        data[attrs[-1]] = value
        return True

    def add_dependency(self, require: Requirement, group: str = 'main'):
        do_add = True
        dependencies = self._dependencies.get(group)
        if dependencies:
            for i, dep in enumerate(dependencies):
                if require.key != dep.key:
                    continue
                if str(require) == str(dep):
                    return False
                do_add = False
                dependencies[i] = require

        if do_add:
            if dependencies is None:
                self._dependencies[group] = [require]
            else:
                dependencies.append(require)
        return True

    def remove_dependency(self, require: Requirement, group: str = 'main'):
        dependencies = self._dependencies.get(group)
        if not dependencies:
            return False
        deps = [dep for dep in dependencies if dep.key != require.key]
        if len(deps) == len(dependencies):
            return False
        self._dependencies[group] = deps
        return True

    def get_for_install(self, group: str = 'main'):
        deps = self._dependencies.get(group)
        if deps is None:
            return None
        return markers.filter_requirements(deps)

    def get_dependencies_for_install(self) -> Dict[str, List[str]]:
        return {
            group: markers.filter_requirements(deps)
            for group, deps in self._dependencies.items()
        }

    def get_dependencies_with_group(self) -> Dict[Requirement, str]:
        dependencies: Dict[Requirement, str] = {}
        for group, deps in self._dependencies.items():
            for dep in deps:
                dependencies[dep] = group
        return dependencies
