"""rebuild_package
Pull source packages from your local DjangoPyPI server, build binary distributions and upload them back to the server

Usage:
    rebuild_package <package_name> [<release_version>] [--build=<distribution-type>] [--index-server=<index-server>]

Options:
    <package_name>                    package to pull and push
    <release_version>                 optional specific version to pull, else the latests on pypi.python.org
    --build=<distribution-type>       manually download and build specific distribution of package [default: bdist_egg]
    --index-server=<index-server>     local index server from ~/.pypirc to push the package to [default: local]
    --help                            show this screen
    --version                         show version
"""

import sys


def rebuild_package(argv=sys.argv[1:]):
    from docopt import docopt
    from ..__version__ import __version__
    arguments = dict(docopt(__doc__, argv=argv, help=True, version=__version__))
    _logging()
    _rebuild_package(arguments)


def _logging():
    from logging import basicConfig, DEBUG
    basicConfig(stream=sys.stdout, level=DEBUG)


def _rebuild_package(arguments):
    from .mirror_build import rebuild_package_binary_distributions
    index_server = arguments.get("--index-server")
    package_name = arguments.get("<package_name>")
    release_version = arguments.get("<release_version>")
    distribution_type = arguments.get("--build")
    rebuild_package_binary_distributions(index_server, package_name, release_version)
