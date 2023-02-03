import collections
import re
import subprocess
import sys
from datetime import datetime
from typing import Union

import requests

try:
    from importlib.metadata import PackageNotFoundError, distribution
except ImportError:
    from pkg_resources import DistributionNotFound as PackageNotFoundError
    from pkg_resources import get_distribution as distribution


API_URL = "https://pypi.org/search/?q={query}"
DATE_FORMAT = '%Y-%m-%d'

P_NAME = re.compile(r"<span class=\"package-snippet__name\">(.+)</span>")
P_VERSION = re.compile(r".*<span class=\"package-snippet__version\">(.+)</span>")
P_RELEASE = re.compile(r"<time\s+datetime=\"([^\"]+)\"")
P_DESCRIPTION = re.compile(r".*<p class=\"package-snippet__description\">(.+)</p>")

P_INDEX_VERSIONS = re.compile('(?<=Available versions:)([a-zA-Z0-9., ]+)(?=\\n)')


def check_version(package_name: str) -> Union[str, bool]:
    try:
        installed = distribution(package_name)
    except PackageNotFoundError:
        return False
    else:
        return installed.version


def search(name: str):
    url = API_URL.format(query=name)
    page_data = requests.get(url=url).text
    names = P_NAME.findall(page_data)
    versions = P_VERSION.findall(page_data)
    releases = P_RELEASE.findall(page_data)
    descriptions = P_DESCRIPTION.findall(page_data)
    releases = [
        datetime.strptime(release, "%Y-%m-%dT%H:%M:%S%z").strftime(DATE_FORMAT)
        for release in releases
    ]

    n_n = max(map(len, names)) + 1
    n_v = max(map(len, versions)) + 1
    n_r = max(map(len, releases)) + 1
    n_d = max(map(len, descriptions)) + 1

    fmt = lambda n, v, r, d: f"{n: <{n_n}} {v: <{n_v}} {r: <{n_r}} {d: <{n_d}}"
    pkg = collections.namedtuple('pkg', ['name', 'desc'])

    return [
        pkg(name, fmt(name, version, release, desc))
        for name, version, release, desc in zip(names, versions, releases, descriptions)
    ]


def versions(name: str):
    try:
        cmd = [sys.executable, '-m', 'pip', 'index', 'versions', name]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = process.communicate()
        m = P_INDEX_VERSIONS.search(out.decode())
        if m is None:
            return None
        return [v.strip() for v in m.group().strip().split(',')]
    except subprocess.CalledProcessError:
        pass
