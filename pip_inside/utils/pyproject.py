import itertools
import os
from types import SimpleNamespace
from typing import List, Union

import tomlkit

from pip_inside.utils.version_specifies import get_package_name


class PyProject:
    def __init__(self, path='pyproject.toml') -> None:
        self.path = path
        self._meta = {}

    @classmethod
    def from_toml(cls, path='pyproject.toml'):
        pyproject = cls(path)
        pyproject.load()
        return pyproject

    def load(self):
        if not os.path.exists(self.path):
            raise ValueError(f"'{self.path}' not found")

        with open(self.path, 'r') as f:
            self._meta = tomlkit.load(f)

    def flush(self):
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

    def add_dependency(self, name: str, group: str = 'main'):
        if group == 'main':
            key = 'project.dependencies'
        else:
            key = f"project.optional-dependencies.{group}"
        dependencies = self.get(key, create_if_missing=True, default=[])
        if name not in dependencies:
            dependencies.append(name)

    def remove_dependency(self, name: str, group: str = 'main'):
        if group == 'main':
            key = 'project.dependencies'
        else:
            key = f"project.optional-dependencies.{group}"
        dependencies = self.get(key, create_if_missing=False)
        if dependencies is None or len(dependencies) == 0:
            return False
        package_name = get_package_name(name)
        remove_list = [dep for dep in dependencies if get_package_name(dep) == package_name]
        if len(remove_list) == 0:
            return False
        for dep in remove_list:
            try:
                dependencies.remove(dep)
            except ValueError:
                pass
        return True

    def find_dependency(self, name: str, group: str = 'main'):
        package_name = get_package_name(name)
        for dep in self.get_dependencies(group):
            pkg_name = get_package_name(dep)
            if pkg_name == package_name:
                return dep
        return None

    @staticmethod
    def _is_in_dependencies(name: str, dependencies: List[str]) -> bool:
        if name in dependencies:
            return True
        if name in set([get_package_name(dep) for dep in dependencies]):
            return True
        return False

    def get_dependencies(self, group: str = 'main'):
        if group == 'all':
            key_main = 'project.dependencies'
            key_optionals = 'project.optional-dependencies'
            deps_main = self.get(key_main, default=[])
            deps_optionals = list(itertools.chain(*self.get(key_optionals, default={}).values()))
            return deps_main + deps_optionals

        if group == 'main':
            return self.get('project.dependencies')
        else:
            return self.get(f"project.optional-dependencies.{group}")

    @staticmethod
    def get_template():
        return SimpleNamespace(
            name=os.path.basename(os.getcwd()),
            description=''
        )
