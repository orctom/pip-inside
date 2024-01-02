import hashlib
import io
import os
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Optional

import click
from flit_core.common import Metadata, Module, get_info_from_module
from flit_core.config import pep621_allowed_fields, read_flit_config
from flit_core.sdist import SdistBuilder
from flit_core.wheel import WheelBuilder

from pip_inside.utils.pyproject import PyProject


def make_metadata(module, ini_info, extra_meta):
    metadata = {'name': module.name, 'provides': [module.name]}
    metadata.update(get_info_from_module(module, ini_info.dynamic_metadata))
    metadata.update(ini_info.metadata)
    if extra_meta:
        metadata.update(extra_meta)
    return Metadata(metadata)


class PiWheelBuilder(WheelBuilder):

    @classmethod
    def build_wheel(cls, config_path: Path, dist_path: Path, extra_meta: Optional[dict] = None):
        def create_builder(target_fp):
            directory = config_path.parent
            ini_info = read_flit_config(config_path)
            entrypoints = ini_info.entrypoints
            module = Module(ini_info.module, directory)
            metadata = make_metadata(module, ini_info, extra_meta)
            return cls(
                directory, module, metadata, entrypoints, target_fp, ini_info.data_directory
            )
        (fd, temp_path) = tempfile.mkstemp(suffix='.whl', dir=str(dist_path))
        try:
            with io.open(fd, 'w+b') as fp:
                wb = create_builder(fp)
                wb.build(False)

            wheel_path = dist_path / wb.wheel_filename
            os.replace(temp_path, str(wheel_path))
        except:
            os.unlink(temp_path)
            raise

        return SimpleNamespace(builder=wb, file=wheel_path)


class PiSdistBuilder(SdistBuilder):

    @classmethod
    def build_sdist(cls, config_path: Path, dist_path: Path, extra_meta: Optional[dict] = None):

        def create_builder():
            ini_info = read_flit_config(config_path)
            srcdir = config_path.parent
            module = Module(ini_info.module, srcdir)
            metadata = make_metadata(module, ini_info, extra_meta)
            extra_files = [config_path.name] + ini_info.referenced_files
            return cls(
                module, metadata, srcdir, ini_info.reqs_by_extra,
                ini_info.entrypoints, extra_files, ini_info.data_directory,
                ini_info.sdist_include_patterns, ini_info.sdist_exclude_patterns,
            )

        builder = create_builder()
        sdist_file = builder.build(dist_path, gen_setup_py=False)
        return SimpleNamespace(builder=builder, file=sdist_file)


def handle_build(dist: str = 'dist'):
    click.secho(f"Building wheel and sdist to: {dist}", fg='bright_cyan')
    pkg = build_package(dist)

    wheel_name, sdist_name = str(pkg.wheel.file), str(pkg.sdist.file)
    pad_size = max(len(wheel_name), len(sdist_name)) + 1
    click.secho(f"Build {wheel_name: <{pad_size}} md5: {pkg.wheel_md5}, size: {pkg.wheel_size}", fg='green')
    click.secho(f"Build {sdist_name: <{pad_size}} md5: {pkg.sdist_md5}, size: {pkg.sdist_size}", fg='green')


def build_package(path_dist: str):
    os.makedirs('dist', exist_ok=True)
    pyproject = PyProject.from_toml()
    path_toml, path_dist = Path('pyproject.toml'), Path(path_dist)
    extra_meta = {
        'author': ','.join([author.get('name') for author in pyproject.get('project.authors')]),
        'license': pyproject.get('tool.pi.license-expression'),
        'home_page': pyproject.get('project.urls.homepage'),
    }

    pep621_allowed_fields.add('license-expression')
    wheel_info = PiWheelBuilder.build_wheel(path_toml, path_dist, extra_meta)
    sdist_info = PiSdistBuilder.build_sdist(path_toml, path_dist, extra_meta)

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
