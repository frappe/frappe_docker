"""
Deprecated v1 API client. To be removed once v2 is at parity with v1.
"""

from __future__ import absolute_import

import base64
from io import BytesIO
import os
import re
import six
import urllib
import warnings

if six.PY3:
    basestring = str  # pylint: disable=redefined-builtin,useless-suppression
    url_path_quote = urllib.parse.quote  # pylint: disable=no-member,useless-suppression
else:
    url_path_quote = urllib.quote  # pylint: disable=no-member,useless-suppression

try:
    import json
except ImportError:
    import simplejson as json

from .rest import ErrorResponse, RESTClient, params_to_urlencoded
from .session import BaseSession, DropboxSession, DropboxOAuth2Session


def format_path(path):
    """Normalize path for use with the Dropbox API.

    This function turns multiple adjacent slashes into single
    slashes, then ensures that there's a leading slash but
    not a trailing slash.
    """
    if not path:
        return path

    path = re.sub(r'/+', '/', path)

    if path == '/':
        return ''
    else:
        return '/' + path.strip('/')


class DropboxClient(object):
    """
    This is a deprecated class for making calls to the Dropbox v1 API. Please
    use the v2 API by instantiating :class:`dropbox.Dropbox` instead.

    All of the API call methods can raise a :class:`dropbox.rest.ErrorResponse`
    exception if the server returns a non-200 or invalid HTTP response. Note
    that a 401 return status at any point indicates that the access token
    you're using is no longer valid and the user must be put through the OAuth
    2 authorization flow again.
    """

    def __init__(self, oauth2_access_token, locale=None, rest_client=None):
        """Construct a ``DropboxClient`` instance.

        Parameters
          oauth2_access_token
            An OAuth 2 access token (string).  For backwards compatibility this may
            also be a DropboxSession object (see :meth:`create_oauth2_access_token()`).
          locale
            The locale of the user of your application.  For example "en" or "en_US".
            Some API calls return localized data and error messages; this setting
            tells the server which locale to use.  By default, the server uses "en_US".
          rest_client
            Optional :class:`dropbox.rest.RESTClient`-like object to use for making
            requests.
        """
        warnings.warn(
            'You are using a deprecated client. Please use the new v2 client '
            'located at dropbox.Dropbox.', DeprecationWarning, stacklevel=2)

        if rest_client is None:
            rest_client = RESTClient
        if isinstance(oauth2_access_token, basestring):
            if not _OAUTH2_ACCESS_TOKEN_PATTERN.match(oauth2_access_token):
                raise ValueError("invalid format for oauth2_access_token: %r"
                                 % (oauth2_access_token,))
            self.session = DropboxOAuth2Session(oauth2_access_token, locale)
        elif isinstance(oauth2_access_token, DropboxSession):
            # Backwards compatibility with OAuth 1
            if locale is not None:
                raise ValueError("The 'locale' parameter to DropboxClient is only useful "
                                 "when also passing in an OAuth 2 access token")
            self.session = oauth2_access_token
        else:
            raise ValueError("'oauth2_access_token' must either be a string or a DropboxSession")
        self.rest_client = rest_client

    def request(self, target, params=None, method='POST',
                content_server=False, notification_server=False):
        """
        An internal method that builds the url, headers, and params for a Dropbox API request.
        It is exposed if you need to make API calls not implemented in this library or if you
        need to debug requests.

        Parameters
            target
              The target URL with leading slash (e.g. '/files').
            params
              A dictionary of parameters to add to the request.
            method
              An HTTP method (e.g. 'GET' or 'POST').
            content_server
              A boolean indicating whether the request is to the
              API content server, for example to fetch the contents of a file
              rather than its metadata.
            notification_server
              A boolean indicating whether the request is to the API notification
              server, for example for longpolling.

        Returns
              A tuple of ``(url, params, headers)`` that should be used to make the request.
              OAuth will be added as needed within these fields.
        """
        assert method in ['GET', 'POST', 'PUT'], "Only 'GET', 'POST', and 'PUT' are allowed."
        assert not (content_server and notification_server), \
            "Cannot construct request simultaneously for content and notification servers."

        if params is None:
            params = {}

        if content_server:
            host = self.session.API_CONTENT_HOST
        elif notification_server:
            host = self.session.API_NOTIFICATION_HOST
        else:
            host = self.session.API_HOST

        headers, params = self.session.build_access_headers(params)

        if method in ('GET', 'PUT'):
            url = self.session.build_url(host, target, params)
        else:
            url = self.session.build_url(host, target)

        return url, params, headers

    def account_info(self):
        """Retrieve information about the user's account.

        Returns
              A dictionary containing account information.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#account-info
        """
        url, _, headers = self.request("/account/info", method='GET')
        return self.rest_client.GET(url, headers)

    def disable_access_token(self):
        """
        Disable the access token that this ``DropboxClient`` is using.  If this call
        succeeds, further API calls using this object will fail.
        """
        url, params, headers = self.request("/disable_access_token", method='POST')

        return self.rest_client.POST(url, params, headers)

    def create_oauth2_access_token(self):
        """
        If this ``DropboxClient`` was created with an OAuth 1 access token, this method
        can be used to create an equivalent OAuth 2 access token.  This can be used to
        upgrade your app's existing access tokens from OAuth 1 to OAuth 2.

        Example::

            from dropbox.client import DropboxClient
            from dropbox.session import DropboxSession
            session = DropboxSession(APP_KEY, APP_SECRET)
            access_key, access_secret = \
                '123abc', 'xyz456'  # Previously obtained OAuth 1 credentials
            session.set_token(access_key, access_secret)
            client = DropboxClient(session)
            token = client.create_oauth2_access_token()
            # Optionally, create a new client using the new token
            new_client = DropboxClient(token)
        """
        if not isinstance(self.session, DropboxSession):
            raise ValueError("This call requires a DropboxClient that is configured with an "
                             "OAuth 1 access token.")
        url, params, headers = self.request("/oauth2/token_from_oauth1", method='POST')

        r = self.rest_client.POST(url, params, headers)
        return r['access_token']

    def get_chunked_uploader(self, file_obj, length):
        """Creates a :class:`ChunkedUploader` to upload the given file-like object.

        Parameters
            file_obj
              The file-like object which is the source of the data
              being uploaded.
            length
              The number of bytes to upload.

        The expected use of this function is as follows::

            bigFile = open("data.txt", 'rb')

            uploader = myclient.get_chunked_uploader(bigFile, size)
            print "uploading: ", size
            while uploader.offset < size:
                try:
                    upload = uploader.upload_chunked()
                except rest.ErrorResponse, e:
                    # perform error handling and retry logic
            uploader.finish('/bigFile.txt')

        The SDK leaves the error handling and retry logic to the developer
        to implement, as the exact requirements will depend on the application
        involved.
        """
        return ChunkedUploader(self, file_obj, length)

    def upload_chunk(self, file_obj, length=None, offset=0,  # pylint: disable=unused-argument
            upload_id=None):
        """Uploads a single chunk of data from a string or file-like object. The majority of users
        should use the :class:`ChunkedUploader` object, which provides a simpler interface to the
        chunked_upload API endpoint.

        Parameters
            file_obj
              The source of the chunk to upload; a file-like object or a string.
            length
              This argument is ignored but still present for backward compatibility reasons.
            offset
              The byte offset to which this source data corresponds in the original file.
            upload_id
              The upload identifier for which this chunk should be uploaded,
              returned by a previous call, or None to start a new upload.

        Returns
            A dictionary containing the keys:

            upload_id
              A string used to identify the upload for subsequent calls to :meth:`upload_chunk()`
              and :meth:`commit_chunked_upload()`.
            offset
              The offset at which the next upload should be applied.
            expires
              The time after which this partial upload is invalid.
        """

        params = dict()

        if upload_id:
            params['upload_id'] = upload_id
            params['offset'] = offset

        url, _, headers = self.request("/chunked_upload", params,
            method='PUT', content_server=True)

        try:
            reply = self.rest_client.PUT(url, file_obj, headers)
            return reply['offset'], reply['upload_id']
        except ErrorResponse as e:
            raise e

    def commit_chunked_upload(self, full_path, upload_id, overwrite=False, parent_rev=None):
        """Commit the previously uploaded chunks for the given path.

        Parameters
            full_path
              The full path to which the chunks are uploaded, *including the file name*.
              If the destination folder does not yet exist, it will be created.
            upload_id
              The chunked upload identifier, previously returned from upload_chunk.
            overwrite
              Whether to overwrite an existing file at the given path. (Default ``False``.)
              If overwrite is False and a file already exists there, Dropbox
              will rename the upload to make sure it doesn't overwrite anything.
              You need to check the metadata returned for the new name.
              This field should only be True if your intent is to potentially
              clobber changes to a file that you don't know about.
            parent_rev
              Optional rev field from the 'parent' of this upload.
              If your intent is to update the file at the given path, you should
              pass the parent_rev parameter set to the rev value from the most recent
              metadata you have of the existing file at that path. If the server
              has a more recent version of the file at the specified path, it will
              automatically rename your uploaded file, spinning off a conflict.
              Using this parameter effectively causes the overwrite parameter to be ignored.
              The file will always be overwritten if you send the most recent parent_rev,
              and it will never be overwritten if you send a less recent one.

        Returns
            A dictionary containing the metadata of the newly committed file.

            For a detailed description of what this call returns, visit:
            https://www.dropbox.com/developers/core/docs#commit-chunked-upload
        """

        params = {
            'upload_id': upload_id,
            'overwrite': overwrite,
        }

        if parent_rev is not None:
            params['parent_rev'] = parent_rev

        url, params, headers = self.request("/commit_chunked_upload/%s" % full_path,
                                            params, content_server=True)

        return self.rest_client.POST(url, params, headers)

    def put_file(self, full_path, file_obj, overwrite=False, parent_rev=None):
        """Upload a file.

        A typical use case would be as follows::

            f = open('working-draft.txt', 'rb')
            response = client.put_file('/magnum-opus.txt', f)
            print "uploaded:", response

        which would return the metadata of the uploaded file, similar to::

            {
                'bytes': 77,
                'icon': 'page_white_text',
                'is_dir': False,
                'mime_type': 'text/plain',
                'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
                'path': '/magnum-opus.txt',
                'rev': '362e2029684fe',
                'revision': 221922,
                'root': 'dropbox',
                'size': '77 bytes',
                'thumb_exists': False
            }

        Parameters
            full_path
              The full path to upload the file to, *including the file name*.
              If the destination folder does not yet exist, it will be created.
            file_obj
              A file-like object to upload. If you would like, you can pass a string as file_obj.
            overwrite
              Whether to overwrite an existing file at the given path. (Default ``False``.)
              If overwrite is False and a file already exists there, Dropbox
              will rename the upload to make sure it doesn't overwrite anything.
              You need to check the metadata returned for the new name.
              This field should only be True if your intent is to potentially
              clobber changes to a file that you don't know about.
            parent_rev
              Optional rev field from the 'parent' of this upload.
              If your intent is to update the file at the given path, you should
              pass the parent_rev parameter set to the rev value from the most recent
              metadata you have of the existing file at that path. If the server
              has a more recent version of the file at the specified path, it will
              automatically rename your uploaded file, spinning off a conflict.
              Using this parameter effectively causes the overwrite parameter to be ignored.
              The file will always be overwritten if you send the most recent parent_rev,
              and it will never be overwritten if you send a less recent one.

        Returns
              A dictionary containing the metadata of the newly uploaded file.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#files-put

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 503: User over quota.
        """
        path = "/files_put/%s%s" % (self.session.root, format_path(full_path))

        params = {
            'overwrite': bool(overwrite),
        }

        if parent_rev is not None:
            params['parent_rev'] = parent_rev

        url, params, headers = self.request(path, params, method='PUT', content_server=True)

        return self.rest_client.PUT(url, file_obj, headers)

    def get_file(self, from_path, rev=None, start=None, length=None):
        """Download a file.

        Example::

            out = open('magnum-opus.txt', 'wb')
            with client.get_file('/magnum-opus.txt') as f:
                out.write(f.read())

        which would download the file ``magnum-opus.txt`` and write the contents into
        the file ``magnum-opus.txt`` on the local filesystem.

        Parameters
            from_path
              The path to the file to be downloaded.
            rev
              Optional previous rev value of the file to be downloaded.
            start
              Optional byte value from which to start downloading.
            length
              Optional length in bytes for partially downloading the file. If ``length`` is
              specified but ``start`` is not, then the last ``length`` bytes will be downloaded.
        Returns
              A :class:`dropbox.rest.RESTResponse` that is the HTTP response for
              the API request.  It is a file-like object that can be read from.  You
              must call ``close()`` when you're done.

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at the given path, or the file that was there was deleted.
              - 200: Request was okay but response was malformed in some way.
        """
        path = "/files/%s%s" % (self.session.root, format_path(from_path))

        params = {}
        if rev is not None:
            params['rev'] = rev

        url, params, headers = self.request(path, params, method='GET', content_server=True)
        if start is not None:
            if length:
                headers['Range'] = 'bytes=%s-%s' % (start, start + length - 1)
            else:
                headers['Range'] = 'bytes=%s-' % start
        elif length is not None:
            headers['Range'] = 'bytes=-%s' % length
        return self.rest_client.request("GET", url, headers=headers, raw_response=True)

    def get_file_and_metadata(self, from_path, rev=None):
        """Download a file alongwith its metadata.

        Acts as a thin wrapper around get_file() (see :meth:`get_file()` comments for
        more details)

        A typical usage looks like this::

            out = open('magnum-opus.txt', 'wb')
            f, metadata = client.get_file_and_metadata('/magnum-opus.txt')
            with f:
                out.write(f.read())

        Parameters
            from_path
              The path to the file to be downloaded.
            rev
              Optional previous rev value of the file to be downloaded.

        Returns
              A pair of ``(response, metadata)``:

              response
                A :class:`dropbox.rest.RESTResponse` that is the HTTP response for
                the API request.  It is a file-like object that can be read from.  You
                must call ``close()`` when you're done.
              metadata
                A dictionary containing the metadata of the file (see
                https://www.dropbox.com/developers/core/docs#metadata for details).

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at the given path, or the file that was there was deleted.
              - 200: Request was okay but response was malformed in some way.
        """
        file_res = self.get_file(from_path, rev)
        metadata = DropboxClient.__parse_metadata_as_dict(file_res)

        return file_res, metadata

    @staticmethod
    def __parse_metadata_as_dict(dropbox_raw_response):
        # Parses file metadata from a raw dropbox HTTP response, raising a
        # dropbox.rest.ErrorResponse if parsing fails.
        metadata = None
        for header, header_val in dropbox_raw_response.getheaders().items():
            if header.lower() == 'x-dropbox-metadata':
                try:
                    metadata = json.loads(header_val)
                except ValueError:
                    raise ErrorResponse(dropbox_raw_response, '')
        if not metadata:
            raise ErrorResponse(dropbox_raw_response, '')
        return metadata

    def delta(self, cursor=None, path_prefix=None, include_media_info=False):
        """A way of letting you keep up with changes to files and folders in a
        user's Dropbox.  You can periodically call delta() to get a list of "delta
        entries", which are instructions on how to update your local state to
        match the server's state.

        Parameters
          cursor
            On the first call, omit this argument (or pass in ``None``).  On
            subsequent calls, pass in the ``cursor`` string returned by the previous
            call.
          path_prefix
            If provided, results will be limited to files and folders
            whose paths are equal to or under ``path_prefix``.  The ``path_prefix`` is
            fixed for a given cursor.  Whatever ``path_prefix`` you use on the first
            ``delta()`` must also be passed in on subsequent calls that use the returned
            cursor.
          include_media_info
            If True, delta will return additional media info for photos and videos
            (the time a photo was taken, the GPS coordinates of a photo, etc.). There
            is a delay between when a file is uploaded to Dropbox and when this
            information is available; delta will only include a file in the changelist
            once its media info is ready. The value you use on the first ``delta()`` must
            also be passed in on subsequent calls that use the returned cursor.

        Returns
          A dict with four keys:

          entries
            A list of "delta entries" (described below).
          reset
            If ``True``, you should your local state to be an empty folder
            before processing the list of delta entries.  This is only ``True`` only
            in rare situations.
          cursor
            A string that is used to keep track of your current state.
            On the next call to delta(), pass in this value to return entries
            that were recorded since the cursor was returned.
          has_more
            If ``True``, then there are more entries available; you can
            call delta() again immediately to retrieve those entries.  If ``False``,
            then wait at least 5 minutes (preferably longer) before checking again.

        Delta Entries: Each entry is a 2-item list of one of following forms:

          - [*path*, *metadata*]: Indicates that there is a file/folder at the given
            path.  You should add the entry to your local path.  (The *metadata*
            value is the same as what would be returned by the ``metadata()`` call.)

            - If the new entry includes parent folders that don't yet exist in your
              local state, create those parent folders in your local state.  You
              will eventually get entries for those parent folders.
            - If the new entry is a file, replace whatever your local state has at
              *path* with the new entry.
            - If the new entry is a folder, check what your local state has at
              *path*.  If it's a file, replace it with the new entry.  If it's a
              folder, apply the new *metadata* to the folder, but do not modify
              the folder's children.
          - [*path*, ``None``]: Indicates that there is no file/folder at the *path* on
            Dropbox.  To update your local state to match, delete whatever is at *path*,
            including any children (you will sometimes also get "delete" delta entries
            for the children, but this is not guaranteed).  If your local state doesn't
            have anything at *path*, ignore this entry.

        Remember: Dropbox treats file names in a case-insensitive but case-preserving
        way.  To facilitate this, the *path* strings above are lower-cased versions of
        the actual path.  The *metadata* dicts have the original, case-preserved path.
        """
        path = "/delta"

        params = {'include_media_info': include_media_info}
        if cursor is not None:
            params['cursor'] = cursor
        if path_prefix is not None:
            params['path_prefix'] = path_prefix

        url, params, headers = self.request(path, params)

        return self.rest_client.POST(url, params, headers)

    def longpoll_delta(self, cursor, timeout=None):
        """A long-poll endpoint to wait for changes on an account. In conjunction with
        :meth:`delta()`, this call gives you a low-latency way to monitor an account for
        file changes.

        Note that this call goes to ``api-notify.dropbox.com`` instead of ``api.dropbox.com``.

        Unlike most other API endpoints, this call does not require OAuth authentication.
        The passed-in cursor can only be acquired via an authenticated call to :meth:`delta()`.

        Parameters
          cursor
            A delta cursor as returned from a call to :meth:`delta()`. Note that a cursor
            returned from a call to :meth:`delta()` with ``include_media_info=True`` is
            incompatible with ``longpoll_delta()`` and an error will be returned.
          timeout
            An optional integer indicating a timeout, in seconds. The default value is
            30 seconds, which is also the minimum allowed value. The maximum is 480
            seconds. The request will block for at most this length of time, plus up
            to 90 seconds of random jitter added to avoid the thundering herd problem.
            Care should be taken when using this parameter, as some network
            infrastructure does not support long timeouts.

        Returns
            The connection will block until there are changes available or a timeout occurs.
            The response will be a dictionary that looks like the following example::

              {"changes": false, "backoff": 60}

            For a detailed description of what this call returns, visit:
            https://www.dropbox.com/developers/core/docs#longpoll-delta

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (generally due to an invalid parameter; check e.error for details).
        """
        path = "/longpoll_delta"

        params = {'cursor': cursor}
        if timeout is not None:
            params['timeout'] = timeout

        url, params, headers = self.request(path, params, method='GET', notification_server=True)

        return self.rest_client.GET(url, headers)

    def create_copy_ref(self, from_path):
        """Creates and returns a copy ref for a specific file.  The copy ref can be
        used to instantly copy that file to the Dropbox of another account.

        Parameters
          path
            The path to the file for a copy ref to be created on.

        Returns
          A dictionary that looks like the following example::

            {"expires": "Fri, 31 Jan 2042 21:01:05 +0000", "copy_ref": "z1X6ATl6aWtzOGq0c3g5Ng"}

        """
        path = "/copy_ref/%s%s" % (self.session.root, format_path(from_path))

        url, _, headers = self.request(path, {}, method='GET')

        return self.rest_client.GET(url, headers)

    def add_copy_ref(self, copy_ref, to_path):
        """Adds the file referenced by the copy ref to the specified path

        Parameters
          copy_ref
            A copy ref string that was returned from a create_copy_ref call.
            The copy_ref can be created from any other Dropbox account, or from the same account.
          path
            The path to where the file will be created.

        Returns
            A dictionary containing the metadata of the new copy of the file.
         """
        path = "/fileops/copy"

        params = {'from_copy_ref': copy_ref,
                  'to_path': format_path(to_path),
                  'root': self.session.root}

        url, params, headers = self.request(path, params)

        return self.rest_client.POST(url, params, headers)

    def file_copy(self, from_path, to_path):
        """Copy a file or folder to a new location.

        Parameters
            from_path
              The path to the file or folder to be copied.
            to_path
              The destination path of the file or folder to be copied.
              This parameter should include the destination filename (e.g.
              from_path: '/test.txt', to_path: '/dir/test.txt'). If there's
              already a file at the to_path it will raise an ErrorResponse.

        Returns
              A dictionary containing the metadata of the new copy of the file or folder.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#fileops-copy

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 403: An invalid copy operation was attempted
                (e.g. there is already a file at the given destination,
                or trying to copy a shared folder).
              - 404: No file was found at given from_path.
              - 503: User over storage quota.
        """
        params = {
            'root': self.session.root,
            'from_path': format_path(from_path),
            'to_path': format_path(to_path),
        }

        url, params, headers = self.request("/fileops/copy", params)

        return self.rest_client.POST(url, params, headers)

    def file_create_folder(self, path):
        """Create a folder.

        Parameters
            path
              The path of the new folder.

        Returns
              A dictionary containing the metadata of the newly created folder.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#fileops-create-folder

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 403: A folder at that path already exists.
        """
        params = {'root': self.session.root, 'path': format_path(path)}

        url, params, headers = self.request("/fileops/create_folder", params)

        return self.rest_client.POST(url, params, headers)

    def file_delete(self, path):
        """Delete a file or folder.

        Parameters
            path
              The path of the file or folder.

        Returns
              A dictionary containing the metadata of the just deleted file.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#fileops-delete

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at the given path.
        """
        params = {'root': self.session.root, 'path': format_path(path)}

        url, params, headers = self.request("/fileops/delete", params)

        return self.rest_client.POST(url, params, headers)

    def file_move(self, from_path, to_path):
        """Move a file or folder to a new location.

        Parameters
            from_path
              The path to the file or folder to be moved.
            to_path
              The destination path of the file or folder to be moved.
              This parameter should include the destination filename (e.g. if
              ``from_path`` is ``'/test.txt'``, ``to_path`` might be
              ``'/dir/test.txt'``). If there's already a file at the
              ``to_path`` it will raise an ErrorResponse.

        Returns
              A dictionary containing the metadata of the new copy of the file or folder.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#fileops-move

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 403: An invalid move operation was attempted
                (e.g. there is already a file at the given destination,
                or moving a shared folder into a shared folder).
              - 404: No file was found at given from_path.
              - 503: User over storage quota.
        """
        params = {'root': self.session.root,
                  'from_path': format_path(from_path),
                  'to_path': format_path(to_path)}

        url, params, headers = self.request("/fileops/move", params)

        return self.rest_client.POST(url, params, headers)

    def metadata(self, path, list=True, file_limit=25000,  # pylint: disable=redefined-builtin
            hash=None, rev=None, include_deleted=False,  # pylint: disable=redefined-builtin
            include_media_info=False):
        """Retrieve metadata for a file or folder.

        A typical use would be::

            folder_metadata = client.metadata('/')
            print "metadata:", folder_metadata

        which would return the metadata of the root folder. This
        will look something like::

            {
                'bytes': 0,
                'contents': [
                    {
                       'bytes': 0,
                       'icon': 'folder',
                       'is_dir': True,
                       'modified': 'Thu, 25 Aug 2011 00:03:15 +0000',
                       'path': '/Sample Folder',
                       'rev': '803beb471',
                       'revision': 8,
                       'root': 'dropbox',
                       'size': '0 bytes',
                       'thumb_exists': False
                    },
                    {
                       'bytes': 77,
                       'icon': 'page_white_text',
                       'is_dir': False,
                       'mime_type': 'text/plain',
                       'modified': 'Wed, 20 Jul 2011 22:04:50 +0000',
                       'path': '/magnum-opus.txt',
                       'rev': '362e2029684fe',
                       'revision': 221922,
                       'root': 'dropbox',
                       'size': '77 bytes',
                       'thumb_exists': False
                    }
                ],
                'hash': 'efdac89c4da886a9cece1927e6c22977',
                'icon': 'folder',
                'is_dir': True,
                'path': '/',
                'root': 'app_folder',
                'size': '0 bytes',
                'thumb_exists': False
            }

        In this example, the root folder contains two things: ``Sample Folder``,
        which is a folder, and ``/magnum-opus.txt``, which is a text file 77 bytes long

        Parameters
            path
              The path to the file or folder.
            list
              Whether to list all contained files (only applies when
              path refers to a folder).
            file_limit
              The maximum number of file entries to return within
              a folder. If the number of files in the folder exceeds this
              limit, an exception is raised. The server will return at max
              25,000 files within a folder.
            hash
              Every folder listing has a hash parameter attached that
              can then be passed back into this function later to save on
              bandwidth. Rather than returning an unchanged folder's contents,
              the server will instead return a 304.
            rev
              Optional revision of the file to retrieve the metadata for.
              This parameter only applies for files. If omitted, you'll receive
              the most recent revision metadata.
            include_deleted
              When listing contained files, include files that have been deleted.
            include_media_info
              If True, includes additional media info for photos and videos if
              available (the time a photo was taken, the GPS coordinates of a photo,
              etc.).

        Returns
              A dictionary containing the metadata of the file or folder
              (and contained files if appropriate).

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#metadata

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 304: Current folder hash matches hash parameters, so contents are unchanged.
              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at given path.
              - 406: Too many file entries to return.
        """
        path = "/metadata/%s%s" % (self.session.root, format_path(path))

        params = {
            'file_limit': file_limit,
            'list': 'true',
            'include_deleted': include_deleted,
            'include_media_info': include_media_info,
        }

        if not list:
            params['list'] = 'false'
        if hash is not None:
            params['hash'] = hash
        if rev:
            params['rev'] = rev

        url, params, headers = self.request(path, params, method='GET')

        return self.rest_client.GET(url, headers)

    def thumbnail(self, from_path, size='m', format='JPEG'):  # pylint: disable=redefined-builtin
        """Download a thumbnail for an image.

        Parameters
            from_path
              The path to the file to be thumbnailed.
            size
              A string specifying the desired thumbnail size.  Currently
              supported sizes: ``"xs"`` (32x32), ``"s"`` (64x64), ``"m"`` (128x128),
              ``"l``" (640x480), ``"xl"`` (1024x768).
              Check https://www.dropbox.com/developers/core/docs#thumbnails for
              more details.
            format
              The image format the server should use for the returned
              thumbnail data.  Either ``"JPEG"`` or ``"PNG"``.

        Returns
              A :class:`dropbox.rest.RESTResponse` that is the HTTP response for
              the API request.  It is a file-like object that can be read from.  You
              must call ``close()`` when you're done.

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at the given from_path,
                or files of that type cannot be thumbnailed.
              - 415: Image is invalid and cannot be thumbnailed.
        """
        assert format in ['JPEG', 'PNG'], \
            "expected a thumbnail format of 'JPEG' or 'PNG', got %s" % format

        path = "/thumbnails/%s%s" % (self.session.root, format_path(from_path))
        url, _, headers = self.request(path, {'size': size, 'format': format},
                method='GET', content_server=True)
        return self.rest_client.request("GET", url, headers=headers, raw_response=True)

    def thumbnail_and_metadata(self, from_path, size='m', format='JPEG'):  # noqa: E501; pylint: disable=redefined-builtin
        """Download a thumbnail for an image alongwith its metadata.

        Acts as a thin wrapper around thumbnail() (see :meth:`thumbnail()` comments for
        more details)

        Parameters
            from_path
              The path to the file to be thumbnailed.
            size
              A string specifying the desired thumbnail size. See :meth:`thumbnail()`
              for details.
            format
              The image format the server should use for the returned
              thumbnail data.  Either ``"JPEG"`` or ``"PNG"``.

        Returns
              A pair of ``(response, metadata)``:

              response
                A :class:`dropbox.rest.RESTResponse` that is the HTTP response for
                the API request.  It is a file-like object that can be read from.  You
                must call ``close()`` when you're done.
              metadata
                A dictionary containing the metadata of the file whose thumbnail
                was downloaded (see https://www.dropbox.com/developers/core/docs#metadata
                for details).

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No file was found at the given from_path,
                or files of that type cannot be thumbnailed.
              - 415: Image is invalid and cannot be thumbnailed.
              - 200: Request was okay but response was malformed in some way.
        """
        thumbnail_res = self.thumbnail(from_path, size, format)
        metadata = DropboxClient.__parse_metadata_as_dict(thumbnail_res)

        return thumbnail_res, metadata

    def search(self, path, query, file_limit=1000, include_deleted=False):
        """Search folder for filenames matching query.

        Parameters
            path
              The folder to search within.
            query
              The query to search on (minimum 3 characters).
            file_limit
              The maximum number of file entries to return within a folder.
              The server will return at max 1,000 files.
            include_deleted
              Whether to include deleted files in search results.

        Returns
              A list of the metadata of all matching files (up to
              file_limit entries).  For a detailed description of what
              this call returns, visit:
              https://www.dropbox.com/developers/core/docs#search

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
        """
        path = "/search/%s%s" % (self.session.root, format_path(path))

        params = {
            'query': query,
            'file_limit': file_limit,
            'include_deleted': include_deleted,
        }

        url, params, headers = self.request(path, params)

        return self.rest_client.POST(url, params, headers)

    def revisions(self, path, rev_limit=1000):
        """Retrieve revisions of a file.

        Parameters
            path
              The file to fetch revisions for. Note that revisions
              are not available for folders.
            rev_limit
              The maximum number of file entries to return within
              a folder. The server will return at max 1,000 revisions.

        Returns
              A list of the metadata of all matching files (up to rev_limit entries).

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#revisions

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: No revisions were found at the given path.
        """
        path = "/revisions/%s%s" % (self.session.root, format_path(path))

        params = {
            'rev_limit': rev_limit,
        }

        url, params, headers = self.request(path, params, method='GET')

        return self.rest_client.GET(url, headers)

    def restore(self, path, rev):
        """Restore a file to a previous revision.

        Parameters
            path
              The file to restore. Note that folders can't be restored.
            rev
              A previous rev value of the file to be restored to.

        Returns
              A dictionary containing the metadata of the newly restored file.

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#restore

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: Unable to find the file at the given revision.
        """
        path = "/restore/%s%s" % (self.session.root, format_path(path))

        params = {
            'rev': rev,
        }

        url, params, headers = self.request(path, params)

        return self.rest_client.POST(url, params, headers)

    def media(self, path):
        """Get a temporary unauthenticated URL for a media file.

        All of Dropbox's API methods require OAuth, which may cause problems in
        situations where an application expects to be able to hit a URL multiple times
        (for example, a media player seeking around a video file). This method
        creates a time-limited URL that can be accessed without any authentication,
        and returns that to you, along with an expiration time.

        Parameters
            path
              The file to return a URL for. Folders are not supported.

        Returns
            A dictionary that looks like the following example::

              {'url': 'https://dl.dropboxusercontent.com/1/view/abcdefghijk/example',
               'expires': 'Thu, 16 Sep 2011 01:01:25 +0000'}

            For a detailed description of what this call returns, visit:
            https://www.dropbox.com/developers/core/docs#media

        Raises
            A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

            - 400: Bad request (may be due to many things; check e.error for details).
            - 404: Unable to find the file at the given path.
        """
        path = "/media/%s%s" % (self.session.root, format_path(path))

        url, _, headers = self.request(path, method='GET')

        return self.rest_client.GET(url, headers)

    def share(self, path, short_url=True):
        """Create a shareable link to a file or folder.

        Shareable links created on Dropbox are time-limited, but don't require any
        authentication, so they can be given out freely. The time limit should allow
        at least a day of shareability, though users have the ability to disable
        a link from their account if they like.

        Parameters
            path
              The file or folder to share.

        Returns
              A dictionary that looks like the following example::

                {'url': u'https://db.tt/c0mFuu1Y', 'expires': 'Tue, 01 Jan 2030 00:00:00 +0000'}

              For a detailed description of what this call returns, visit:
              https://www.dropbox.com/developers/core/docs#shares

        Raises
              A :class:`dropbox.rest.ErrorResponse` with an HTTP status of:

              - 400: Bad request (may be due to many things; check e.error for details).
              - 404: Unable to find the file at the given path.
        """
        path = "/shares/%s%s" % (self.session.root, format_path(path))

        params = {
            'short_url': short_url,
        }

        url, params, headers = self.request(path, params, method='GET')

        return self.rest_client.GET(url, headers)


