def get_dependencies(name):
    from collections import deque
    from pkg_resources import get_distribution
    distribution = get_distribution(name)
    queue = deque()
    returned_dependencies = set()
    queue.append(distribution)
    while queue:
        dependency = queue.popleft()
        dependency_name = dependency.project_name
        # get the requirement with the specs, if any
        dependency_str = str(dependency).split(' ')[0]
        if dependency_name in returned_dependencies:
            continue
        yield dependency_name, dependency_str
        returned_dependencies.add(dependency_name)
        queue.extend(get_distribution(dependency_name).requires())

def main():
    import sys
    dependencies = get_dependencies(sys.argv[-1])
    dependencies = [dependency_name for dependency_name, dependency_str in dependencies]
    dependencies = sorted(dependencies[1:])     # skip self
    print('\n'.join(dependencies))

if __name__ == "__main__":
    main()
