def get_dependencies(name):
    from collections import deque
    from pkg_resources import get_distribution
    distribution = get_distribution(name)
    queue = deque()
    returned_dependencies = set()
    queue.append((distribution, None))
    while queue:
        dependency, parent = queue.popleft()
        dependency_name = dependency.project_name
        # get the requirement with the specs, if any
        dependency_str = str(dependency).split(' ')[0]
        if dependency_name in returned_dependencies:
            continue
        yield parent, dependency_name, dependency_str
        returned_dependencies.add(dependency_name)
        queue.extend([(requirement, dependency_str) for requirement in get_distribution(dependency_name).requires()])

def print_tree(dependencies, parent, indent):
    print indent * '\t' + parent
    if parent in dependencies:
        for child in sorted(dependencies[parent], key=lambda x: len(dependencies.get(x, []))):
            print_tree(dependencies, child, indent+1)

def main():
    import sys
    if len(sys.argv) == 1:
        print "Usage: {} <package name> [--tree]".format(sys.argv[0])
        return
    tree = len(sys.argv) > 2 and sys.argv[2] == "--tree"
    dependencies = get_dependencies(sys.argv[1])
    if not tree:
        dependencies = [dependency_str for parent, dependency_name, dependency_str in dependencies]
        dependencies = dependencies[1:]         # remove self
        dependencies.sort()
        print '\n'.join(dependencies)
    else:
        dependency_tree = dict()
        for parent, dependency_name, dependency_str in dependencies:
            dependency_tree.setdefault(parent, list()).append(dependency_name)
        print_tree(dependency_tree, sys.argv[1], 0)

if __name__ == "__main__":
    main()
