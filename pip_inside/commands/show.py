from pip_inside.utils.dependencies import Dependencies


def handle_show(unused: bool):
    Dependencies().print_non_dependencies() if unused else Dependencies().print_dependencies()
