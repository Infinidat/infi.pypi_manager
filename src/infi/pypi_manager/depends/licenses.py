from __future__ import print_function
import os
import sys
import re

from .. import PyPI, PackageNotFound
from . import get_dependencies

_dependency_string_pattern = re.compile('^(?P<name>.*?)((==|<=|>=|=<|=>)(?P<version>.*))?$')
def _dependency_string_to_name_and_version(s):
    match = _dependency_string_pattern.match(s)
    if not match:
        return s, None
    return match.group('name'), match.group('version')

class License(object):
    FIELDS = ('name', 'version', 'license', 'notice', 'homepage', 'package_url')
    def __init__(self, **kwargs):
        for key in self.FIELDS:
            if key not in kwargs:
                setattr(self, key, None)
        for key, value in kwargs.iteritems():
            if key not in self.FIELDS:
                raise TypeError('Unexpected argument for {}: {}'.format(type(self).__name__, key))
            setattr(self, key, value)
    def __getitem__(self, item):
        if item not in self.FIELDS:
            raise KeyError('{} has no such field: {}'.format(type(self).__name__, item))
        return getattr(self, item)

def get_license(package_name, version=None, safe=False):
    license = License(
            name=package_name,
            version=version,
            )
    pypi_client = PyPI()
    try:
        info = pypi_client.get_release_data(package_name, version=version)
    except PackageNotFound:
        if safe:
            return license
        raise
    if not info:
        return license
    license.version = info.get('version', version)
    if 'classifiers' in info:
        classifiers = [c.split(' :: ') for c in info['classifiers']]
        license_classifiers = [c for c in classifiers if c[0] == 'License']
        if license_classifiers:
            license.license = ', '.join(set(c[-1] for c in license_classifiers))
    if 'license' in info:
        license.notice = info['license']
        license.license = license.license or license.notice
    license.homepage = info.get('home_page')
    license.package_url = info.get('release_url')
    return license

def get_dependency_licenses(dependencies, progress_callback=None):
    ''' Return licenses of package dependencies '''
    dependencies = dependencies[1:]       # remove self
    for i, (_, dependency, dependency_str) in enumerate(dependencies, 1):
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

def output_normal(licenses):
    for l in licenses:
        print('{} {}: {}'.format(l.name, l.version or '', l.license or 'UNKNOWN'))

def output_csv(package_name, licenses):
    import csv
    filename = os.path.abspath('{}-dependencies.csv'.format(package_name))
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        writer.writerow([f.replace('_', ' ').title() for f in License.FIELDS])
        for license in licenses:
            writer.writerow([getattr(license, f) for f in License.FIELDS])
    print('Saved licenses in {}'.format(filename), file=sys.stderr)

def output_table(licenses):
    from prettytable import PrettyTable
    excluded_fields = ('notice',)
    fields = [f for f in License.FIELDS if f not in excluded_fields]
    t = PrettyTable([f.replace('_', ' ').title() for f in fields])
    t.align = 'l'
    def getfield(_l, _f):
        _v = getattr(_l, _f)
        if _v is None:
            return ''
        return _v
    for license in licenses:
        t.add_row([getfield(license, f) for f in fields])
    print(t.get_string())

def run(options, licenses):
    licenses = get_dependency_licenses(licenses, progress_callback=_progress_callback)
    iterator = sorted(licenses, key=lambda license: license.name.lower())
    if options["--csv"]:
        output_csv(options["<package>"], iterator)
    elif options["--table"]:
        output_table(iterator)
    else:
        output_normal(iterator)