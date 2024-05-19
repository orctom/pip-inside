# https://peps.python.org/pep-0496/
# https://peps.python.org/pep-0508/
import logging
import os
from typing import List, Union

from pkg_resources import Requirement as _Requirement
from pkg_resources._vendor.packaging.markers import InvalidMarker, default_environment, _format_marker
from pkg_resources._vendor.packaging.markers import Marker as _Marker
from pkg_resources._vendor.packaging.markers import Op, UndefinedComparison, UndefinedEnvironmentName, Variable, _evaluate_markers

LOGGER = logging.getLogger(__name__)


class Marker(_Marker):
    def __init__(self) -> None:
        self._markers = []

    def evaluate(self, environment=None):
        def strip_doller_sign(item):
            if item.__class__.__name__ != 'Variable':
                return item
            return Variable(item.value.strip('$'))

        builtin_environment = default_environment()
        current_environment = {**os.environ, **builtin_environment}
        if environment is not None:
            current_environment.update(environment)
        markers = [(strip_doller_sign(lhs), op, strip_doller_sign(rhs)) for lhs, op, rhs in self._markers]
        return _evaluate_markers(markers, current_environment)
    
    def __str__(self):
        return _format_marker(self._markers or [])


class Requirement(_Requirement):
    def __init__(self, requirement_string: str) -> None:
        requirement_string = self._parse_requirements(requirement_string)
        super().__init__(requirement_string)
        if self.marker:
            marker = Marker()
            for lhs, op, rhs in self.marker._markers:
                if lhs.__class__.__name__ == 'Value' and rhs.__class__.__name__ == 'Value':  # multi Value in different modules
                    if '$' in lhs.value:
                        marker._markers.append((Variable(lhs.value), op, rhs))
                    elif '$' in rhs.value:
                        marker._markers.append((lhs, op, Variable(rhs.value)))
                else:
                    marker._markers.append((lhs, op, rhs))
            self.marker = marker

    def _parse_requirements(self, line):
        if ' #' in line:
            line = line[:line.find(' #')]
        return line


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
            return []
    else:
        # should not happen
        return markers
