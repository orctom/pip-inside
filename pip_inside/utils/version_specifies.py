import re

P_VERSION_SPECIFIERS = re.compile('^[a-zA-Z0-9_.-]+\s*(?=(?:===|~=|==|!=|<=|>=|<|>))')
P_NORMALIZE = re.compile('^[a-zA-Z0-9_.-]+\s*(?=(?:===|~=|==|!=|<=|>=|<|>)?\s*;?)')
URL_VERSION_SPECIFIERS = 'https://peps.python.org/pep-0440/#version-specifiers'


def has_version_specifier(name: str):
    return P_VERSION_SPECIFIERS.search(name) is not None


def get_package_name(name: str):
    return P_NORMALIZE.search(name).group()
