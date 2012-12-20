""" mirror_package

Usage:
    mirror_package <package_name> <distribution_type> [<release_version>] [--recursive]

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
    from .. import download_package_from_global_pypi
    from .. import upload_package_to_local_pypi
    from .. import extract_source_package_to_tempdir, chdir
    package_name = arguments.get("<package_name>")
    distribution_type = arguments.get("<distribution_type>")
    release_version = arguments.get("<release_version>")
    recursive = arguments.get("--recursive")
    package_source_archive = download_package_from_global_pypi(package_name, release_version)
    package_dir = extract_source_package_to_tempdir(package_source_archive)
    with chdir(package_dir):
        pass
        upload_package_to_local_pypi(distribution_type)
    if recursive:
        _recursive(package_name, distribution_type, release_version)


def _recursive(package_name, distribution_type, release_version):
    from ..recursive import virtualenv
    with virtualenv() as env:
        env.easy_install(package_name, release_version)
        for dependency in env.get_dependencies(package_name):
            mirror_package([dependency, distribution_type, env.get_installed_version(dependency)])

