from __future__ import print_function
import sys
import argparse
import re

from .. import PyPI, PackageNotFound
from ..dependencies import get_dependencies

_dependency_string_pattern = re.compile('^(?P<name>.*?)((==|<=|>=|=<|=>)(?P<version>.*))?$')
def _dependency_string_to_name_and_version(s):
    match = _dependency_string_pattern.match(s)
    if not match:
        return s, None
    return match.group('name'), match.group('version')

def get_license(package_name, version=None, safe=False):
    pypi_client = PyPI()
    try:
        info = pypi_client.get_release_data(package_name, version=version)
    except PackageNotFound:
        if safe:
            return None
        raise
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
    ''' Return licenses of package dependencies, as a list of tuples
    (dependency, version, license) '''
    licenses = []
    dependencies = list(get_dependencies(package_name))[1:]
    for i, (dependency, dependency_str) in enumerate(dependencies, 1):
        version = _dependency_string_to_name_and_version(dependency_str)[1]
        if progress_callback:
            progress_callback(dependency, version, i, len(dependencies), True)
        license = get_license(dependency, version=version, safe=True) or '[PACKAGE NOT FOUND]'
        licenses.append((dependency, version, license))
        if progress_callback:
            progress_callback(dependency, version, i, len(dependencies), False)
    return licenses

def _progress_callback(dep_name, dep_version, dep_index, total_deps, is_before):
    text = '[{}/{}] {} {}'.format(dep_index, total_deps, dep_name, dep_version or '')
    if is_before:
        print('\r' + text, end='', file=sys.stderr)
    else:
        print('\r{}\r'.format(' ' * len(text)), end='', file=sys.stderr)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Package name')
    args = parser.parse_args()
    licenses = get_dependency_licenses(args.name, progress_callback=_progress_callback)
    for dependency, version, license in sorted(licenses, key=lambda keyval: keyval[0].lower()):
        print('{}{}{}: {}'.format(dependency, ' ' if version else '', version or '', license))

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
