from __future__ import print_function
import os
import sys
import argparse
import re
from collections import namedtuple

from .. import PyPI, PackageNotFound
from ..dependencies import get_dependencies

_dependency_string_pattern = re.compile('^(?P<name>.*?)((==|<=|>=|=<|=>)(?P<version>.*))?$')
def _dependency_string_to_name_and_version(s):
    match = _dependency_string_pattern.match(s)
    if not match:
        return s, None
    return match.group('name'), match.group('version')

License = namedtuple('License', ('name', 'version', 'license', 'notice'))
LICENSE_FIELDS = License._fields

def get_license(package_name, version=None, safe=False):
    pypi_client = PyPI()
    try:
        info = pypi_client.get_release_data(package_name, version=version)
    except PackageNotFound:
        if safe:
            return License(package_name, version, None, None)
        raise
    if not info:
        return License(package_name, version, None, None)
    version = info.get('version', version)
    license, notice = None, None
    if 'classifiers' in info:
        classifiers = [c.split(' :: ') for c in info['classifiers']]
        license_classifiers = [c for c in classifiers if c[0] == 'License']
        if license_classifiers:
            license = ', '.join(set(c[-1] for c in license_classifiers))
    if 'license' in info:
        notice = info['license']
        license = license or notice
    return License(package_name, version, license, notice)

def get_dependency_licenses(package_name, progress_callback=None):
    ''' Return licenses of package dependencies '''
    dependencies = list(get_dependencies(package_name))[1:]
    for i, (dependency, dependency_str) in enumerate(dependencies, 1):
        version = _dependency_string_to_name_and_version(dependency_str)[1]
        if progress_callback:
            progress_callback(dependency, version, i, len(dependencies), True)
        license = get_license(dependency, version=version, safe=True)
        yield license
        if progress_callback:
            progress_callback(dependency, version, i, len(dependencies), False)

def _progress_callback(dep_name, dep_version, dep_index, total_deps, is_before):
    text = '[{}/{}] {} {}'.format(dep_index, total_deps, dep_name, dep_version or '')
    if is_before:
        print('\r' + text, end='', file=sys.stderr)
    else:
        print('\r{}\r'.format(' ' * len(text)), end='', file=sys.stderr)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Package name')
    parser.add_argument('--csv', action='store_true', help='Output in CSV format')
    args = parser.parse_args()
    licenses = get_dependency_licenses(args.name, progress_callback=_progress_callback)
    iterator = sorted(licenses, key=lambda license: license.name.lower())
    if args.csv:
        output_csv(args.name, iterator)
    else:
        output_normal(iterator)

def output_normal(licenses):
    for l in licenses:
        print('{} {}: {}'.format(l.name, l.version or '', l.license or 'UNKNOWN'))

def output_csv(package_name, licenses):
    import csv
    filename = os.path.abspath('{}-dependencies.csv'.format(package_name))
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(LICENSE_FIELDS)
        for license in licenses:
            writer.writerow(license)
    print('Saved licenses in {}'.format(filename), file=sys.stderr)

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
