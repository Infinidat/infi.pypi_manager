import re
from infi.execute import execute_assert_success
from pkg_resources import get_distribution

def get_dependencies(name):
    from collections import deque
    distribution = get_distribution(name)
    queue = deque()
    returned_dependencies = []
    queue.append(distribution)
    while queue:
        dependency = queue.popleft()
        dependency_name = dependency.project_name
        # get the requirement with the specs, if any
        dependency_str = str(dependency).split(' ')[0]
        if dependency_name in returned_dependencies:
            continue
        yield dependency_name, dependency_str
        returned_dependencies.append(dependency_name)
        queue.extend(get_distribution(dependency_name).requires())

def run_easy_install(package_name, package):
    cmd = "easy_install -U '{}'".format(package)
    print "Running:", cmd,
    output = execute_assert_success(cmd, shell=True).get_stdout()

    try:
        # try to get the name of the package from what is already installed
        # e.g. setuptools will become distribute
        package_name = get_distribution(package_name).project_name
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
    import os
    dependencies = list(reversed(list(get_dependencies(name))))
    print "Found {} dependencies.".format(len(dependencies))
    for package_name, package in dependencies:
        run_easy_install(package_name, package)

def main():
    import sys
    hard_install(sys.argv[1])
