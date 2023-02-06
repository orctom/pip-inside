import hashlib
import os
import tarfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import click
from flit_core.sdist import SdistBuilder
from flit_core.wheel import make_wheel_in


def handle_build(dist: str = 'dist'):
    click.secho(f"Building wheel and sdist to: {dist}", fg='cyan')
    pkg = build_package(dist)

    wheel_name, sdist_name = str(pkg.wheel.file), str(pkg.sdist.file)
    pad_size = max(len(wheel_name), len(sdist_name)) + 1
    click.secho(f"Build {wheel_name: <{pad_size}} md5: {pkg.wheel_md5}, size: {pkg.wheel_size}", fg='green')
    click.secho(f"Build {sdist_name: <{pad_size}} md5: {pkg.sdist_md5}, size: {pkg.sdist_size}", fg='green')


def build_package(dist):
    dist = Path(dist)
    sb = SdistBuilder.from_ini_path(Path('pyproject.toml'))
    sdist_file = sb.build(dist, gen_setup_py=False)
    sdist_info = SimpleNamespace(builder=sb, file=sdist_file)
    with unpacked_tarball(sdist_file) as tmpdir:
        tmp_ini_file = Path(tmpdir, 'pyproject.toml')
        wheel_info = make_wheel_in(tmp_ini_file, dist)
    
    wheel_data, sdist_data = open(wheel_info.file, 'rb').read(), open(sdist_info.file, 'rb').read()
    wheel_md5 = hashlib.md5(wheel_data).hexdigest()
    wheel_sha256 = hashlib.sha256(wheel_data).hexdigest()
    wheel_size = get_file_size(wheel_info.file)
    sdist_md5 = hashlib.md5(sdist_data).hexdigest()
    sdist_sha256 = hashlib.sha256(sdist_data).hexdigest()
    sdist_size = get_file_size(sdist_info.file)
    return SimpleNamespace(
        wheel=wheel_info,
        wheel_md5=wheel_md5,
        wheel_sha256=wheel_sha256,
        wheel_size=wheel_size,
        sdist=sdist_info,
        sdist_md5=sdist_md5,
        sdist_sha256=sdist_sha256,
        sdist_size=sdist_size,
    )


@contextmanager
def unpacked_tarball(path):
    tf = tarfile.open(str(path))
    with TemporaryDirectory() as tmpdir:
        tf.extractall(tmpdir)
        files = os.listdir(tmpdir)
        assert len(files) == 1, files
        yield os.path.join(tmpdir, files[0])


def get_file_size(filename: str) -> str:
    file_size = os.path.getsize(filename) / 1024
    size_unit = "KB"

    if file_size > 1024:
        file_size = file_size / 1024
        size_unit = "MB"

    return f"{file_size:.1f} {size_unit}"
