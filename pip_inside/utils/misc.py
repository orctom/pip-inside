import re

P_HAS_VERSION_SPECIFIERS = re.compile('(?:===|~=|==|!=|<=|>=|<|>)')
URL_VERSION_SPECIFIERS = 'https://peps.python.org/pep-0440/#version-specifiers'

P_KV_SEP = re.compile('\s*=\s*')


def has_ver_spec(name: str):
    return P_HAS_VERSION_SPECIFIERS.search(name) is not None


def norm_name(name: str):
    return name.lower().replace('_', '-') if name else None


def norm_module(name: str):
    return name.lower().replace('-', '_') if name else None
