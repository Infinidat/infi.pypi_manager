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
                         'http://pypi.python.org/packages/source/i/ipython/ipython-0.13.tar.gz')

    def test_download(self):
        from .. import download_package_from_global_pypi
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = PyPI()
        self.assertEqual(pypi.get_latest_source_distribution_url('pycrypto'),
                         'http://pypi.python.org/packages/source/p/pycrypto/pycrypto-2.6.tar.gz')

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
                         'http://pypi01.infinidat.com//media/dists/ipython-0.13.tar.gz#md5=42832d994731e9f64d0944ae864be4a1')

    def test_download(self):
        from .. import download_package_from_global_pypi
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = DjangoPyPI("pypi01.infinidat.com")
        self.assertEqual(pypi.get_latest_source_distribution_url('pycrypto'),
                         'http://pypi01.infinidat.com//media/dists/pycrypto-2.5.tar.gz#md5=2fdd4d7919840b5fbc800b8364cb8ca4')

