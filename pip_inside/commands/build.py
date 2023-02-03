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

    md5_wheel = hashlib.md5(open(pkg.wheel.file, 'rb').read()).hexdigest()
    md5_sdist = hashlib.md5(open(pkg.sdist.file, 'rb').read()).hexdigest()
    wheel_name, sdist_name = str(pkg.wheel.file), str(pkg.sdist.file)
    pad_size = max(len(wheel_name), len(sdist_name)) + 1
    click.secho(f"Build {wheel_name: <{pad_size}} (md5: {md5_wheel})", fg='green')
    click.secho(f"Build {sdist_name: <{pad_size}} (md5: {md5_sdist})", fg='green')


def build_package(dist):
    dist = Path(dist)
    sb = SdistBuilder.from_ini_path(Path('pyproject.toml'))
    sdist_file = sb.build(dist, gen_setup_py=False)
    sdist_info = SimpleNamespace(builder=sb, file=sdist_file)
    with unpacked_tarball(sdist_file) as tmpdir:
        tmp_ini_file = Path(tmpdir, 'pyproject.toml')
        wheel_info = make_wheel_in(tmp_ini_file, dist)
    return SimpleNamespace(wheel=wheel_info, sdist=sdist_info)


@contextmanager
def unpacked_tarball(path):
    tf = tarfile.open(str(path))
    with TemporaryDirectory() as tmpdir:
        tf.extractall(tmpdir)
        files = os.listdir(tmpdir)
        assert len(files) == 1, files
        yield os.path.join(tmpdir, files[0])
