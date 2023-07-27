import os
import re

P = re.compile(r'__version__\s*=\s*[\'\"]([a-z0-9.-]+)[\'\"]')


def get_version_from_init(filepath: str, silent: bool = False):
    text = open(filepath).read()
    m = P.search(text)
    if m is None:
        if silent:
            return None
        else:
            raise ValueError(f"'__version__' not defined in '{filepath}'")
    return m.groups()[0]


def set_version_in_init(filepath: str, version: str):
    version_line = f"__version__ = '{version}'\n"
    if os.path.exists(filepath):
        with open(filepath, 'a+') as f:
            f.seek(0)
            lines = f.readlines()
            add_version_line = True
            for i, line in enumerate(lines):
                m = P.search(line)
                if m is None:
                    continue
                add_version_line = False
                ver = m.groups()[0]
                if ver == version:
                    return
                lines[i] = version_line

            f.truncate(0)
            if add_version_line:
                i = _add_version_position(lines)
                lines.insert(i, version_line)
            for line in lines:
                f.write(line)
            return f"Updated {filepath}, version: {version}"
    else:
        with open(filepath, 'w') as f:
            f.write(version_line)
            return f"Added {filepath}, version: {version}"


def _add_version_position(lines: list):
    saw_contents = False
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            if not saw_contents:
                continue
            else:
                return i

        saw_contents = True
        if line.startswith('#'):
            continue
        return i
    return len(lines)
