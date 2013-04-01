""" mirror_package
Pull packages from pypi.python.org and push them to your local DjangoPyPI server

Usage:
    mirror_package <package_name> [<distribution_type>] [<release_version>] [--recursive] [--index-server=<index-server>]

Options:
    <package_name>                    package to pull and push
    <distribution_type>               distribution type to push to your pypi server [default: sdist]
    <release_version>                 optional specific version to pull, else the latests on pypi.python.org
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
    from ..mirror import mirror_package
    index_server = arguments.get("--index-server")
    package_name = arguments.get("<package_name>")
    distribution_type = arguments.get("<distribution_type>")
    release_version = arguments.get("<release_version>")
    recursive = arguments.get("--recursive")
    mirror_package(package_name, distribution_type, release_version, index_server)
    if recursive:
        _recursive(package_name, distribution_type, release_version)


def _recursive(package_name, distribution_type, release_version):
    from ..recursive import virtualenv
    with virtualenv() as env:
        env.easy_install(package_name, release_version)
        for dependency in env.get_dependencies(package_name):
            mirror_package([dependency, distribution_type, env.get_installed_version(dependency)])
