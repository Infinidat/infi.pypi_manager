from .. import PyPI, DjangoPyPI, PackageNotFound
from prettytable import PrettyTable
from pkg_resources import parse_version
import requests
import urllib
import re

def get_versions_from_reference(reference_repo):
    reference_pypi_html = requests.get("{}/pypi".format(reference_repo.server)).content
    search_result = re.findall("""href=["'](?:/pypi/)?([^/]+)/([^/]+)/["']""", reference_pypi_html)
    return dict((k, urllib.unquote(v)) for k, v in search_result)

def compare_pypi_repos(reference_repo, other_repo):
    upgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    downgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    reference_repo_versions = get_versions_from_reference(reference_repo)
    packages_to_check = reference_repo_versions.keys()
    for name in sorted(packages_to_check):
        try:
            reference_repo_version = reference_repo_versions[name]
            other_repo_version = other_repo.get_latest_version(name)
        except PackageNotFound:
            continue
        if other_repo_version != reference_repo_version:
            if parse_version(reference_repo_version) < parse_version(other_repo_version):
                upgrade_table.add_row([name, reference_repo_version, other_repo_version])
            else:
                downgrade_table.add_row([name, reference_repo_version, other_repo_version])

    print "Upgradable Packages:"
    print upgrade_table
    print
    print "Downgradable Packages:"
    print downgrade_table


def main():
    import sys
    local = DjangoPyPI(sys.argv[-1])
    pypi = PyPI()

    compare_pypi_repos(local, pypi)
