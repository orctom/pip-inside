import collections
import re
import shutil
import subprocess
from datetime import datetime
from typing import Optional, Union

import click
import requests
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from . import misc, spinner

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

P_INDEX_VERSIONS = re.compile('(?<=Available versions:)([a-zA-Z0-9., ]+)')


def prompt_searches(name: Optional[str] = None):
    continued = False
    while True:
        try:
            if name is None:
                prompt = 'Search aother package (leave blank to exit):' if continued else 'Search a package (leave blank to exit):'
                name = inquirer.text(message=prompt).execute()
                if not name:
                    return

            with spinner.Spinner(f"Searching for {name}"):
                pkgs = search(name)
            name = inquirer.select(
                message="Select the package:",
                choices=[Choice(value=pkg.name, name=pkg.desc) for pkg in pkgs],
                vi_mode=True,
                wrap_lines=True,
                mandatory=True,
            ).execute()

            pkg_info = None
            trying, max_tries = 0, 3
            while not pkg_info:
                trying += 1
                msg = f"Fetching package info for {name}" if trying == 1 else f"Fetching package info for {name} ({trying} of {max_tries})"
                with spinner.Spinner(msg):
                    pkg_info = meta_from_pypi(name)
                    if pkg_info:
                        break
            if not pkg_info:
                click.secho('Failed to fetch version list', fg='cyan')
                return
            description = pkg_info.get('info').get('description')
            click.secho(description, fg='cyan')

        finally:
            continued = True
            name = None


def prompt_a_package(continued: bool = False):
    prompt = 'Add aother package (leave blank to exit):' if continued else 'Add a package (leave blank to exit):'
    name = inquirer.text(message=prompt).execute()
    if not name:
        return

    with spinner.Spinner(f"Searching for {name}"):
        pkgs = search(name)
    name = inquirer.select(
        message="Select the package:",
        choices=[Choice(value=pkg.name, name=pkg.desc) for pkg in pkgs],
        vi_mode=True,
        wrap_lines=True,
        mandatory=True,
    ).execute()

    with spinner.Spinner(f"Fetching version list for {name}"):
        versions = fetch_versions(name)
    if versions:
        version = inquirer.fuzzy(
            message="Select the version:",
            choices=['[set manually]'] + versions[:15],
            vi_mode=True,
            wrap_lines=True,
            mandatory=True,
        ).execute()
        if version == '[set manually]':
            version = inquirer.text(message="Version:", completer={v: None for v in versions[:15]}).execute().strip()
    else:
        click.secho('Failed to fetch version list, please set version menually', fg='cyan')
        version = inquirer.text(message="Version:").execute().strip()
    if version:
        name = f"{name}{version}" if misc.has_ver_spec(version) else f"{name}=={version}"
    return name


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


def fetch_versions(name: str):
    return versions_by_pip_index(name) or versions_by_json(name)


def versions_by_pip_index(name: str):
    try:
        cmd = [shutil.which('python'), '-m', 'pip', 'index', 'versions', name]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, _ = process.communicate()
        m = P_INDEX_VERSIONS.search(out.decode())
        if m is None:
            return None
        return [v.strip() for v in m.group().strip().split(',')]
    except subprocess.CalledProcessError:
        return None


def versions_by_json(name: str):
    try:
        data = meta_from_pypi(name)
        if not data:
            return None
        versions = list(data.get('releases').keys())
        versions.reverse()
        return versions
    except Exception:
        return None


def meta_from_pypi(name: str):
    try:
        headers = {'Accept': 'application/json'}
        r = requests.get(f"https://pypi.org/pypi/{name}/json", headers=headers)
        r.raise_for_status()
        if r.text is None or len(r.text) < 10:
            return None
        return r.json()
    except Exception as e:
        click.secho(f"Failed to fetch pckage info, due to: {e}", fg='yellow')
        return None
