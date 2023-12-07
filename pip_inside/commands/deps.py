from typing import Optional
from pip_inside.utils.dependencies import Dependencies


def handle_deps(unused: bool, search: Optional[str] = None):
    Dependencies().print_non_dependencies(search) if unused else Dependencies().print_dependencies(search)
