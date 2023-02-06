# pip-inside

I use `pip`, so I have `requirements.txt`, and `requirements-dev.txt` as well.

I started to configure mine `black`, `isort`, `pypy`..., so I have `pyproject.toml` later.

I wanted to move `requrements.txt` into `pyproject.toml`, as it's feature-rich, then I saw [poetry](https://python-poetry.org/).

I missed a lot about `pip`, as `poetry`:
 - sometimes slow, and sometimes quite slow
 - hash mismatch, then I have to delete my entire cache, and download everything again
 - when you have huge dependencies like `torch` (~2 GB), too bad to install a general version, then a working version in `toe` plugin

So this `pip-inside` comes out. It's just `flit` with `pip` as the dependency installer.

So it does NOT have these features (might add some of them later):
 - hash checking
 - version freezing
 - dependency tree


## install

```shell
# in each of your virtual env
pip install pip-inside
```

## commands

 - pip-inside
 - pi

```shell
pip-inside
Usage: pip-inside [OPTIONS] COMMAND [ARGS]...

Options:
  -V, --version  show version of this tool
  --help         Show this message and exit.

Commands:
  add      Add a package as project dependency
  build    Build the wheel and sdist
  init     Init project in current directory
  install  Install project dependencies by groups
  publish  Publish the wheel and sdist to remote repository
  remove   Remove a package from project dependencies
  version  Show version of current project
```
