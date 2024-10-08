import unittest
import uuid

from .. import PyPI, PackageNotFound
from ..mirror.mirror_build import download_package_from_global_pypi, DjangoPyPI

class PyPI_TestCase(unittest.TestCase):
    def test_get_package__exists(self):
        pypi = PyPI()
        result = pypi.get_available_versions('infi.traceback')
        assert len(result) > 1

    def test_get_latest_version(self):
        pypi = PyPI()
        result = pypi.get_latest_version('infi.traceback')
        assert isinstance(result, str)

    def test_get_package__doesn_not_exist(self):
        pypi = PyPI()
        with self.assertRaises(PackageNotFound):
            pypi.get_available_versions(uuid.uuid4().hex)

    def test_download(self):
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = PyPI()
        dist = pypi.get_latest_source_distribution_url('infi')
        self.assertTrue(dist.startswith("https://files.pythonhosted.org"))
        self.assertIn("infi-0.0.1.tar.gz", dist)

class DjangoPyPI_TestCase(unittest.TestCase):
    def test_get_package__exists(self):
        pypi = DjangoPyPI("pypi.infinidat.com")
        result = pypi.get_available_versions('infi.traceback')

    def test_get_package__doesn_not_exist(self):
        pypi = DjangoPyPI("pypi.infinidat.com")
        with self.assertRaises(PackageNotFound):
            pypi.get_available_versions(uuid.uuid4().hex)

    def test_download(self):
        import stat
        import os
        path = download_package_from_global_pypi('infi.traceback')
        size = os.stat(path)[stat.ST_SIZE]
        self.assertGreater(size, 0)

    def test_get_source_url__latest(self):
        pypi = DjangoPyPI("pypi.infinidat.com")
        self.assertEqual(pypi.get_latest_source_distribution_url('infi'),
                         'https://pypi.infinidat.com//media/dists/infi-0.0.1.tar.gz#sha256=870d87161d572c4222353e4f7d06b7bc590a745ef3926e98cd827ffb65f2aaad')
