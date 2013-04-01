""" mirror_package
Pull packages from pypi.python.org and push them to your local DjangoPyPI server

Usage:
    mirror_package <package_name> [<release_version>] [--build=<distribution-type>] [--recursive] [--index-server=<index-server>]

Options:
    <package_name>                    package to pull and push
    <release_version>                 optional specific version to pull, else the latests on pypi.python.org
    --build=<distribution-type>       manually download and build specific distribution of package
    --index-server=<index-server>     local index server from ~/.pypirc to push the package to [default: local]
    --recursive                       recursively mirror all the dependencies
    --help                            show this screen
    --version                         show version
"""

import sys


def mirror_package(argv=sys.argv[1:]):
    from docopt import docopt
    from ..__version__ import __version__
    arguments = dict(docopt(__doc__, argv=argv, help=True, version=__version__))
    _logging()
    _mirror_package(arguments)


def _logging():
    from logging import basicConfig, DEBUG
    basicConfig(stream=sys.stdout, level=DEBUG)


def _mirror_package(arguments):
    index_server = arguments.get("--index-server")
    package_name = arguments.get("<package_name>")
    distribution_type = arguments.get("<distribution_type>")
    release_version = arguments.get("<release_version>")
    distribution_type = arguments.get("--build")
    recursive = arguments.get("--recursive")
    if distribution_type is not None:
        from ..mirror_build import mirror_package
        mirror_package(package_name, distribution_type, release_version, index_server)
    else:
        from ..mirror_all import mirror_package
        mirror_package(index_server, package_name, release_version)
    if recursive:
        _recursive(package_name, release_version, arguments)


def _recursive(package_name, release_version, arguments):
    from ..recursive import virtualenv
    with virtualenv() as env:
        env.easy_install(package_name, release_version)
        for dependency in env.get_dependencies(package_name):
            arguments['<package_name>'] = dependency
            arguments['<release_version>'] = env.get_installed_version(dependency)
            arguments['--recursive'] = None
            _mirror_package(arguments)
