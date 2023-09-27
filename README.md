# pip-inside

Like [poetry](https://python-poetry.org/), but using `pip` to maintain dependencies.

Using `flit-core` as the `build-backend`.


**CONVENSIONS**:

 - dynamic `version` (`__version__ = 'your version'` in `{root_module}/__init__.py`)
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
> pi
Usage: pi [OPTIONS] COMMAND [ARGS]...

Options:
  -V, --version  show version of this tool
  --help         Show this message and exit.

Commands:
  add      Add a package as project dependency
  build    Build the wheel and sdist
  init     Init project in current directory
  install  Install project dependencies by groups
  lock     Create or update version lock file 'pi.lock'
  publish  Publish the wheel and sdist to remote repository
  remove   Remove a package from project dependencies
  search   Search a package from remote pypi
  shell    Ensure '.venv' virtualenv, and new shell into it
  show     Show dependency tree
  upgrade  Upgrade pip-inside and pip as well
  version  Show version of current project
```
