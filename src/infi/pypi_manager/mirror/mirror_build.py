from infi.pyutils.contexts import contextmanager
from logging import getLogger
from .. import PyPI, DjangoPyPI, DistributionNotFound, UnsupportedArchive, InvalidArchive

logger = getLogger()


def get_index_url_from_pydistutils():
    from ConfigParser import ConfigParser
    from urlparse import urlparse
    from os import path, name
    config = ConfigParser()
    config.read([path.expanduser(path.join('~', '%spydistutils.cfg' % ('' if name == 'nt' else '.')))])
    result = urlparse(config.get('easy_install', 'index-url'))
    return result.geturl().replace(result.path, '')


def download_package_from_local_pypi(index_server, package_name, release_version=None):
    from urllib import urlretrieve
    from tempfile import mkstemp
    from os import close
    index_url = get_index_url_from_pydistutils()
    djangopypi = DjangoPyPI(index_url)
    release_version = release_version or djangopypi.get_latest_version(package_name)
    url = djangopypi.get_source_distribution_url_of_specific_release_version(package_name, release_version)
    url = url.split('#')[0]
    fd, path = mkstemp(suffix=url.split('/')[-1])
    close(fd)
    urlretrieve(url, path)
    logger.info("Downloaded {} to {}".format(url, path))
    return path


def download_package_from_global_pypi(package_name, release_version=None, use_download_url=False):
    from urllib import urlretrieve
    from tempfile import mkstemp
    from os import close
    pypi = PyPI()
    release_version = release_version or pypi.get_latest_version(package_name)
    if use_download_url:
        release_data = pypi.get_release_data(package_name, release_version)
        if "download_url" not in release_data or release_data["download_url"] == "UNKNOWN":
            msg = "No valid download url found for package {} {}"
            raise DistributionNotFound(msg.format(package_name, release_version))
        url = release_data["download_url"]
    else:
        url = pypi.get_source_distribution_url_of_specific_release_version(package_name, release_version)
    fd, path = mkstemp(suffix=url.split('/')[-1])
    close(fd)
    urlretrieve(url, path)
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


def mirror_package(package_name, distribution_type, release_version, index_server, use_download_url):
    package_source_archive = download_package_from_global_pypi(package_name, release_version, use_download_url)
    with tempdir() as base:
        setup_py_dir = extract_source_package_to_tempdir(package_source_archive, base)
        with chdir(setup_py_dir):
            upload_package_to_local_pypi(distribution_type, index_server)


def rebuild_package_binary_distributions(index_server, package_name, release_version, distribution_type='bdist_egg'):
    package_source_archive = download_package_from_local_pypi(index_server, package_name, release_version)
    with tempdir() as base:
        setup_py_dir = extract_source_package_to_tempdir(package_source_archive, base)
        with chdir(setup_py_dir):
            upload_package_to_local_pypi(distribution_type, index_server)


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
