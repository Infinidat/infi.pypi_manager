import unittest

from .. import PyPI, PackageNotFound, download_package_from_global_pypi, DjangoPyPI

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
                         'http://pypi.python.org/packages/source/i/ipython/ipython-0.13.1.tar.gz')

    def test_download(self):
        from .. import download_package_from_global_pypi
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = PyPI()
        self.assertEqual(pypi.get_latest_source_distribution_url('infi'),
                         'http://pypi.python.org/packages/source/i/infi/infi-0.0.1-develop-1.tar.gz')

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
                         'http://pypi01.infinidat.com//media/dists/ipython-0.13.1.tar.gz#md5=ca7e75f7c802afc6aaa0a1ea59846420')

    def test_download(self):
        from .. import download_package_from_global_pypi
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        self.assertEqual(pypi.get_latest_source_distribution_url('infi'),
                         'http://pypi01.infinidat.com//media/dists/infi-0.0.1-develop-1.tar.gz#md5=97cfb0266e37c3115d031f77f420f463')
