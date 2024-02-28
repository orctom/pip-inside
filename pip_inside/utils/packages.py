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

P_VERSIONS_FROM_INSTALL = re.compile('(?<=from versions:)([a-zA-Z0-9., ]+)')
HINT_QUIT = '(press "q" to quit)'


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
            if pkgs is None:
                click.secho(f"No packages found by name '{name}'", fg='cyan')
                continue
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
            info = pkg_info.get('info')
            releases = {version: dists[0] for version, dists in pkg_info.get('releases').items() if dists and not dists[0].get('yanked')}
            releases_recent = '\n'.join([
                f" - {version: <10} ({misc.formatted_date(dist.get('upload_time'), DATE_FORMAT)})"
                for version, dist in list(sorted(releases.items(), key=lambda d: d[1].get('upload_time'), reverse=True))[:50]
            ])
            url = info.get('home_page') or (info.get('project_urls') or {}).get('Homepage') or ''
            deps = '\n'.join([f" - {dep}" for dep in info.get('requires_dist') or [] if 'extra' not in dep])
            pkg_descriptions = (
                f"{colored(f'[{name}] {HINT_QUIT}')}\n\n"
                f"{colored('Summary')}        : {info.get('summary')}\n"
                f"{colored('URL')}            : {url}\n"
                f"{colored('Python Version')} : {info.get('requires_python')}\n"
                f"{colored('Dependencies')}   :\n{deps}\n\n"
                f"{colored('Recent Releases')}:\n{releases_recent}\n\n"
                f"{colored('Description')}    :\n{info.get('description')}\n"
            )
            click.echo_via_pager(pkg_descriptions)
        finally:
            continued = True
            name = None


def show_versions(name: str):
    msg = f"Fetching package info for {name}"
    with spinner.Spinner(msg):
        pkg_info = meta_from_pypi(name)
    if not pkg_info:
        click.secho('Failed to fetch version list', fg='cyan')
        return
    releases = {version: dists[0] for version, dists in pkg_info.get('releases').items() if dists and not dists[0].get('yanked')}
    releases_recent = '\n'.join([
        f" - {version: <10} ({misc.formatted_date(dist.get('upload_time'), DATE_FORMAT)})"
        for version, dist in list(sorted(releases.items(), key=lambda d: d[1].get('upload_time'), reverse=True))
    ])
    click.echo_via_pager(f"{colored(f'Releases {HINT_QUIT}')}:\n{releases_recent}\n")


def prompt_a_package(continued: bool = False):
    prompt = 'Add aother package (leave blank to exit):' if continued else 'Add a package (leave blank to exit):'
    pkgs = None
    while pkgs is None:
        name = inquirer.text(message=prompt).execute()
        if not name:
            return

        with spinner.Spinner(f"Searching for {name}"):
            pkgs = search(name)
        if pkgs is None:
            click.secho(f"No packages found by name '{name}'", fg='cyan')
            continue
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
                choices=['[set manually]'] + sorted(versions, reverse=True),
                vi_mode=True,
                wrap_lines=True,
                mandatory=True,
            ).execute()
            if version == '[set manually]':
                version = inquirer.text(message="Version:", completer={v: None for v in versions}).execute().strip()
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


def search(name: str, retries: int = 3):
    def fmt(n, v, r, d):
        return f"{n: <{n_n}} {v: <{n_v}} {r: <{n_r}} {d: <{n_d}}"

    url = API_URL.format(query=name)
    for i in range(retries):
        try:
            r = requests.get(url, timeout=(2, .5))
            r.raise_for_status()
            page_data = r.text
            names = P_NAME.findall(page_data)
            if len(names) == 0:
                return None
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

            pkg = collections.namedtuple('pkg', ['name', 'desc'])

            return [
                pkg(name, fmt(name, version, release, desc))
                for name, version, release, desc in zip(names, versions, releases, descriptions)
            ]
        except Exception as e:
            if i + 1 == retries:
                raise e
            continue


def fetch_versions(name: str):
    return versions_by_pip_install(name) or versions_from_pypi(name)


def versions_by_pip_install(name: str):
    try:
        cmd = [shutil.which('python'), '-m', 'pip', 'install', '--use-deprecated=legacy-resolver', f"{name}=="]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = process.communicate()
        m = P_VERSIONS_FROM_INSTALL.search(err.decode())
        if m is None:
            return None
        return [v.strip() for v in m.group().strip().split(',')]
    except subprocess.CalledProcessError:
        return None


def versions_from_pypi(name: str):
    try:
        pkg_info = meta_from_pypi(name)
        if not pkg_info:
            return None
        releases = {version: dists[0] for version, dists in pkg_info.get('releases').items() if dists and not dists[0].get('yanked')}
        return [
            version
            for version, _ in list(sorted(releases.items(), key=lambda d: d[1].get('upload_time'), reverse=True))
        ]
    except Exception:
        return None


def meta_from_pypi(name: str, retries: int = 3):
    url = f"https://pypi.org/pypi/{name}/json"
    headers = {'Accept': 'application/json'}
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=(2, .5))
            r.raise_for_status()
            if r.text is None or len(r.text) < 10:
                return None
            return r.json()
        except Exception as e:
            if i + 1 == retries:
                raise e
            continue
    return None


def colored(text, color='blue'):
    return click.style(text, fg=color)
