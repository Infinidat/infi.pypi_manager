from .. import PyPI, DjangoPyPI
from prettytable import PrettyTable
from pkg_resources import parse_version
import requests
import urllib
import re

def get_versions_from_reference(reference_repo):
    reference_pypi_html = requests.get("{}/pypi".format(reference_repo.server)).content
    search_result = re.findall("""href=["'](?:/pypi/)?([^/]+)/([^/]+)/["']""", reference_pypi_html)
    return dict((k, urllib.unquote(v)) for k, v in search_result)

def get_version_dict_from_other(other_repo, repos_to_check):
    search_result = list()
    for i in range(0, len(repos_to_check), 10):
        res = other_repo._client.search(dict(name=repos_to_check[i:i+10]), "or")
        search_result.extend(res)
    return dict([(repo["name"], repo["version"]) for repo in search_result if repo["name"] in repos_to_check])

def compare_pypi_repos(reference_repo, other_repo):
    upgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    downgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    reference_repo_versions = get_versions_from_reference(reference_repo)
    repos_to_check = reference_repo_versions.keys()
    other_repo_versions = get_version_dict_from_other(other_repo, repos_to_check)
    for name in sorted(repos_to_check):
        try:
            reference_repo_version = reference_repo_versions[name]
            other_repo_version = other_repo_versions[name]
        except KeyError:
            continue
        if other_repo_version != reference_repo_version:
            if parse_version(reference_repo_version) < parse_version(other_repo_version):
                upgrade_table.add_row([name, reference_repo_version, other_repo_version])
            else:
                downgrade_table.add_row([name, reference_repo_version, other_repo_version])

    print "Upgradable Packaages:"
    print upgrade_table
    print
    print "Downgradable Packaages:"
    print downgrade_table


def main():
    import sys
    local = DjangoPyPI(sys.argv[-1])
    pypi = PyPI()

    compare_pypi_repos(local, pypi)
