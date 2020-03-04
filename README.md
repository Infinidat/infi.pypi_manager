Overview
========

A set of command-line scripts for copying Python packages from pypi.python.org to djangopypi servers.

Checking out the code
=====================

Run the following:

    easy_install -U infi.projector
    projector devenv build


Provides the following commands
===============================

Compares two repositories for changes between them (upgradable/downgradable packages):

    compare_pypi_repos <reference_repo> <other_repo>

Install (using easy_install) a package and its dependencies:

    hard_install <package_name>

Mirror a package and its distributable from pypi.python.org to local DjangoPyPI (based on .pypirc):

    mirror_package <package_name> [<release_version>] [--build=<distribution-type> [--use-download-url]] [--recursive] [--index-server=<index-server>]

Generate a dependency tree/list for a package:

    pydepends <package>
    pydepends <package> --tree
    pydepends <package> --licenses [--csv | --table]
    pydepends <package> --find=<dependency>

Pull source packages from your local DjangoPyPI server, build binary distributions and upload them back to the server:

    rebuild_package <package_name> [<release_version>] [--build=<distribution-type>] [--index-server=<index-server>]
