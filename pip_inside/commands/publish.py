import configparser
import os
from types import SimpleNamespace
from urllib.parse import urlparse

import click
import requests
from flit_core.common import Metadata
from InquirerPy import inquirer

from pip_inside import Aborted
from pip_inside.utils import spinner

from .build import build_package

PYPI = 'https://upload.pypi.org/legacy/'
TESTPYPI = 'https://test.pypi.org/legacy/'
PYPI_URLS = {
    '': PYPI,
    None: PYPI,
    'pypi': PYPI,
    'testpypi': TESTPYPI,
}
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
    credential = get_credential_from_pypirc(repository, config_file, interactive)
    pkg = build_package(dist)
    upload_to_repository(pkg, credential)


def get_credential_from_pypirc(repository: str, config_file: str = '~/.pypirc', interactive: bool = False):
    cp = configparser.ConfigParser()
    config_file = os.path.expanduser(config_file)
    cp.read(config_file)

    url = cp.get(repository, 'repository', fallback=None)
    if url is None:
        url = PYPI_URLS.get(repository, PYPI)
    if url.startswith(SWITCH_TO_HTTPS):
        url = 'https' + url[4:]
    if url.startswith('http://'):
        click.secho(f"Insecure repository: {url}, risk of leaking credentials", fg='yellow')

    username = cp.get(repository, 'username', fallback=None)
    password = cp.get(repository, 'password', fallback=None)

    credentials = SimpleNamespace(name=repository, url=url, username=username, password=password)
    check_credentials(credentials, config_file, interactive)
    return credentials


def check_credentials(credential, config_file: str, interactive: bool):
    if credential.username is None:
        if not interactive:
            raise Aborted(f"'username' expected in {config_file}")
        credential.username = inquirer.text(message='Username:', mandatory=True).execute().strip()

    if credential.password is None:
        if not interactive:
            raise Aborted(f"'password' expected in {config_file}")
        credential.username = inquirer.text(message='Password:', mandatory=True).execute().strip()


def upload_to_repository(pkg, credential):
    def upload(file, metadata: Metadata):
        with spinner.Spinner(f"Uploading {file.name} to {credential.name}"):
            data = build_post_data(metadata, file.suffix)
            with file.open('rb') as f:
                content = f.read()
                files = {'content': (file.name, content)}
            resp = requests.post(credential.url, data=data, files=files, auth=(credential.username, credential.password))
            resp.raise_for_status()
    upload(pkg.wheel.file, pkg.wheel.builder.metadata)
    upload(pkg.sdist.file, pkg.sdist.builder.metadata)


def build_post_data(metadata: Metadata, ext: str):
    params_of_ext = {
        '.whl': {'filetype': 'bdist_wheel', 'pyversion': 'py3'},
        '.gz': {'filetype': 'sdist'}
    }
    params_general = {
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
    }
    params = {**params_of_ext.get(ext), **params_general}
    return {k: v for k, v in params.items() if v}


def get_published_url(url, name):
    if url.endswith('/legacy/'):
        domain = urlparse(url).netloc
        if domain.startswith('upload.'):
            domain = domain[7:]
        return f"https://{domain}/project/{name}/"
    return f"{url}/{name}"
