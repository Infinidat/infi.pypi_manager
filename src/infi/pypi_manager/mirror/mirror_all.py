try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import os
import socket
import httplib
import base64
import urlparse
import cStringIO as StringIO
import urllib

from infi.pyutils.contexts import contextmanager
from infi.pypi_manager import PyPI, DistributionNotFound

from logging import getLogger
logger = getLogger()

def send_setuptools_request(repository, username, password, data):
    # code taken from distribute 0.6.35, file ./setuptools/command/upload.py
    # changed logging and return value

    # set up the authentication
    auth = "Basic " + base64.encodestring(username + ":" + password).strip()

    # Build up the MIME payload for the POST data
    boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
    sep_boundary = '\n--' + boundary
    end_boundary = sep_boundary + '--'
    body = StringIO.StringIO()
    for key, value in data.items():
        # handle multiple entries for the same name
        if type(value) != type([]):
            value = [value]
        for value in value:
            if type(value) is tuple:
                fn = ';filename="%s"' % value[0]
                value = value[1]
            else:
                fn = ""
            value = str(value)
            body.write(sep_boundary)
            body.write('\nContent-Disposition: form-data; name="%s"'%key)
            body.write(fn)
            body.write("\n\n")
            body.write(value)
            if value and value[-1] == '\r':
                body.write('\n')  # write an extra newline (lurve Macs)
    body.write(end_boundary)
    body.write("\n")
    body = body.getvalue()

    logger.info("Submitting %s to %s" % (data['content'][0], repository))

    # build the Request
    # We can't use urllib2 since we need to send the Basic
    # auth right with the first request
    schema, netloc, url, params, query, fragments = \
        urlparse.urlparse(repository)
    assert not params and not query and not fragments
    if schema == 'http':
        http = httplib.HTTPConnection(netloc)
    elif schema == 'https':
        http = httplib.HTTPSConnection(netloc)
    else:
        raise AssertionError, "unsupported schema "+schema

    data = ''
    try:
        http.connect()
        http.putrequest("POST", url)
        http.putheader('Content-type',
                       'multipart/form-data; boundary=%s'%boundary)
        http.putheader('Content-length', str(len(body)))
        http.putheader('Authorization', auth)
        http.endheaders()
        http.send(body)
    except socket.error, e:
        logger.exception("")
        return

    r = http.getresponse()
    if r.status == 200:
        logger.info('Server response (%s): %s' % (r.status, r.reason))
        return True
    else:
        logger.error('Upload failed (%s): %s' % (r.status, r.reason))
        return False


def mirror_file(repository_config, filename, package_name, package_version, metadata):
    # merge the metadata with constant data that setuptools sends and data about the file.
    # then call the function that actually sends the post request.
    f = open(filename,'rb')
    content = f.read()
    f.close()
    basename = os.path.basename(filename)
    data = {
        ':action': 'file_upload',
        'protocol_version': '1',
        'metadata_version': '1.0',
        'content': (basename, content),
        'md5_digest': md5(content).hexdigest(),
        'name': package_name,
        'version': package_version,
    }

    data.update(metadata)

    for key, value in data.items():
        if isinstance(value, unicode):
            data[key] = value.encode("utf-8")

    repository = repository_config["repository"]
    username = repository_config.get("username", "")
    password = repository_config.get("password", "")
    send_setuptools_request(repository, username, password, data)

@contextmanager
def temp_urlretrieve(url, localpath):
    logger.info("Retrieving {}".format(url))
    urllib.urlretrieve(url, localpath)
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
