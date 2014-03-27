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
        from . import __file__
        from os import path
        python = path.join(self._bindir, "python")
        exec_file = __file__[:-1] if __file__.endswith("pyc") else __file__
        pid = execute_assert_success([python, exec_file, package_name])
        output = pid.get_stdout().strip()
        return output.splitlines()

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
    from ..mirror.mirror_build import tempdir
    with tempdir() as path:
        logger.info("Creating virtualenv in {0}".format(path))
        execute_assert_success(["virtualenv", "--no-site-packages", path])
        yield Env.from_virtualenv(path)
