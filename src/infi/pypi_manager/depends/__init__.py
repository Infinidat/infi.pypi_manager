def get_dependencies(name, allow_duplicates=False):
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
        if allow_duplicates:
            yield parent, dependency_name, dependency_str
        if dependency_name in returned_dependencies:
            continue
        if not allow_duplicates:
            yield parent, dependency_name, dependency_str
        returned_dependencies.add(dependency_name)
        queue.extend([(requirement, dependency_str) for requirement in get_distribution(dependency_name).requires()])

if __name__ == "__main__":
    # very similar to output_list, but used by recursive.py in a venv so we can't import dependencies.py
    import sys
    dependencies = list(get_dependencies(sys.argv[1]))
    dependencies = [dependency_str for parent, dependency_name, dependency_str in dependencies]
    dependencies = dependencies[1:]         # remove self
    dependencies.sort()
    print '\n'.join(dependencies)