class ChunkedUploader(object):
    """Contains the logic around a chunked upload, which uploads a
    large file to Dropbox via the /chunked_upload endpoint.
    """

    def __init__(self, client, file_obj, length):
        self.client = client
        self.offset = 0
        self.upload_id = None

        self.last_block = None
        self.file_obj = file_obj
        self.target_length = length

    def upload_chunked(self, chunk_size=4 * 1024 * 1024):
        """Uploads data from this ChunkedUploader's file_obj in chunks, until
        an error occurs. Throws an exception when an error occurs, and can
        be called again to resume the upload.

        Parameters
            chunk_size
              The number of bytes to put in each chunk. (Default 4 MB.)
        """

        while self.offset < self.target_length:
            next_chunk_size = min(chunk_size, self.target_length - self.offset)
            if self.last_block is None:
                self.last_block = self.file_obj.read(next_chunk_size)

            try:
                (self.offset, self.upload_id) = self.client.upload_chunk(
                    BytesIO(self.last_block), next_chunk_size, self.offset, self.upload_id)
                self.last_block = None
            except ErrorResponse as e:
                # Handle the case where the server tells us our offset is wrong.
                must_reraise = True
                if e.status == 400:
                    reply = e.body
                    if "offset" in reply and reply['offset'] != 0 and reply['offset'] > self.offset:
                        self.last_block = None
                        self.offset = reply['offset']
                        must_reraise = False
                if must_reraise:
                    raise

    def finish(self, path, overwrite=False, parent_rev=None):
        """Commits the bytes uploaded by this ChunkedUploader to a file
        in the users dropbox.

        Parameters
            path
              The full path of the file in the Dropbox.
            overwrite
              Whether to overwrite an existing file at the given path. (Default ``False``.)
              If overwrite is False and a file already exists there, Dropbox
              will rename the upload to make sure it doesn't overwrite anything.
              You need to check the metadata returned for the new name.
              This field should only be True if your intent is to potentially
              clobber changes to a file that you don't know about.
            parent_rev
              Optional rev field from the 'parent' of this upload.
              If your intent is to update the file at the given path, you should
              pass the parent_rev parameter set to the rev value from the most recent
              metadata you have of the existing file at that path. If the server
              has a more recent version of the file at the specified path, it will
              automatically rename your uploaded file, spinning off a conflict.
              Using this parameter effectively causes the overwrite parameter to be ignored.
              The file will always be overwritten if you send the most recent parent_rev,
              and it will never be overwritten if you send a less recent one.
        """

        path = "/commit_chunked_upload/%s%s" % (self.client.session.root, format_path(path))

        params = dict(
            overwrite=bool(overwrite),
            upload_id=self.upload_id,
        )

        if parent_rev is not None:
            params['parent_rev'] = parent_rev

        url, params, headers = self.client.request(path, params, content_server=True)

        return self.client.rest_client.POST(url, params, headers)


