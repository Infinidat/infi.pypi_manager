from logging import getLogger
from infi.pyutils.contexts import contextmanager
logger = getLogger(__name__)


class Env(object):
    def __init__(self, basedir):
        from os import path
        super(Env, self).__init__()
        self._basedir = basedir
        self._bindir = path.join(self._basedir, "bin")

    def easy_install(self, package_name, release_version=None):
        from infi.execute import execute_assert_success
        from os import path
        easy_install = path.join(self._bindir, "easy_install")
        requiremement = package_name if release_version is None else "{0}=={1}".format(package_name, release_version)
        logger.info("installing {0}, version {1}".format(package_name, release_version))
        execute_assert_success([easy_install, "-i", "http://pypi.python.org/simple", "-U", requiremement])

    def get_dependencies(self, package_name):
        from infi.execute import execute_assert_success
        from . import dependencies
        from os import path
        python = path.join(self._bindir, "python")
        pid = execute_assert_success([python, dependencies.__file__, package_name])
        return eval(pid.get_stdout().strip())

    def get_installed_version(self, package_name):
        from infi.execute import execute_assert_success
        from os import path
        python = path.join(self._bindir, "python")
        statements = ["from pkg_resources import get_distribution",
                      "print get_distribution({0!r}).version".format(package_name)]
        pid = execute_assert_success([python, "-c", "; ".join(statements)])
        return eval(repr(pid.get_stdout().strip()))

    @classmethod
    def from_virtualenv(cls, basedir):
        return cls(basedir)


@contextmanager
def virtualenv():
    from infi.execute import execute_assert_success
    from .mirror_build import tempdir
    with tempdir() as path:
        logger.info("Creating virtualenv in {0}".format(path))
        execute_assert_success(["virtualenv", "--no-site-packages", "--distribute", path])
        yield Env.from_virtualenv(path)
