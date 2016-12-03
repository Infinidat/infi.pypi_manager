from __future__ import print_function

from .. import PyPI, DjangoPyPI, PackageNotFound
from prettytable import PrettyTable
from pkg_resources import parse_version, resource_filename
import requests
import re
try:
    from urlparse import unquote
except ImportError:
    # Python 3
    from urllib.parse import unquote

def get_versions_from_reference(reference_repo):
    reference_pypi_html = requests.get("{}/pypi".format(reference_repo.server)).text
    search_result = re.findall("""href=["'](?:/pypi/)?([^/]+)/([^/]+)/["']""", reference_pypi_html)
    return dict((k, unquote(v)) for k, v in search_result)

def get_skipped_packages():
    with open(resource_filename(__name__, "skipped_packages.txt"), "rb") as fd:
        return [line.strip() for line in fd.readlines()]

def compare_pypi_repos(reference_repo, other_repo):
    upgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    downgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    skipped_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    skipped_packages = get_skipped_packages()
    reference_repo_versions = get_versions_from_reference(reference_repo)
    packages_to_check = list(reference_repo_versions.keys())
    for name in sorted(packages_to_check):
        try:
            reference_repo_version = reference_repo_versions[name]
            other_repo_version = other_repo.get_latest_version(name)
        except PackageNotFound:
            continue
        if other_repo_version != reference_repo_version:
            if name in skipped_packages or any(x in other_repo_version for x in ['a', 'b', 'dev', 'post', 'rc']):
                skipped_table.add_row([name, reference_repo_version, other_repo_version])
            elif parse_version(reference_repo_version) < parse_version(other_repo_version):
                upgrade_table.add_row([name, reference_repo_version, other_repo_version])
            else:
                downgrade_table.add_row([name, reference_repo_version, other_repo_version])

    print("Upgradable Packages:")
    print(upgrade_table)
    print()
    print("Downgradable Packages:")
    print(downgrade_table)
    print()
    print("Skipped Packages:")
    print(skipped_table)

def main():
    import sys
    local = DjangoPyPI(sys.argv[-1])
    pypi = PyPI()

    compare_pypi_repos(local, pypi)
