import configparser
import os
from types import SimpleNamespace

import click
import requests
from flit_core.common import Metadata
from InquirerPy import inquirer

from pip_inside import Aborted
from pip_inside.utils import spinner

from .build import build_package

API_PYPI = 'https://upload.pypi.org/legacy/'
API_TESTPYPI = 'https://test.pypi.org/legacy/'
WEB_PYPI = "https://pypi.org/"
WEB_TESTPYPI = "https://test.pypi.org/"
NAME_TO_API = {
    '': API_PYPI,
    None: API_PYPI,
    'pypi': API_PYPI,
    'testpypi': API_TESTPYPI,
}
API_NORMALIZE = {
    "http://pypi.python.org/": API_PYPI,
    "https://pypi.python.org/": API_PYPI,
    "http://test.pypi.org/": API_TESTPYPI,
    "https://test.pypi.org/": API_TESTPYPI,
    "http://testpypi.python.org/": API_TESTPYPI,
    "https://testpypi.python.org/": API_TESTPYPI,
}
API_TO_WEB = {
    API_PYPI: WEB_PYPI,
    API_TESTPYPI: WEB_TESTPYPI
}


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
    url = NAME_TO_API.get(repository) if url is None else API_NORMALIZE.get(url, url)
    if url is None:
        raise Aborted(f"Missing key: 'repository' in '{repository}' section of '{config_file}'")

    if url.startswith('http://'):
        click.secho(f"Warning: insecure repository: {url}, has risk of credential leaking risk", fg='yellow')

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
    def upload(metadata: Metadata, file, md5_digest, sha256_digest):
        with spinner.Spinner(f"Uploading {file.name}"):
            data = build_post_data(metadata, file.suffix, md5_digest, sha256_digest)
            with file.open('rb') as f:
                content = f.read()
                files = {'content': (file.name, content)}
            resp = requests.post(credential.url, data=data, files=files, auth=(credential.username, credential.password))
            resp.raise_for_status()
    try:
        click.secho(f"Publishing to [{credential.name}] ({credential.url})", fg='bright_cyan')
        upload(pkg.wheel.builder.metadata, pkg.wheel.file, pkg.wheel_md5, pkg.wheel_sha256)
        upload(pkg.sdist.builder.metadata, pkg.sdist.file, pkg.sdist_md5, pkg.sdist_sha256)
        check_published_url(credential.url, pkg.wheel.builder.metadata)
    except requests.exceptions.HTTPError as e:
        import traceback
        click.secho(traceback.format_exc(), fg='red')
        raise Aborted(f"Failed to upload, {e}")


def build_post_data(metadata: Metadata, ext: str, md5_digest, sha256_digest):
    params_of_ext = {
        '.whl': {'filetype': 'bdist_wheel', 'pyversion': 'py3'},
        '.gz': {'filetype': 'sdist'}
    }
    params_general = {
        ':action': 'file_upload',
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

        'protocol_version': 1,
        'md5_digest': md5_digest,
        'sha256_digest': sha256_digest,
    }
    params = {**params_of_ext.get(ext), **params_general}
    return {k: v for k, v in params.items() if v}


def check_published_url(url, meta: Metadata):
    pypi_web = API_TO_WEB.get(url)
    if pypi_web:
        published_url = f"{pypi_web}project/{meta.name}/{meta.version}"
        click.secho(f"View at: {published_url}", fg='bright_cyan')
    click.secho('Done', fg='green')