# Allow access of ChunkedUploader via DropboxClient for backwards compatibility.
DropboxClient.ChunkedUploader = ChunkedUploader


class DropboxOAuth2FlowBase(object):

    def __init__(self, consumer_key, consumer_secret, locale=None, rest_client=RESTClient):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.locale = locale
        self.rest_client = rest_client

    def _get_authorize_url(self, redirect_uri, state):
        params = dict(response_type='code',
                      client_id=self.consumer_key)
        if redirect_uri is not None:
            params['redirect_uri'] = redirect_uri
        if state is not None:
            params['state'] = state

        return self.build_url(BaseSession.WEB_HOST, '/oauth2/authorize', params)

    def _finish(self, code, redirect_uri):
        url = self.build_url(BaseSession.API_HOST, '/oauth2/token')
        params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.consumer_key,
            'client_secret': self.consumer_secret,
        }
        if self.locale is not None:
            params['locale'] = self.locale
        if redirect_uri is not None:
            params['redirect_uri'] = redirect_uri

        response = self.rest_client.POST(url, params=params)
        access_token = response["access_token"]
        user_id = response["uid"]
        return access_token, user_id

    def build_path(self, target, params=None):
        """Build the path component for an API URL.

        This method urlencodes the parameters, adds them
        to the end of the target url, and puts a marker for the API
        version in front.

        Parameters
            target
              A target url (e.g. '/files') to build upon.
            params
              Optional dictionary of parameters (name to value).

        Returns
            The path and parameters components of an API URL.
        """
        if six.PY2 and isinstance(target, six.text_type):
            target = target.encode("utf8")

        target_path = url_path_quote(target)

        params = params or {}
        params = params.copy()

        if self.locale:
            params['locale'] = self.locale

        if params:
            query_string = params_to_urlencoded(params)
            return "/%s%s?%s" % (BaseSession.API_VERSION, target_path, query_string)
        else:
            return "/%s%s" % (BaseSession.API_VERSION, target_path)

    def build_url(self, host, target, params=None):
        """Build an API URL.

        This method adds scheme and hostname to the path
        returned from build_path.

        Parameters
            target
              A target url (e.g. '/files') to build upon.
            params
              Optional dictionary of parameters (name to value).

        Returns
            The full API URL.
        """
        return "https://%s%s" % (host, self.build_path(target, params))


