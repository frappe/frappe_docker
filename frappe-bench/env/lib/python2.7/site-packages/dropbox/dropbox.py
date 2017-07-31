__all__ = [
    'Dropbox',
    'DropboxTeam',
    'create_session',
]

# This should always be 0.0.0 in master. Only update this after tagging
# before release.
__version__ = '7.3.1'

import contextlib
import json
import logging
import random
import six
import time

import requests

from . import files, stone_serializers
from .auth import (
    AuthError_validator,
    RateLimitError_validator,
)
from .base import DropboxBase
from .base_team import DropboxTeamBase
from .exceptions import (
    ApiError,
    AuthError,
    BadInputError,
    HttpError,
    InternalServerError,
    RateLimitError,
)
from .session import (
    API_CONTENT_HOST,
    API_HOST,
    API_NOTIFICATION_HOST,
    HOST_API,
    HOST_CONTENT,
    HOST_NOTIFY,
    pinned_session,
)


class RouteResult(object):
    """The successful result of a call to a route."""

    def __init__(self, obj_result, http_resp=None):
        """
        :param str obj_result: The result of a route not including the binary
            payload portion, if one exists. Must be serialized JSON.
        :param requests.models.Response http_resp: A raw HTTP response. It will
            be used to stream the binary-body payload of the response.
        """
        assert isinstance(obj_result, six.string_types), \
            'obj_result: expected string, got %r' % type(obj_result)
        if http_resp is not None:
            assert isinstance(http_resp, requests.models.Response), \
                'http_resp: expected requests.models.Response, got %r' % \
                type(http_resp)
        self.obj_result = obj_result
        self.http_resp = http_resp


class RouteErrorResult(object):
    """The error result of a call to a route."""

    def __init__(self, request_id, obj_result):
        """
        :param str request_id: A request_id can be shared with Dropbox Support
            to pinpoint the exact request that returns an error.
        :param str obj_result: The result of a route not including the binary
            payload portion, if one exists.
        """
        self.request_id = request_id
        self.obj_result = obj_result


def create_session(max_connections=8, proxies=None):
    """
    Creates a session object that can be used by multiple :class:`Dropbox` and
    :class:`DropboxTeam` instances. This lets you share a connection pool
    amongst them, as well as proxy parameters.


    :param int max_connections: Maximum connection pool size.
    :param dict proxies: See the `requests module
            <http://docs.python-requests.org/en/latest/user/advanced/#proxies>`_
            for more details.
    :rtype: :class:`requests.sessions.Session`. `See the requests module
        <http://docs.python-requests.org/en/latest/user/advanced/#session-objects>`_
        for more details.
    """
    # We only need as many pool_connections as we have unique hostnames.
    session = pinned_session(pool_maxsize=max_connections)
    if proxies:
        session.proxies = proxies
    return session


