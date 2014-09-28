__import__("pkg_resources").declare_namespace(__name__)

from logging import getLogger

logger = getLogger()


class PackageNotFound(Exception):
    pass

class DistributionNotFound(Exception):
    pass

class SourceDistributionNotFound(DistributionNotFound):
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


class DjangoPyPI(PyPIBase):
    def __init__(self, server):
        super(DjangoPyPI, self).__init__(server)

    def get_info_from_doap(self, package_name):
        """:returns a list of dictionaries of: has_sig, md5_digest, packagetype, url, version, filename"""
        import requests
        import xml.etree.ElementTree as ElementTree
        doap = requests.get("{}/pypi/{}/doap.rdf".format(self.server, package_name)).content
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

    def get_all_packages(self):
        import requests
        import re
        simple_html = requests.get(self.server + "/simple").content
        return re.findall("""href=["'](?:/simple/)?(.*?)/["']""", simple_html)


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

    def get_release_data(self, package_name, version=None):
        if version is None:
            version = self.get_latest_version(package_name)
        return self._client.release_data(package_name, version)

    def get_all_packages(self):
        return self._client.list_packages()
