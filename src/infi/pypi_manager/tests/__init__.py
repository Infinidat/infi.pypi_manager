import unittest

from .. import PyPI, PackageNotFound
from ..mirror.mirror_build import download_package_from_global_pypi, DjangoPyPI

class PyPI_TestCase(unittest.TestCase):
    def test_get_package__exists(self):
        pypi = PyPI()
        result = pypi.get_available_versions('infi.traceback')

    def test_get_package__doesn_not_exist(self):
        pypi = PyPI()
        with self.assertRaises(PackageNotFound):
            pypi.get_available_versions('abcxyz')

    def test_get_source_url(self):
        pypi = PyPI()
        self.assertEqual(pypi.get_latest_source_distribution_url('ipython'),
                         'https://pypi.python.org/packages/source/i/ipython/ipython-1.2.1.tar.gz')

    def test_download(self):
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = PyPI()
        self.assertEqual(pypi.get_latest_source_distribution_url('infi'),
                         'https://pypi.python.org/packages/source/i/infi/infi-0.0.1.tar.gz')

class DjangoPyPI_TestCase(unittest.TestCase):
    def test_get_package__exists(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        result = pypi.get_available_versions('infi.traceback')

    def test_get_package__doesn_not_exist(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        with self.assertRaises(PackageNotFound):
            pypi.get_available_versions('abcxyz')

    def test_get_source_url(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        self.assertEqual(pypi.get_latest_source_distribution_url('ipython'),
                'http://pypi01.infinidat.com//media/dists/ipython-1.2.1.tar.gz#md5=4ffb36697f7ca8cb4a2de0f5b30bc89c')

    def test_download(self):
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        self.assertEqual(pypi.get_latest_source_distribution_url('infi'),
                         'http://pypi01.infinidat.com//media/dists/infi-0.0.1.tar.gz#md5=62f7db8e3017d37b5a99cc571d5b0f07')
