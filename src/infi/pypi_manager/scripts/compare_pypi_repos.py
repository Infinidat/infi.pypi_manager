from .. import PyPI, DjangoPyPI, PackageNotFound
from prettytable import PrettyTable
from pkg_resources import parse_version

def compare_pypi_repos(reference_repo, other_repo):
    upgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    downgrade_table = PrettyTable(["Package", reference_repo.server, other_repo.server])
    for name in reference_repo.get_all_packages():
        try:
            reference_repo_version = reference_repo.get_latest_version(name)
            other_repo_version = other_repo.get_latest_version(name)
        except PackageNotFound:
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