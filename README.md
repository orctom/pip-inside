# pip-inside

I use `pip`, so I have `requirements.txt`, and might `requirements-dev.txt` as well.

Later when I started to configure my `black`, `isort`, `pypy`..., I have `pyproject.toml`.

Then I  wanted to move `requrements.txt` into `pyproject.toml`, as it's feature-rich, then I saw [poetry](https://python-poetry.org/).

After used poetry for months, I started to missing `pip`, as `poetry`:
 - sometimes slow, and sometimes quite slow
 - hash mismatch, then I have to delete my entire cache, and download everything again
 - when you have huge dependencies like `torch` (~2 GB), too bad to install a general version, then a working version later in `toe` plugin

So this `pip-inside` comes out. It's just `flit-core` with `pip` as the dependency installer.


**NOTICES**:

Only supports:
 - dynamic `version` (`__version__ = 'your version'` in {root_module}/__init__.py)
 - non-dynamic `description` (in `pyproject.toml`)
 - no `src` folder in project root
 - virtualenv folder named `.venv` in project root
 - not checking hashes


## install

```shell
# in each of your virtual env
pip install pip-inside
```

## commands

 - pip-inside
 - pi

```shell
pi
Usage: pi [OPTIONS] COMMAND [ARGS]...

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