class _DropboxTransport(object):
    """
    Responsible for implementing the wire protocol for making requests to the
    Dropbox API.
    """

    _API_VERSION = '2'

    # Download style means that the route argument goes in a Dropbox-API-Arg
    # header, and the result comes back in a Dropbox-API-Result header. The
    # HTTP response body contains a binary payload.
    _ROUTE_STYLE_DOWNLOAD = 'download'

    # Upload style means that the route argument goes in a Dropbox-API-Arg
    # header. The HTTP request body contains a binary payload. The result
    # comes back in a Dropbox-API-Result header.
    _ROUTE_STYLE_UPLOAD = 'upload'

    # RPC style means that the argument and result of a route are contained in
    # the HTTP body.
    _ROUTE_STYLE_RPC = 'rpc'

    # This is the default longest time we'll block on receiving data from the server
    _DEFAULT_TIMEOUT = 30

    def __init__(self,
                 oauth2_access_token,
                 max_retries_on_error=4,
                 max_retries_on_rate_limit=None,
                 user_agent=None,
                 session=None,
                 headers=None,
                 timeout=_DEFAULT_TIMEOUT):
        """
        :param str oauth2_access_token: OAuth2 access token for making client
            requests.

        :param int max_retries_on_error: On 5xx errors, the number of times to
            retry.
        :param Optional[int] max_retries_on_rate_limit: On 429 errors, the
            number of times to retry. If `None`, always retries.
        :param str user_agent: The user agent to use when making requests. This
            helps us identify requests coming from your application. We
            recommend you use the format "AppName/Version". If set, we append
            "/OfficialDropboxPythonSDKv2/__version__" to the user_agent,
        :param session: If not provided, a new session (connection pool) is
            created. To share a session across multiple clients, use
            :func:`create_session`.
        :type session: :class:`requests.sessions.Session`
        :param dict headers: Additional headers to add to requests.
        :param Optional[float] timeout: Maximum duration in seconds that
            client will wait for any single packet from the
            server. After the timeout the client will give up on
            connection. If `None`, client will wait forever. Defaults
            to 30 seconds.
        """
        assert len(oauth2_access_token) > 0, \
            'OAuth2 access token cannot be empty.'
        assert headers is None or isinstance(headers, dict), \
            'Expected dict, got %r' % headers
        self._oauth2_access_token = oauth2_access_token

        self._max_retries_on_error = max_retries_on_error
        self._max_retries_on_rate_limit = max_retries_on_rate_limit
        if session:
            assert isinstance(session, requests.sessions.Session), \
                'Expected requests.sessions.Session, got %r' % session
            self._session = session
        else:
            self._session = create_session()
        self._headers = headers

        base_user_agent = 'OfficialDropboxPythonSDKv2/' + __version__
        if user_agent:
            self._raw_user_agent = user_agent
            self._user_agent = '{}/{}'.format(user_agent, base_user_agent)
        else:
            self._raw_user_agent = None
            self._user_agent = base_user_agent

        self._logger = logging.getLogger('dropbox')

        self._host_map = {HOST_API: API_HOST,
                          HOST_CONTENT: API_CONTENT_HOST,
                          HOST_NOTIFY: API_NOTIFICATION_HOST}

        self._timeout = timeout

    def request(self,
                route,
                namespace,
                request_arg,
                request_binary,
                timeout=None):
        """
        Makes a request to the Dropbox API and in the process validates that
        the route argument and result are the expected data types. The
        request_arg is converted to JSON based on the arg_data_type. Likewise,
        the response is deserialized from JSON and converted to an object based
        on the {result,error}_data_type.

        :param host: The Dropbox API host to connect to.
        :param route: The route to make the request to.
        :type route: :class:`.datatypes.stone_base.Route`
        :param request_arg: Argument for the route that conforms to the
            validator specified by route.arg_type.
        :param request_binary: String or file pointer representing the binary
            payload. Use None if there is no binary payload.
        :param Optional[float] timeout: Maximum duration in seconds
            that client will wait for any single packet from the
            server. After the timeout the client will give up on
            connection. If `None`, will use default timeout set on
            Dropbox object.  Defaults to `None`.
        :return: The route's result.
        """
        host = route.attrs['host'] or 'api'
        route_name = namespace + '/' + route.name
        route_style = route.attrs['style'] or 'rpc'
        serialized_arg = stone_serializers.json_encode(route.arg_type,
                                                       request_arg)

        if (timeout is None and
                route == files.list_folder_longpoll):
            # The client normally sends a timeout value to the
            # longpoll route. The server will respond after
            # <timeout> + random(0, 90) seconds. We increase the
            # socket timeout to the longpoll timeout value plus 90
            # seconds so that we don't cut the server response short
            # due to a shorter socket timeout.
            # NB: This is done here because base.py is auto-generated
            timeout = request_arg.timeout + 90

        res = self.request_json_string_with_retry(host,
                                                  route_name,
                                                  route_style,
                                                  serialized_arg,
                                                  request_binary,
                                                  timeout=timeout)
        decoded_obj_result = json.loads(res.obj_result)
        if isinstance(res, RouteResult):
            returned_data_type = route.result_type
            obj = decoded_obj_result
        elif isinstance(res, RouteErrorResult):
            returned_data_type = route.error_type
            obj = decoded_obj_result['error']
            user_message = decoded_obj_result.get('user_message')
            user_message_text = user_message and user_message.get('text')
            user_message_locale = user_message and user_message.get('locale')
        else:
            raise AssertionError('Expected RouteResult or RouteErrorResult, '
                                 'but res is %s' % type(res))

        deserialized_result = stone_serializers.json_compat_obj_decode(
            returned_data_type, obj, strict=False)

        if isinstance(res, RouteErrorResult):
            raise ApiError(res.request_id,
                           deserialized_result,
                           user_message_text,
                           user_message_locale)
        elif route_style == self._ROUTE_STYLE_DOWNLOAD:
            return (deserialized_result, res.http_resp)
        else:
            return deserialized_result

    def request_json_object(self,
                            host,
                            route_name,
                            route_style,
                            request_arg,
                            request_binary,
                            timeout=None):
        """
        Makes a request to the Dropbox API, taking a JSON-serializable Python
        object as an argument, and returning one as a response.

        :param host: The Dropbox API host to connect to.
        :param route_name: The name of the route to invoke.
        :param route_style: The style of the route.
        :param str request_arg: A JSON-serializable Python object representing
            the argument for the route.
        :param Optional[bytes] request_binary: Bytes representing the binary
            payload. Use None if there is no binary payload.
        :param Optional[float] timeout: Maximum duration in seconds
            that client will wait for any single packet from the
            server. After the timeout the client will give up on
            connection. If `None`, will use default timeout set on
            Dropbox object.  Defaults to `None`.
        :return: The route's result as a JSON-serializable Python object.
        """
        serialized_arg = json.dumps(request_arg)
        res = self.request_json_string_with_retry(host,
                                                  route_name,
                                                  route_style,
                                                  serialized_arg,
                                                  request_binary,
                                                  timeout=timeout)
        # This can throw a ValueError if the result is not deserializable,
        # but that would be completely unexpected.
        deserialized_result = json.loads(res.obj_result)
        if isinstance(res, RouteResult) and res.http_resp is not None:
            return (deserialized_result, res.http_resp)
        else:
            return deserialized_result

    def request_json_string_with_retry(self,
                                       host,
                                       route_name,
                                       route_style,
                                       request_json_arg,
                                       request_binary,
                                       timeout=None):
        """
        See :meth:`request_json_object` for description of parameters.

        :param request_json_arg: A string representing the serialized JSON
            argument to the route.
        """
        attempt = 0
        rate_limit_errors = 0
        while True:
            self._logger.info('Request to %s', route_name)
            try:
                return self.request_json_string(host,
                                                route_name,
                                                route_style,
                                                request_json_arg,
                                                request_binary,
                                                timeout=timeout)
            except InternalServerError as e:
                attempt += 1
                if attempt <= self._max_retries_on_error:
                    # Use exponential backoff
                    backoff = 2**attempt * random.random()
                    self._logger.info(
                        'HttpError status_code=%s: Retrying in %.1f seconds',
                        e.status_code, backoff)
                    time.sleep(backoff)
                else:
                    raise
            except RateLimitError as e:
                rate_limit_errors += 1
                if (self._max_retries_on_rate_limit is None or
                        self._max_retries_on_rate_limit >= rate_limit_errors):
                    # Set default backoff to 5 seconds.
                    backoff = e.backoff if e.backoff is not None else 5.0
                    self._logger.info(
                        'Ratelimit: Retrying in %.1f seconds.', backoff)
                    time.sleep(backoff)
                else:
                    raise

    def request_json_string(self,
                            host,
                            func_name,
                            route_style,
                            request_json_arg,
                            request_binary,
                            timeout=None):
        """
        See :meth:`request_json_string_with_retry` for description of
        parameters.
        """
        if host not in self._host_map:
            raise ValueError('Unknown value for host: %r' % host)

        if not isinstance(request_binary, (six.binary_type, type(None))):
            # Disallow streams and file-like objects even though the underlying
            # requests library supports them. This is to prevent incorrect
            # behavior when a non-rewindable stream is read from, but the
            # request fails and needs to be re-tried at a later time.
            raise TypeError('expected request_binary as binary type, got %s' %
                            type(request_binary))

        # Fully qualified hostname
        fq_hostname = self._host_map[host]
        url = self._get_route_url(fq_hostname, func_name)

        headers = {'User-Agent': self._user_agent}
        if host != HOST_NOTIFY:
            headers['Authorization'] = 'Bearer %s' % self._oauth2_access_token
            if self._headers:
                headers.update(self._headers)

        # The contents of the body of the HTTP request
        body = None
        # Whether the response should be streamed incrementally, or buffered
        # entirely. If stream is True, the caller is responsible for closing
        # the HTTP response.
        stream = False

        if route_style == self._ROUTE_STYLE_RPC:
            headers['Content-Type'] = 'application/json'
            body = request_json_arg
        elif route_style == self._ROUTE_STYLE_DOWNLOAD:
            headers['Dropbox-API-Arg'] = request_json_arg
            stream = True
        elif route_style == self._ROUTE_STYLE_UPLOAD:
            headers['Content-Type'] = 'application/octet-stream'
            headers['Dropbox-API-Arg'] = request_json_arg
            body = request_binary
        else:
            raise ValueError('Unknown operation style: %r' % route_style)

        if timeout is None:
            timeout = self._timeout

        r = self._session.post(url,
                               headers=headers,
                               data=body,
                               stream=stream,
                               verify=True,
                               timeout=timeout,
                               )

        request_id = r.headers.get('x-dropbox-request-id')
        if r.status_code >= 500:
            raise InternalServerError(request_id, r.status_code, r.text)
        elif r.status_code == 400:
            raise BadInputError(request_id, r.text)
        elif r.status_code == 401:
            assert r.headers.get('content-type') == 'application/json', (
                'Expected content-type to be application/json, got %r' %
                r.headers.get('content-type'))
            err = stone_serializers.json_compat_obj_decode(
                AuthError_validator, r.json()['error'])
            raise AuthError(request_id, err)
        elif r.status_code == 429:
            err = None
            if r.headers.get('content-type') == 'application/json':
                err = stone_serializers.json_compat_obj_decode(
                    RateLimitError_validator, r.json()['error'])
                retry_after = err.retry_after
            else:
                retry_after_str = r.headers.get('retry-after')
                if retry_after_str is not None:
                    retry_after = int(retry_after_str)
                else:
                    retry_after = None
            raise RateLimitError(request_id, err, retry_after)
        elif 200 <= r.status_code <= 299:
            if route_style == self._ROUTE_STYLE_DOWNLOAD:
                raw_resp = r.headers['dropbox-api-result']
            else:
                assert r.headers.get('content-type') == 'application/json', (
                    'Expected content-type to be application/json, got %r' %
                    r.headers.get('content-type'))
                raw_resp = r.content.decode('utf-8')
            if route_style == self._ROUTE_STYLE_DOWNLOAD:
                return RouteResult(raw_resp, r)
            else:
                return RouteResult(raw_resp)
        elif r.status_code in (403, 404, 409):
            raw_resp = r.content.decode('utf-8')
            return RouteErrorResult(request_id, raw_resp)
        else:
            raise HttpError(request_id, r.status_code, r.text)

    def _get_route_url(self, hostname, route_name):
        """Returns the URL of the route.

        :param str hostname: Hostname to make the request to.
        :param str route_name: Name of the route.
        :rtype: str
        """
        return 'https://{hostname}/{version}/{route_name}'.format(
            hostname=hostname,
            version=Dropbox._API_VERSION,
            route_name=route_name,
        )

    def _save_body_to_file(self, download_path, http_resp, chunksize=2**16):
        """
        Saves the body of an HTTP response to a file.

        :param str download_path: Local path to save data to.
        :param http_resp: The HTTP response whose body will be saved.
        :type http_resp: :class:`requests.models.Response`
        :rtype: None
        """
        with open(download_path, 'wb') as f:
            with contextlib.closing(http_resp):
                for c in http_resp.iter_content(chunksize):
                    f.write(c)


class Dropbox(_DropboxTransport, DropboxBase):
    """
    Use this class to make requests to the Dropbox API using a user's access
    token. Methods of this class are meant to act on the corresponding user's
    Dropbox.
    """
    pass


class DropboxTeam(_DropboxTransport, DropboxTeamBase):
    """
    Use this class to make requests to the Dropbox API using a team's access
    token. Methods of this class are meant to act on the team, but there is
    also an :meth:`as_user` method for assuming a team member's identity.
    """

    def as_user(self, team_member_id):
        """
        Allows a team credential to assume the identity of a member of the
        team.

        :return: A :class:`Dropbox` object that can be used to query on behalf
            of this member of the team.
        :rtype: Dropbox
        """
        new_headers = self._headers.copy() if self._headers else {}
        new_headers['Dropbox-API-Select-User'] = team_member_id
        return Dropbox(
            self._oauth2_access_token,
            max_retries_on_error=self._max_retries_on_error,
            max_retries_on_rate_limit=self._max_retries_on_rate_limit,
            user_agent=self._raw_user_agent,
            session=self._session,
            headers=new_headers,
        )
