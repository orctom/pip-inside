# https://peps.python.org/pep-0496/
# https://peps.python.org/pep-0508/
import logging
import os
import re
from typing import List, Union

from packaging.markers import (
    InvalidMarker,
    Op,
    UndefinedComparison,
    UndefinedEnvironmentName,
    Variable,
    _evaluate_markers,
    _format_marker,
    default_environment,
)
from packaging.markers import Marker as _Marker
from packaging.requirements import Requirement as _Requirement

from .misc import norm_name

LOGGER = logging.getLogger(__name__)
P_NEG = re.compile('\s*\-f\s+http[^\s]+')


class Marker(_Marker):
    def __init__(self) -> None:
        self._markers = []

    def evaluate(self, environment=None):
        builtin_environment = default_environment()
        current_environment = {**os.environ, **builtin_environment}
        if environment is not None:
            current_environment.update(environment)
        current_environment['extra'] = current_environment.get('extra', '')
        markers = _markers_strip_doller_sign(self._markers)
        return _evaluate_markers(markers._markers, current_environment)

    def __str__(self):
        return _format_marker(self._markers or [])


class Requirement(_Requirement):
    def __init__(self, requirement_string: str) -> None:
        self.requirement_string = self._parse_requirements(requirement_string)
        super().__init__(self.requirement_string)
        if self.marker:
            self.marker = _markers_value_to_variable(self.marker._markers)

    def _parse_requirements(self, line):
        if ' #' in line:
            line = line[:line.find(' #')]
        return line

    @property
    def key(self):
        return norm_name(self.name)

    def is_markers_matching(self):
        return filter_requirement(self) is not None

    def __repr__(self) -> str:
        return self.requirement_string


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


def _markers_value_to_variable(markers, marker: Marker = None):
    def to_variable(item):
        if item.__class__.__name__ == 'Value':
            if '$' in item.value:
                return Variable(item.value)
        return item

    is_top = marker is None
    marker = marker or Marker()
    clz = type(markers)

    if len(markers) != 3:
        for _markers in markers:
            if isinstance(_markers, str):
                marker._markers.append(_markers)
            else:
                _markers_value_to_variable(_markers, marker)

    else:
        lhs, op, rhs = markers
        _markers = clz([to_variable(lhs), op, to_variable(rhs)])
        if is_top:
            marker._markers = _markers
        else:
            marker._markers.append(_markers)
    return marker


def _markers_strip_doller_sign(markers, marker: Marker = None):
    def strip_doller_sign(item):
        if item.__class__.__name__ != 'Variable':
            return item
        return Variable(item.value.strip('$'))

    is_top = marker is None
    marker = marker or Marker()
    clz = type(markers)

    if len(markers) != 3:
        for _markers in markers:
            if isinstance(_markers, str):
                marker._markers.append(_markers)
            else:
                _markers_strip_doller_sign(_markers, marker)

    else:
        lhs, op, rhs = markers
        _markers = clz([strip_doller_sign(lhs), op, strip_doller_sign(rhs)])
        if is_top:
            marker._markers = _markers
        else:
            marker._markers.append(_markers)
    return marker
