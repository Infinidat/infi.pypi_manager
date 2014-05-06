import re
import sys
from infi.execute import execute_assert_success
import pkg_resources
from ..depends.dependencies import get_dependencies

def run_easy_install(package_name, package):
    cmd = "easy_install -U \"{}\"".format(package)
    print "Running:", cmd,
    sys.stdout.flush()
    output = execute_assert_success(cmd, shell=True).get_stdout()

    try:
        # try to get the name of the package from what is already installed
        # e.g. setuptools will become distribute
        package_name = pkg_resources.get_distribution(package_name).project_name
    except pkg_resources.DistributionNotFound:
        pass

    added = re.search("Adding ({}.*?) to".format(package_name), output)
    removed = re.search("Removing ({}.*?) from".format(package_name), output)
    stayed = re.search("({}.*?) is already".format(package_name), output)
    best_match = re.search("Best match: ({}.*)".format(package_name), output)
    if stayed:
        print "(Already on latest version {})".format(stayed.group(1))
    elif removed and added:
        print "(Updated from {} to {})".format(removed.group(1), added.group(1))
    elif best_match:
        print "(Installed version {})".format(best_match.group(1))
    else:
        # status unknown
        print "(updated)"

def hard_install(name):
    dependencies = list(reversed(list(get_dependencies(name))))
    print "Found {} dependencies.".format(len(dependencies))
    for parent, package_name, package in dependencies:
        run_easy_install(package_name, package)

def main():
    import sys
    hard_install(sys.argv[1])
