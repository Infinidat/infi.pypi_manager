from sys import argv, stdout
from logging import basicConfig, DEBUG
from .. import download_package_from_global_pypi
from .. import upload_package_to_local_pypi
from .. import extract_source_package_to_tempdir, chdir

def mirror_package(argv=argv[1:]):
    argv.append(None)
    basicConfig(stream=stdout, level=DEBUG)
    package_name, distribution_type, release_version = argv[0], argv[1], argv[2]
    package_source_archive = download_package_from_global_pypi(package_name, release_version)
    package_dir = extract_source_package_to_tempdir(package_source_archive)
    with chdir(package_dir):
        upload_package_to_local_pypi(distribution_type)