class DropboxOAuth2FlowNoRedirect(DropboxOAuth2FlowBase):
    """
    OAuth 2 authorization helper for apps that can't provide a redirect URI
    (such as the command-line example apps).

    Example::

        from dropbox.client import DropboxOAuth2FlowNoRedirect, DropboxClient
        from dropbox import rest as dbrest

        auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)

        authorize_url = auth_flow.start()
        print "1. Go to: " + authorize_url
        print "2. Click \\"Allow\\" (you might have to log in first)."
        print "3. Copy the authorization code."
        auth_code = raw_input("Enter the authorization code here: ").strip()

        try:
            access_token, user_id = auth_flow.finish(auth_code)
        except dbrest.ErrorResponse, e:
            print('Error: %s' % (e,))
            return

        c = DropboxClient(access_token)
    """

    def __init__(self, consumer_key, consumer_secret, locale=None, rest_client=None):
        """
        Construct an instance.

        Parameters
          consumer_key
            Your API app's "app key"
          consumer_secret
            Your API app's "app secret"
          locale
            The locale of the user of your application.  For example "en" or "en_US".
            Some API calls return localized data and error messages; this setting
            tells the server which locale to use.  By default, the server uses "en_US".
          rest_client
            Optional :class:`dropbox.rest.RESTClient`-like object to use for making
            requests.
        """
        if rest_client is None:
            rest_client = RESTClient
        super(DropboxOAuth2FlowNoRedirect, self).__init__(consumer_key, consumer_secret,
                                                          locale, rest_client)

    def start(self):
        """
        Starts the OAuth 2 authorization process.

        Returns
            The URL for a page on Dropbox's website.  This page will let the user "approve"
            your app, which gives your app permission to access the user's Dropbox account.
            Tell the user to visit this URL and approve your app.
        """
        return self._get_authorize_url(None, None)

    def finish(self, code):
        """
        If the user approves your app, they will be presented with an "authorization code".  Have
        the user copy/paste that authorization code into your app and then call this method to
        get an access token.

        Parameters
          code
            The authorization code shown to the user when they approved your app.

        Returns
            A pair of ``(access_token, user_id)``.  ``access_token`` is a string that
            can be passed to DropboxClient.  ``user_id`` is the Dropbox user ID (string) of the
            user that just approved your app.

        Raises
            The same exceptions as :meth:`DropboxOAuth2Flow.finish()`.
        """
        return self._finish(code, None)


