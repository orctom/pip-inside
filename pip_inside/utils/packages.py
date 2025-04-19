import click
import requests

from . import misc, spinner

DATE_FORMAT = '%Y-%m-%d'
HINT_QUIT = '(press "q" to quit)'


def show_info(name: str):
    msg = f"Fetching package info for {name}"
    with spinner.Spinner(msg):
        pkg_info = meta_from_pypi(name)
    if not pkg_info:
        click.secho('Failed to fetch version list', fg='cyan')
        return
    _print_pkg_info(name, pkg_info)


def _print_pkg_info(name: str, pkg_info: dict):
    info = pkg_info.get('info')
    releases = {version: dists[0] for version, dists in pkg_info.get('releases').items() if dists and not dists[0].get('yanked')}
    releases_recent = '\n'.join([
        f" - {version: <11} ({misc.formatted_date(dist.get('upload_time'), DATE_FORMAT)})"
        for version, dist in list(sorted(releases.items(), key=lambda d: d[1].get('upload_time'), reverse=True))[:50]
    ])
    url = info.get('home_page') or (info.get('project_urls') or {}).get('Homepage') or ''
    deps_group = misc.group_by_extras(info.get('requires_dist'))
    pad_size = max([len(k) for k in list(deps_group)] + [11]) + 1
    dependencies = '\n'.join([f" - {dep}" for dep in deps_group.get('') or []])
    dependencies_extras = '\n'.join([f" - {extra: <{pad_size}}:{', '.join(deps)}" for extra, deps in deps_group.items() if extra])

    pkg_descriptions = (
        f"{colored(f'[{name}] {HINT_QUIT}')}\n\n"
        f"{colored('Summary')}        : {info.get('summary')}\n"
        f"{colored('URL')}            : {url}\n"
        f"{colored('Python Version')} : {info.get('requires_python')}\n"
        f"{colored('Dependencies')}   :\n{dependencies}\n\n"
        f"{colored('Extras')}         :\n{dependencies_extras}\n\n"
        f"{colored('Recent Releases')}:\n{releases_recent}\n\n"
        f"{colored('Description')}    :\n{info.get('description')}\n"
    )
    click.echo_via_pager(pkg_descriptions)


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
