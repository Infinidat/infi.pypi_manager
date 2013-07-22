from __future__ import print_function
import sys
import argparse

from .. import PyPI
from ..dependencies import get_dependencies

def get_license(package_name):
    pypi_client = PyPI()
    info = pypi_client.get_release_data(package_name)
    if not info:
        return 'N/A'
    if 'classifiers' in info:
        classifiers = [c.split(' :: ') for c in info['classifiers']]
        license_classifiers = [c for c in classifiers if c[0] == 'License']
        if license_classifiers:
            return ', '.join(set(c[-1] for c in license_classifiers))
    if 'license' in info:
        return info['license']
    return 'N/A'

def get_dependency_licenses(package_name, progress_callback=None):
    licenses = {}
    dependencies = list(get_dependencies(package_name))[1:]
    for i, (dependency, dependency_str) in enumerate(dependencies, 1):
        if progress_callback:
            progress_callback(dependency, i, len(dependencies), True)
        licenses[dependency] = get_license(dependency)
        if progress_callback:
            progress_callback(dependency, i, len(dependencies), False)
    return licenses

def _progress_callback(dep_name, dep_index, total_deps, is_before):
    text = '[{}/{}] {}'.format(dep_index, total_deps, dep_name)
    if is_before:
        print('\r' + text, end='', file=sys.stderr)
    else:
        print('\r{}\r'.format(' ' * len(text)), end='', file=sys.stderr)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Package name')
    args = parser.parse_args()
    licenses = get_dependency_licenses(args.name, progress_callback=_progress_callback)
    for dependency, license in sorted(licenses.iteritems()):
        print('{}: {}'.format(dependency, license))

def main():
    try:
        run()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        return 1
    except:
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
