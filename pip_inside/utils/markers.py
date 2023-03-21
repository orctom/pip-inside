# https://peps.python.org/pep-0496/
# https://peps.python.org/pep-0508/
import logging
import os
from typing import List, Union

from packaging.markers import InvalidMarker, Op, UndefinedComparison, UndefinedEnvironmentName, Variable
from pkg_resources import Requirement

LOGGER = logging.getLogger(__name__)


STANDARD = (
    'os_name',
    'sys_platform',
    'platform_machine',
    'platform_python_implementation',
    'platform_release',
    'platform_system',
    'platform_version',
    'python_version',
    'python_full_version',
    'implementation_name',
    'implementation_version',
)


def filter_requirements(requirements: List[Requirement]):
    dependencies = []
    for require in requirements:
        req = filter_requirement(require)
        if req:
            dependencies.append(str(req))
    return dependencies


def filter_requirement(require: Requirement):
    try:
        if require.marker is None:
            return require
        if require.marker.evaluate(os.environ):
            require.marker._markers = filter_custom_markers(require.marker._markers)
            return require
        return None
    except (InvalidMarker, UndefinedComparison, UndefinedEnvironmentName) as e:
        LOGGER.exception(f"Invalid dependency: [{str(require)}], {str(e)}")
        return None


def filter_custom_markers(markers: Union[tuple, str, list]):
    if isinstance(markers, list):
        _markers = [filter_custom_markers(marker) for marker in markers]
        for i, marker in enumerate(_markers):
            if marker is not None:
                continue
            if i >= 1 and isinstance(_markers[i - 1], (str, Op)):
                _markers[i - 1] = None
            if i < len(_markers) - 1 and isinstance(_markers[i + 1], (str, Op)):
                _markers[i + 1] = None
        _markers = list(filter(None, _markers))
        return _markers if len(_markers) > 0 else None
    elif isinstance(markers, str):
        return markers
    elif isinstance(markers, tuple):
        if any(isinstance(m, Variable) for m in markers):
            return markers
        else:
            return None
    else:
        # should not happen
        return markers
