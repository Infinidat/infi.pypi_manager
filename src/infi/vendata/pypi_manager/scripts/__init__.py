from sys import argv

from .. import download_package_from_global_pypi
from .. import upload_package_to_local_pypi
from .. import extract_source_package_to_tempdir, chdir

def mirror_package(argv=argv[1:]):
    package_name, distribution_type = argv[0], argv[1]
    package_source_archive = download_package_from_global_pypi(package_name)
    package_dir = extract_source_package_to_tempdir(package_source_archive)
    with chdir(package_dir):
        upload_package_to_local_pypi(distribution_type)

