import configparser
import os
from types import SimpleNamespace
from urllib.parse import urlparse

import click
from flit_core.common import Metadata
from InquirerPy import inquirer

from .build import build_package

PYPI = 'https://upload.pypi.org/legacy/'
SWITCH_TO_HTTPS = (
    "http://pypi.python.org/",
    "http://testpypi.python.org/",
    "http://upload.pypi.org/",
    "http://upload.pypi.io/",
)


def handle_publish(
    repository: str = 'pypi',
    *,
    dist: str = 'dist',
    config_file: str = '~/.pypirc',
    interactive: bool = False
):
    click.echo('publish')

    credential = get_credential_from_pypirc(repository, config_file)
    check_credentials(credential, config_file, interactive)

    pkg = build_package(dist)




def get_credential_from_pypirc(repository: str, config_file: str = '~/.pypirc'):
    cp = configparser.ConfigParser()
    config_file = os.path.expanduser(config_file)
    cp.read(config_file)

    url = cp.get(repository, 'repository', fallback=PYPI)
    if url.startswith(SWITCH_TO_HTTPS):
        url = 'https' + url[4:]
    if url.startswith('http://'):
        click.secho(f"Insecure repository: {url}, risk of leaking credentials", fg='yellow')

    return SimpleNamespace(
        url = url,
        username = cp.get(repository, 'username', fallback=None),
        password = cp.get(repository, 'password', fallback=None)
    )


def check_credentials(credential, config_file: str, interactive: bool):
    if credential.username is None:
        if not interactive:
            click.secho(f"'username' expected in {config_file}", fg='yellow')
        else:
            credential.username = inquirer.text(message='Username:', mandatory=True).execute().strip()

    if credential.password is None:
        if not interactive:
            click.secho(f"'password' expected in {config_file}", fg='yellow')
        else:
            credential.username = inquirer.text(message='Password:', mandatory=True).execute().strip()


def get_published_url(url, name):
    if url.endswith('/legacy/'):
        domain = urlparse(url).netloc
        if domain.startswith('upload.'):
            domain = domain[7:]
        return f"https://{domain}/project/{name}/"
    return f"{url}/{name}"


def build_post_data(metadata: Metadata):
    params = {
        ':action': '',
        'name': metadata.name,
        'version': metadata.version,
        'metadata_version': '2.1',
        'summary': metadata.summary,
        'home_page': metadata.home_page,
        'author': metadata.author,
        'author_email': metadata.author_email,
        'maintainer': metadata.maintainer,
        'maintainer_email': metadata.maintainer_email,
        'license': metadata.license,
        'description': metadata.description,
        'keywords': metadata.keywords,
        'platform': metadata.platform,
        'classifiers': metadata.classifiers,
        'download_url': metadata.download_url,
        'supported_platform': metadata.supported_platform,
        # Metadata 1.1 (PEP 314)
        'provides': metadata.provides,
        'requires': metadata.requires,
        'obsoletes': metadata.obsoletes,
        # Metadata 1.2 (PEP 345)
        'project_urls': metadata.project_urls,
        'provides_dist': metadata.provides_dist,
        'obsoletes_dist': metadata.obsoletes_dist,
        'requires_dist': metadata.requires_dist,
        'requires_external': metadata.requires_external,
        'requires_python': metadata.requires_python,
        # Metadata 2.1 (PEP 566)
        'description_content_type': metadata.description_content_type,
        'provides_extra': metadata.provides_extra,

        'protocol_version': 2,
        'filetype': ''
    }
    return {k: v for k, v in params.items() if v}
