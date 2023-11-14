import os
import re
from datetime import datetime

P_HAS_VERSION_SPECIFIERS = re.compile('(?:===|~=|==|!=|<=|>=|<|>)')
URL_VERSION_SPECIFIERS = 'https://peps.python.org/pep-0440/#version-specifiers'

P_KV_SEP = re.compile('\s*=\s*')


def has_ver_spec(name: str):
    return P_HAS_VERSION_SPECIFIERS.search(name) is not None


def norm_name(name: str):
    return name.lower().replace('_', '-') if name else None


def norm_module(name: str):
    return name.lower().replace('-', '_') if name else None


def is_in_container():

    def is_container_env():
        return os.path.exists('/.dockerenv')

    def is_container_cgroup():
        paths = ['/proc/self/cgroup', '/proc/1/cgroup']
        for path in paths:
            if not os.path.exists(path):
                continue

            with open(path, 'r') as f:
                for line in f:
                    if 'docker' in line or '0::/' == line:
                        return True
        return False

    def is_conatainer_sched():
        path = '/proc/1/sched'
        if not os.path.exists(path):
            return False

        with open(path, 'r') as f:
            line = f.readline()
            return 'init' not in line and 'systemd' not in line

    return is_container_env() or is_container_cgroup() or is_conatainer_sched()


def formatted_date(date_str, fmt='%Y-%m-%d %H:%M:%S'):
    try:
        return datetime.fromisoformat(date_str).strftime(fmt)
    except Exception:
        return date_str


is_in_docker = is_in_container
