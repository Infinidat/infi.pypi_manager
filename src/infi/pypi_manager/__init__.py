__import__("pkg_resources").declare_namespace(__name__)

from infi.pyutils.contexts import contextmanager
from logging import getLogger

logger = getLogger()


class PackageNotFound(Exception):
    pass


class SourceDistributionNotFound(Exception):
    pass


class UnsupportedArchive(Exception):
    pass


class InvalidArchive(Exception):
    pass


class PyPIBase(object):
    def __init__(self, server):
        if not server.startswith("http://"):
            server = "http://" + server
        self.server = server
        
    def get_all_packages(self):
        from urllib import urlopen
        import re
        simple_html = urlopen(self.server + "/simple").read()
        return re.findall("""href=["'](?:/simple/)?(.*?)/["']""", simple_html)


class DjangoPyPI(PyPIBase):
    def __init__(self, server):
        super(DjangoPyPI, self).__init__(server)

    def get_info_from_doap(self, package_name):
        """:returns a list of dictionaries of: has_sig, md5_digest, packagetype, url, version, filename"""
        from urllib import urlopen
        import xml.etree.ElementTree as ElementTree
        doap = urlopen("{}/pypi/{}/doap.rdf".format(self.server, package_name)).read()
        if 'Not Found' in doap:
            raise PackageNotFound(package_name)
        root = ElementTree.fromstring(doap)
        items = []
        package_types = dict(exe='bdist_wininst', egg='bdist_egg', gz='sdist', zip='sdist', bz2='sdist')
        for version_element in root.iter('{http://usefulinc.com/ns/doap#}Version'):
            # release --> Version --> file-release|revision
            for filename_element in version_element.iter('{http://usefulinc.com/ns/doap#}file-release'):
                uri = filename_element.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                url = "{}/{}".format(self.server, uri)
                item = dict(has_sig=True, md5_sigest=url.split('=', 1)[1], url=url, filename=filename_element.text,
                            version=version_element.find('{http://usefulinc.com/ns/doap#}revision').text)
                item['packagetype'] = package_types.get(item['filename'].split('.')[-1], 'unknown')
                items.append(item)
        return items

    def get_available_versions(self, package_name):
        releases = [item['version'] for item in self.get_info_from_doap(package_name)]
        logger.info("Versions found for {!r}: {!r}".format(package_name, releases))
        if len(releases) == 0:
            raise PackageNotFound(package_name)
        return releases

    def get_latest_version(self, package_name):
        from pkg_resources import parse_version
        versions = self.get_available_versions(package_name)
        versions.sort(key=lambda version: parse_version(version))
        return versions[-1]

    def get_releases_for_version(self, package_name, release_version):
        return [item for item in self.get_info_from_doap(package_name)
                if item['version'] == release_version]

    def get_latest_source_distribution_url(self, package_name):
        release_version = self.get_latest_version(package_name)
        return self.get_source_distribution_url_of_specific_release_version(package_name, release_version)

    def get_source_distribution_url_of_specific_release_version(self, package_name, release_version):
        for release in filter(lambda release: release['packagetype'] == 'sdist',
                              self.get_releases_for_version(package_name, release_version)):
            return release['url']
        raise SourceDistributionNotFound(package_name, release_version)


class PyPI(PyPIBase):
    def __init__(self, server="http://pypi.python.org"):
        super(PyPI, self).__init__(server)
        import xmlrpclib
        self._client = xmlrpclib.ServerProxy("{}/pypi".format(self.server))

    def get_available_versions(self, package_name):
        releases = self._client.package_releases(package_name)
        logger.info("Versions found for {!r}: {!r}".format(package_name, releases))
        if len(releases) == 0:
            raise PackageNotFound(package_name)
        return releases

    def get_latest_version(self, package_name):
        return self.get_available_versions(package_name)[0]

    def get_releases_for_version(self, package_name, release_version):
        return self._client.release_urls(package_name, release_version)

    def get_latest_source_distribution_url(self, package_name):
        release_version = self.get_latest_version(package_name)
        return self.get_source_distribution_url_of_specific_release_version(package_name, release_version)

    def get_source_distribution_url_of_specific_release_version(self, package_name, release_version):
        for release in filter(lambda release: release['packagetype'] == 'sdist',
                              self.get_releases_for_version(package_name, release_version)):
            return release['url']
        raise SourceDistributionNotFound(package_name, release_version)


def download_package_from_global_pypi(package_name, release_version=None):
    from urllib2 import urlopen
    from tempfile import mkstemp
    from os import write, close
    pypi = PyPI()
    if release_version is None:
        url = pypi.get_latest_source_distribution_url(package_name)
    else:
        url = pypi.get_source_distribution_url_of_specific_release_version(package_name, release_version)
    data = urlopen(url).read()
    fd, path = mkstemp(suffix=url.split('/')[-1])
    write(fd, data)
    close(fd)
    logger.info("Downloaded {} to {}".format(url, path))
    return path


def upload_package_to_local_pypi(distribution_format, index_server):
    from infi.execute import execute
    command = ['python', 'setup.py', 'register', '-r', index_server,
                          distribution_format, 'upload', '-r', index_server]
    logger.info("Executing {}".format(' '.join(command)))
    subprocess = execute(command)
    logger.info(subprocess.get_stdout())
    logger.info(subprocess.get_stderr())
    assert subprocess.get_returncode() == 0


def extract_source_package_to_tempdir(package_source_archive, dest_dir):
    import tarfile
    from zipfile import ZipFile
    import os
    logger.info("Unpacking {} to {}".format(package_source_archive, dest_dir))
    if package_source_archive.endswith('zip'):
        archive = ZipFile(package_source_archive)
        archive.extractall(dest_dir)
    elif package_source_archive.endswith('tar.gz'):
        archive = tarfile.open(package_source_archive, mode='r:gz')
        archive.extractall(dest_dir)
    elif package_source_archive.endswith('tar.bz2'):
        archive = tarfile.open(package_source_archive, mode='r:bz2')
        archive.extractall(dest_dir)
    else:
        raise UnsupportedArchive(package_source_archive)
    if os.path.exists(os.path.join(dest_dir, 'setup.py')):
        return dest_dir
    for dirname in os.listdir(dest_dir):
        if os.path.exists(os.path.join(dest_dir, dirname, 'setup.py')):
            return os.path.join(dest_dir, dirname)
        raise InvalidArchive(package_source_archive, dest_dir)
    raise InvalidArchive(package_source_archive, dest_dir)


@contextmanager
def chdir(path):
    import os
    curdir = os.path.abspath(os.path.curdir)
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(curdir)


@contextmanager
def tempdir():
    from tempfile import mkdtemp
    from shutil import rmtree
    path = mkdtemp()
    try:
        yield path
    finally:
        rmtree(path)
