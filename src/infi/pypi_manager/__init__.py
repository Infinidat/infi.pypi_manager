__import__("pkg_resources").declare_namespace(__name__)

import requests
import time
from logging import getLogger
try:
    from xmlrpclib import ServerProxy
except ImportError:
    # Python 3
    from xmlrpc.client import ServerProxy

logger = getLogger()


def warp_rate_limited_operation(func):
    """HOSTDEV-3337: wrap the API rate limit exception and notify user"""
    from infi.pyutils.decorators import wraps
    @wraps(func)
    def inner(*args, **kwargs):
        import xmlrpc

        try:
            return func(*args, **kwargs)
        except xmlrpc.client.Fault as e:
            logger.exception(e)
            print('\nERROR: command failed due to rate limiting.\n'
                  'Consider increasing the the default delay (environment variable "API_DELAY").')
            raise SystemExit(1)

    return inner


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


class JsonClient():
    def __init__(self, server):
        self._server = server

    def _package_release(self, package_name, version):
        # GET /pypi/package_name/release_version/json
        r = requests.get(f"{self._server}/{package_name}/{version}/json")
        if r.status_code == 404:
            raise PackageNotFound
        r.raise_for_status()
        return r.json()

    def package_releases(self, package_name, show_hidden):
        # GET /pypi/package_name/json
        r = requests.get(f"{self._server}/{package_name}/json")
        if r.status_code == 404:
            raise PackageNotFound
        r.raise_for_status()
        return r.json()['releases']

    def release_urls(self, package_name, release_version):
        return self._package_release(package_name, release_version)['urls']

    def release_data(self, package_name, version):
        return self._package_release(package_name, version)['info']

    def list_packages(self):
        raise NotImplemented


class RateLimitedServerProxy(JsonClient):
    def __getattr__(self, name):
        from os import environ

        delay = int(environ.get("API_DELAY", 1))
        time.sleep(delay)

        return super(RateLimitedServerProxy, self).__getattr__(name)


class PyPIBase(object):
    def __init__(self, server):
        if not server.startswith("http"):
            server = "https://" + server
        self.server = server


class DjangoPyPI(PyPIBase):
    def __init__(self, server):
        super(DjangoPyPI, self).__init__(server)

    def get_info_from_doap(self, package_name):
        """:returns a list of dictionaries of: has_sig, md5_digest, packagetype, url, version, filename"""
        import xml.etree.ElementTree as ElementTree
        doap = requests.get("{}/pypi/{}/doap.rdf".format(self.server, package_name)).content
        if b'Not Found' in doap:
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
        releases = list(set(item['version'] for item in self.get_info_from_doap(package_name)))
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
        for release in [release for release in self.get_releases_for_version(package_name, release_version) if release['packagetype'] == 'sdist']:
            return release['url']
        raise SourceDistributionNotFound(package_name, release_version)

    def get_all_packages(self):
        import requests
        import re
        simple_html = requests.get(self.server + "/simple").content
        return re.findall("""href=["'](?:/simple/)?(.*?)/["']""", simple_html)


class PyPI(PyPIBase):
    def __init__(self, server="https://pypi.org"):
        super(PyPI, self).__init__(server)
        self._client = RateLimitedServerProxy("{}/pypi".format(self.server))

    @warp_rate_limited_operation
    def _get_package_releases(self, package_name, show_hidden=False):
        releases = self._client.package_releases(package_name, show_hidden).keys()
        releases = list(releases)
        logger.info("Versions found for {!r}: {!r}".format(package_name, releases))
        if len(releases) == 0:
            raise PackageNotFound("{0} was not found in {1}".format(package_name, self.server))
        return releases

    def get_available_versions(self, package_name):
        return self._get_package_releases(package_name, show_hidden=True)

    def get_latest_version(self, package_name):
        return self._get_package_releases(package_name, show_hidden=False)[0]

    @warp_rate_limited_operation
    def get_releases_for_version(self, package_name, release_version):
        return self._client.release_urls(package_name, release_version)

    def get_latest_source_distribution_url(self, package_name):
        release_version = self.get_latest_version(package_name)
        return self.get_source_distribution_url_of_specific_release_version(package_name, release_version)

    def get_source_distribution_url_of_specific_release_version(self, package_name, release_version):
        for release in [release for release in self.get_releases_for_version(package_name, release_version) if release['packagetype'] == 'sdist']:
            return release['url']
        raise SourceDistributionNotFound(package_name, release_version)

    @warp_rate_limited_operation
    def get_release_data(self, package_name, version=None):
        if version is None:
            version = self.get_latest_version(package_name)
        return self._client.release_data(package_name, version)

    @warp_rate_limited_operation
    def get_all_packages(self):
        return self._client.list_packages()

    def find_pypi_name(self, package_name):
        # find the "correct" name used by PyPI for a package,
        # e.g. logbook -> Logbook, ipython-genutils -> ipython_genutils
        response = requests.get(self.server + "/pypi/" + package_name + "/", allow_redirects=False)
        if response.status_code == 200:
            return package_name
        if response.status_code == 301:
            return response.headers["Location"].split("/")[-1]
        raise PackageNotFound(package_name)
