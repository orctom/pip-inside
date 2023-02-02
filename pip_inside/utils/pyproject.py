import os
from typing import List, Union

import tomlkit

from pip_inside.utils import version_specifies

_PROJECT_DATA = None


def load():
    global _PROJECT_DATA
    if not os.path.exists('pyproject.toml'):
        raise ValueError(f"'pyproject.toml' not found in current directory")

    with open('pyproject.toml', 'rb') as f:
        _PROJECT_DATA = tomlkit.load(f)


def flush():
    global _PROJECT_DATA
    with open('pyproject.toml', "wb") as f:
        tomlkit.dump(_PROJECT_DATA, f)


def update(key: str, value: Union[str, int, float, dict, list]):
    global _PROJECT_DATA
    data = _PROJECT_DATA
    attrs = key.split('.')
    for attr in attrs[:-1]:
        data = data.setdefault(attr, {})
    data[attrs[-1]] = value


def get(key: str, *, create_if_missing: bool = False, default = None):
    global _PROJECT_DATA
    data = _PROJECT_DATA
    attrs = key.split('.')
    if create_if_missing:
        for attr in attrs[:-1]:
            data = data.setdefault(attr, {})
        return data.setdefault(attrs[-1], default)
    else:
        for attr in attrs:
            data = data.get(attr)
            if data is None:
                return None
        return data


def add_dependency(name: str, group: str = 'main'):
    global _PROJECT_DATA
    if group == 'main':
        key = 'project.dependencies'
    else:
        key = f"project.optional-dependencies.{group}"
    dependencies = get(key, create_if_missing=True, default=[])
    if name not in dependencies:
        dependencies.append(name)


def remove_dependency(name: str, group: str = 'main'):
    global _PROJECT_DATA
    if group in 'main':
        key = 'project.dependencies'
    else:
        key = f"project.optional-dependencies.{group}"
    dependencies = get(key, create_if_missing=False)
    if dependencies is None or not _is_in_dependencies(name, dependencies):
        return False
    try:
        dependencies.remove(name)
    except ValueError:
        pass
    return True


def _is_in_dependencies(name: str, dependencies: List[str]) -> bool:
    if name in dependencies:
        return True
    if name in set([version_specifies.get_package_name(dep) for dep in dependencies]):
        return True
    return False
