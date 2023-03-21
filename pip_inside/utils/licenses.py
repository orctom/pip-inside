"""
https://spdx.github.io/spdx-spec/v2.3/SPDX-license-list/
"""

from pathlib import Path

LICENSES = {
    'Apache-2.0': 'Apache License 2.0',
    'GPL-3.0-or-later': 'GNU General Public License v3.0 or later',
    'LGPL-3.0-or-later': 'GNU Lesser General Public License v3.0 or later',
    'MIT': 'MIT license',
    'MulanPSL-2.0': 'Mulan Permissive Software License, Version 2',
}


def get_file(license: str):
    return Path(__file__).parent / 'licenses' / f"{license}.txt"
