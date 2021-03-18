import os
import io
import hashlib
from base64 import standard_b64encode

from six.moves.urllib.request import urlopen, Request
from six.moves.urllib.error import HTTPError

from infi.pyutils.contexts import contextmanager
from infi.pypi_manager import PyPI, DistributionNotFound, rate_limit

from logging import getLogger
logger = getLogger()

def send_setuptools_request(repository, username, password, data):
    # code taken from distribute 40.9.0, file ./setuptools/command/upload.py
    # changed logging and return value
    # TODO use code from twine?

    # set up the authentication
    user_pass = (username + ":" + password).encode('ascii')
    # The exact encoding of the authentication string is debated.
    # Anyway PyPI only accepts ascii for both username or password.
    auth = "Basic " + standard_b64encode(user_pass).decode('ascii')

    # Build up the MIME payload for the POST data
    boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
    sep_boundary = b'\r\n--' + boundary.encode('ascii')
    end_boundary = sep_boundary + b'--\r\n'
    body = io.BytesIO()
    for key, value in data.items():
        title = '\r\nContent-Disposition: form-data; name="%s"' % key
        # handle multiple entries for the same name
        if not isinstance(value, list):
            value = [value]
        for value in value:
            if type(value) is tuple:
                title += '; filename="%s"' % value[0]
                value = value[1]
            else:
                value = str(value).encode('utf-8')
            body.write(sep_boundary)
            body.write(title.encode('utf-8'))
            body.write(b"\r\n\r\n")
            body.write(value)
    body.write(end_boundary)
    body = body.getvalue()

    logger.info("Submitting %s to %s" % (data['content'][0], repository))

    # build the Request
    headers = {
        'Content-type': 'multipart/form-data; boundary=%s' % boundary,
        'Content-length': str(len(body)),
        'Authorization': auth,
    }
    request = Request(repository, data=body,
                      headers=headers)
    # send the data
    try:
        result = urlopen(request)
        status = result.getcode()
        reason = result.msg
    except HTTPError as e:
        status = e.code
        reason = e.msg
    except OSError as e:
        logger.exception("")
        raise

    if status == 200:
        return True
    else:
        logger.error('Upload failed (%s): %s' % (status, reason))
        return False


def mirror_file(repository_config, filename, package_name, package_version, metadata):
    # merge the metadata with constant data that setuptools sends and data about the file.
    # then call the function that actually sends the post request.
    f = open(filename, 'rb')
    content = f.read()
    f.close()
    basename = os.path.basename(filename)
    data = {
        ':action': 'file_upload',
        'protocol_version': '1',
        'metadata_version': '1.0',
        'content': (basename, content),
        'md5_digest': hashlib.md5(content).hexdigest(),
        'name': package_name,
        'version': package_version,
    }

    data.update(metadata)

    repository = repository_config["repository"]
    username = repository_config.get("username", "")
    password = repository_config.get("password", "")
    send_setuptools_request(repository, username, password, data)

@contextmanager
def temp_urlretrieve(url, localpath):
    import requests
    logger.info("Retrieving {}".format(url))

    req = requests.get(url)
    with open(localpath, 'wb') as fd:
        fd.write(req.content)

    try:
        yield
    finally:
        os.remove(localpath)

def mirror_release(repository_config, package_name, version, version_data, release_data):
    """ mirror a release (e.g. one sdist/bdist_egg etc.) based on data retrieved from
    pypi about the package version and the release itself. """
    # prepare metadata to post, download the file, and call mirror_file which finalizes the data and
    # posts it to the server
    metadata = {
        'filetype': release_data['packagetype'],
        'pyversion': '' if release_data['python_version'] == 'source' else release_data['python_version'],
        'comment': release_data['comment_text'],
    }
    for key in ['license', 'author', 'author_email', 'home_page', 'platform', 'summary', 'classifiers', 'description']:
        metadata[key] = version_data[key]

    with temp_urlretrieve(release_data['url'], release_data['filename']):
        return mirror_file(repository_config, release_data['filename'], package_name, version, metadata)

def get_repository_config(server_name):
    # we get a pypi repository alias but we need the url+username+password from pypirc
    # distutils does the translation, but we have to fool it a little
    from distutils.config import PyPIRCCommand
    from distutils.dist import Distribution
    pypirc = PyPIRCCommand(Distribution())
    pypirc.repository = server_name
    return pypirc._read_pypirc()

@rate_limit
def mirror_package(server_name, package_name, version=None):
    pypi = PyPI()
    version = version or pypi.get_latest_version(package_name)
    version_data = pypi.get_release_data(package_name, version)
    release_dataset = pypi._client.release_urls(package_name, version)
    repository_config = get_repository_config(server_name)
    final_result = True

    if not release_dataset:
        msg = "No distributions found for {} {} (maybe you should try to build from download url?)"
        raise DistributionNotFound(msg.format(package_name, version))

    for release_data in release_dataset:
        result = mirror_release(repository_config, package_name, version, version_data, release_data)
        final_result = final_result and result

    return final_result