class DropboxOAuth2Flow(DropboxOAuth2FlowBase):
    """
    OAuth 2 authorization helper.  Use this for web apps.

    OAuth 2 has a two-step authorization process.  The first step is having the user authorize
    your app.  The second involves getting an OAuth 2 access token from Dropbox.

    Example::

        from dropbox.client import DropboxOAuth2Flow, DropboxClient

        def get_dropbox_auth_flow(web_app_session):
            redirect_uri = "https://my-web-server.org/dropbox-auth-finish"
            return DropboxOAuth2Flow(APP_KEY, APP_SECRET, redirect_uri,
                                     web_app_session, "dropbox-auth-csrf-token")

        # URL handler for /dropbox-auth-start
        def dropbox_auth_start(web_app_session, request):
            authorize_url = get_dropbox_auth_flow(web_app_session).start()
            redirect_to(authorize_url)

        # URL handler for /dropbox-auth-finish
        def dropbox_auth_finish(web_app_session, request):
            try:
                access_token, user_id, url_state = \\
                        get_dropbox_auth_flow(web_app_session).finish(request.query_params)
            except DropboxOAuth2Flow.BadRequestException, e:
                http_status(400)
            except DropboxOAuth2Flow.BadStateException, e:
                # Start the auth flow again.
                redirect_to("/dropbox-auth-start")
            except DropboxOAuth2Flow.CsrfException, e:
                http_status(403)
            except DropboxOAuth2Flow.NotApprovedException, e:
                flash('Not approved?  Why not?')
                return redirect_to("/home")
            except DropboxOAuth2Flow.ProviderException, e:
                logger.log("Auth error: %s" % (e,))
                http_status(403)

    """

    def __init__(self, consumer_key, consumer_secret, redirect_uri, session,
                 csrf_token_session_key, locale=None, rest_client=None):
        """
        Construct an instance.

        Parameters
          consumer_key
            Your API app's "app key".
          consumer_secret
            Your API app's "app secret".
          redirect_uri
            The URI that the Dropbox server will redirect the user to after the user
            finishes authorizing your app.  This URI  must be HTTPS-based and pre-registered with
            the Dropbox servers, though localhost URIs are allowed without pre-registration and can
            be either HTTP or HTTPS.
          session
            A dict-like object that represents the current user's web session (will be
            used to save the CSRF token).
          csrf_token_session_key
            The key to use when storing the CSRF token in the session (for
            example: "dropbox-auth-csrf-token").
          locale
            The locale of the user of your application.  For example "en" or "en_US".
            Some API calls return localized data and error messages; this setting
            tells the server which locale to use.  By default, the server uses "en_US".
          rest_client
            Optional :class:`dropbox.rest.RESTClient`-like object to use for making
            requests.
        """
        if rest_client is None:
            rest_client = RESTClient
        super(DropboxOAuth2Flow, self).__init__(consumer_key, consumer_secret, locale, rest_client)
        self.redirect_uri = redirect_uri
        self.session = session
        self.csrf_token_session_key = csrf_token_session_key

    def start(self, url_state=None):
        """
        Starts the OAuth 2 authorization process.

        This function builds an "authorization URL".  You should redirect your user's browser to
        this URL, which will give them an opportunity to grant your app access to their Dropbox
        account.  When the user completes this process, they will be automatically redirected to
        the ``redirect_uri`` you passed in to the constructor.

        This function will also save a CSRF token to ``session[csrf_token_session_key]`` (as
        provided to the constructor).  This CSRF token will be checked on :meth:`finish()` to
        prevent request forgery.

        Parameters
          url_state
            Any data that you would like to keep in the URL through the
            authorization process.  This exact value will be returned to you by :meth:`finish()`.

        Returns
            The URL for a page on Dropbox's website.  This page will let the user "approve"
            your app, which gives your app permission to access the user's Dropbox account.
            Tell the user to visit this URL and approve your app.
        """
        csrf_token = base64.urlsafe_b64encode(os.urandom(16))  # PY3: Returns bytes
        if not isinstance(csrf_token, str):
            csrf_token = csrf_token.decode('utf-8')
        state = csrf_token
        if url_state is not None:
            state += "|" + url_state
        self.session[self.csrf_token_session_key] = csrf_token

        return self._get_authorize_url(self.redirect_uri, state)

    def finish(self, query_params):
        """
        Call this after the user has visited the authorize URL (see :meth:`start()`), approved your
        app and was redirected to your redirect URI.

        Parameters
          query_params
            The query parameters on the GET request to your redirect URI.

        Returns
          A tuple of ``(access_token, user_id, url_state)``.  ``access_token`` can be used to
          construct a :class:`DropboxClient`.  ``user_id`` is the Dropbox user ID (string) of the
          user that just approved your app.  ``url_state`` is the value you originally passed in to
          :meth:`start()`.

        Raises
          :class:`BadRequestException`
            If the redirect URL was missing parameters or if the given parameters were not valid.
          :class:`BadStateException`
            If there's no CSRF token in the session.
          :class:`CsrfException`
            If the ``'state'`` query parameter doesn't contain the CSRF token from the user's
            session.
          :class:`NotApprovedException`
            If the user chose not to approve your app.
          :class:`ProviderException`
            If Dropbox redirected to your redirect URI with some unexpected error identifier
            and error message.
        """
        # Check well-formedness of request.

        state = query_params.get('state')
        if state is None:
            raise self.BadRequestException("Missing query parameter 'state'.")

        error = query_params.get('error')
        error_description = query_params.get('error_description')
        code = query_params.get('code')

        if error is not None and code is not None:
            raise self.BadRequestException("Query parameters 'code' and 'error' are both set; "
                                           " only one must be set.")
        if error is None and code is None:
            raise self.BadRequestException("Neither query parameter 'code' or 'error' is set.")

        # Check CSRF token

        if self.csrf_token_session_key not in self.session:
            raise self.BadStateException("Missing CSRF token in session.")
        csrf_token_from_session = self.session[self.csrf_token_session_key]
        if len(csrf_token_from_session) <= 20:
            raise AssertionError("CSRF token unexpectedly short: %r" % (csrf_token_from_session,))

        split_pos = state.find('|')
        if split_pos < 0:
            given_csrf_token = state
            url_state = None
        else:
            given_csrf_token = state[0:split_pos]
            url_state = state[split_pos + 1:]

        if not _safe_equals(csrf_token_from_session, given_csrf_token):
            raise self.CsrfException("expected %r, got %r" % (csrf_token_from_session,
                                                              given_csrf_token))

        del self.session[self.csrf_token_session_key]

        # Check for error identifier

        if error is not None:
            if error == 'access_denied':
                # The user clicked "Deny"
                if error_description is None:
                    raise self.NotApprovedException("No additional description from Dropbox")
                else:
                    raise self.NotApprovedException("Additional description from Dropbox: " +
                                                    error_description)
            else:
                # All other errors
                full_message = error
                if error_description is not None:
                    full_message += ": " + error_description
                raise self.ProviderException(full_message)

        # If everything went ok, make the network call to get an access token.

        access_token, user_id = self._finish(code, self.redirect_uri)
        return access_token, user_id, url_state

    class BadRequestException(Exception):
        """
        Thrown if the redirect URL was missing parameters or if the
        given parameters were not valid.

        The recommended action is to show an HTTP 400 error page.
        """
        pass

    class BadStateException(Exception):
        """
        Thrown if all the parameters are correct, but there's no CSRF token in the session.  This
        probably means that the session expired.

        The recommended action is to redirect the user's browser to try the approval process again.
        """
        pass

    class CsrfException(Exception):
        """
        Thrown if the given 'state' parameter doesn't contain the CSRF
        token from the user's session.
        This is blocked to prevent CSRF attacks.

        The recommended action is to respond with an HTTP 403 error page.
        """
        pass

    class NotApprovedException(Exception):
        """
        The user chose not to approve your app.
        """
        pass

    class ProviderException(Exception):
        """
        Dropbox redirected to your redirect URI with some unexpected error identifier and error
        message.

        The recommended action is to log the error, tell the user something went wrong, and let
        them try again.
        """
        pass


def _safe_equals(a, b):
    if len(a) != len(b):
        return False
    res = 0
    for ca, cb in zip(a, b):
        res |= ord(ca) ^ ord(cb)
    return res == 0

# From the "Bearer" token spec, RFC 6750.
_OAUTH2_ACCESS_TOKEN_PATTERN = re.compile(r'\A[-_~/A-Za-z0-9\.\+]+=*\Z')
