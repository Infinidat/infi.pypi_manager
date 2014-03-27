"""
Usage:
    pydepends <package>
    pydepends <package> --tree
    pydepends <package> --licenses [--csv | --table]
    pydepends <package> --find=<dependency>

Options:
    <package>                 a name of a package to get dependencies for
    --tree                    show the dependencies in a tree view
    --licenses                get licenses for each dependency
    --csv                     output licenses in CSV format
    --table                   output licenses in a table
    --find=<dependency>       find which dependent packages depend on a specific package
    <dependency>              name of a package to find
"""

import docopt
from . import get_dependencies, licenses

def print_tree(dependencies, parent, indent):
    print indent * '\t' + parent
    if parent in dependencies:
        for child in sorted(dependencies[parent], key=lambda x: len(dependencies.get(x, []))):
            print_tree(dependencies, child, indent+1)

def make_tree(dependencies):
    dependency_tree = dict()
    for parent, dependency_name, dependency_str in dependencies:
        parent_name = parent if parent is None else parent.split('>')[0].split('=')[0]
        dependency_tree.setdefault(parent_name, list()).append(dependency_name)
    return dependency_tree

def output_tree(dependencies):
    dependency_tree = make_tree(dependencies)
    package_name = dependencies[0][1]       # root of tree to print is the requsted package name
    print_tree(dependency_tree, package_name, 0)

def output_list(dependencies):
    dependencies = [dependency_str for parent, dependency_name, dependency_str in dependencies]
    dependencies = dependencies[1:]         # remove self
    dependencies.sort()
    print '\n'.join(dependencies)

def find(dependencies, package_to_find):
    dependency_tree = make_tree(dependencies)
    for parent_name in dependency_tree:
        if package_to_find in dependency_tree[parent_name]:
            print parent_name

def main():
    options = docopt.docopt(__doc__)
    allow_duplicates = options["--find"] is not None        # only the "find" options needs duplicated
    dependencies = list(get_dependencies(options["<package>"], allow_duplicates=allow_duplicates))
    if options["--find"]:
        return find(dependencies, options["--find"])
    elif options["--licenses"]:
        return licenses.run(options, dependencies)
    elif options["--tree"]:
        return output_tree(dependencies)
    return output_list(dependencies)
