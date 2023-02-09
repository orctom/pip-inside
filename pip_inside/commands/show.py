from pip_inside.utils.dependencies import Package


def handle_show(unused: bool):
    pkg = Package.from_unused() if unused else Package.from_project()
    pkg.print_dependencies()
