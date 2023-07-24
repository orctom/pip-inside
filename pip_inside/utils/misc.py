import os
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


def is_in_docker():

    def has_docker_env():
        return os.path.exists('/.dockerenv')

    def has_docker_cgroup():
        path = '/proc/self/cgroup'
        if not os.path.exists(path):
            return False
        with open(path, 'r') as f:
            for line in f:
                if 'docker' in line:
                    return True
        return False

    return has_docker_env() or has_docker_cgroup()
