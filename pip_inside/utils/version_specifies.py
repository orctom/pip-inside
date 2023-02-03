import re

P_VERSION_HAS_SPECIFIERS = re.compile('^[a-zA-Z0-9_.-]+\s*(?=(?:===|~=|==|!=|<=|>=|<|>))')
P_HAS_VERSION_SPECIFIERS = re.compile('(?:===|~=|==|!=|<=|>=|<|>)')
P_NORMALIZE = re.compile('^[a-zA-Z0-9_.-]+\s*(?=(?:===|~=|==|!=|<=|>=|<|>)?\s*;?)')
URL_VERSION_SPECIFIERS = 'https://peps.python.org/pep-0440/#version-specifiers'


def ver_has_spec(name: str):
    return P_VERSION_HAS_SPECIFIERS.search(name) is not None


def has_ver_spec(name: str):
    return P_HAS_VERSION_SPECIFIERS.search(name) is not None


def get_package_name(name: str):
    return P_NORMALIZE.search(name).group()
