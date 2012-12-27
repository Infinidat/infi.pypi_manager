def get_dependencies(name):
    from pkg_resources import get_distribution
    from collections import deque
    distribution = get_distribution(name)
    queue = deque()
    queue.extend(distribution.requires())
    dependencies = set()
    while queue:
        depenency = queue.popleft().project_name
        if depenency in dependencies:
            continue
        dependencies.add(depenency)
        queue.extend(get_distribution(depenency).requires())
    return dependencies

if __name__ == "__main__":
    import sys
    print repr(get_dependencies(sys.argv[-1]))
