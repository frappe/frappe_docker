import os
import pkg_resources
import ssl

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager


_TRUSTED_CERT_FILE = pkg_resources.resource_filename(__name__, 'trusted-certs.crt')


# TODO(kelkabany): We probably only want to instantiate this once so that even
# if multiple Dropbox objects are instantiated, they all share the same pool.
class _SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):  # noqa: E501; pylint: disable=arguments-differ
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       cert_reqs=ssl.CERT_REQUIRED,
                                       ca_certs=_TRUSTED_CERT_FILE,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

def pinned_session(pool_maxsize=8):
    http_adapter = _SSLAdapter(pool_connections=4,
                               pool_maxsize=pool_maxsize)

    _session = requests.session()
    _session.mount('https://', http_adapter)

    return _session

# ========================================================================
# Deprecated: The code below is included only to support the use of the
# old v1 client class. It will be removed once v2 is at parity with v1. Do
# not use this for any new functionality.
# ========================================================================

import random
import six
import time
import urllib

from . import rest

if six.PY2:
    from urlparse import parse_qs  # pylint: disable=import-error,useless-suppression
    url_path_quote = urllib.quote  # pylint: disable=no-member,useless-suppression
    url_encode = urllib.urlencode  # pylint: disable=no-member,useless-suppression
else:
    from urllib.parse import parse_qs  # noqa: E501; pylint: disable=import-error,no-name-in-module,useless-suppression
    url_path_quote = urllib.parse.quote  # pylint: disable=no-member,useless-suppression
    url_encode = urllib.parse.urlencode  # pylint: disable=no-member,useless-suppression

DOMAIN = os.environ.get('DROPBOX_DOMAIN', '.dropboxapi.com')

# Default short hostname for RPC-style routes.
HOST_API = 'api'

# Default short hostname for upload and download-style routes.
HOST_CONTENT = 'content'

# Default short hostname for longpoll routes.
HOST_NOTIFY = 'notify'

# Default short hostname for the Drobox website.
HOST_WWW = 'www'

API_HOST = os.environ.get('DROPBOX_API_HOST', HOST_API + DOMAIN)
API_CONTENT_HOST = os.environ.get('DROPBOX_API_CONTENT_HOST', HOST_CONTENT + DOMAIN)
API_NOTIFICATION_HOST = os.environ.get('DROPBOX_API_NOTIFY_HOST', HOST_NOTIFY + DOMAIN)
WEB_HOST = os.environ.get('DROPBOX_WEB_HOST', HOST_WWW + DOMAIN)

class OAuthToken(object):
    """
    A class representing an OAuth token. Contains two fields: ``key`` and
    ``secret``.
    """
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

class BaseSession(object):
    API_VERSION = 1

    def __init__(self, consumer_key, consumer_secret, access_type="auto",
            locale=None, rest_client=rest.RESTClient):
        """Initialize a DropboxSession object.

        Your consumer key and secret are available
        at https://www.dropbox.com/developers/apps

        Args:

            - ``access_type``: Either 'auto' (the default), 'dropbox', or
                'app_folder'. You probably don't need to specify this and should
                just use the default.
            - ``locale``: A locale string ('en', 'pt_PT', etc.) [optional]
                The locale setting will be used to translate any user-facing error
                messages that the server generates. At this time Dropbox supports
                'en', 'es', 'fr', 'de', and 'ja', though we will be supporting more
                languages in the future. If you send a language the server doesn't
                support, messages will remain in English. Look for these translated
                messages in rest.ErrorResponse exceptions as e.user_error_msg.

        """
        assert access_type in ['dropbox', 'app_folder', 'auto'], \
            "expected access_type of 'dropbox' or 'app_folder'"
        self.consumer_creds = OAuthToken(consumer_key, consumer_secret)
        self.token = None
        self.request_token = None
        self.root = 'sandbox' if access_type == 'app_folder' else access_type
        self.locale = locale
        self.rest_client = rest_client

    def is_linked(self):
        """Return whether the DropboxSession has an access token attached."""
        return bool(self.token)

    def unlink(self):
        """Remove any attached access token from the DropboxSession."""
        self.token = None

    def build_path(self, target, params=None):
        """Build the path component for an API URL.

        This method urlencodes the parameters, adds them
        to the end of the target url, and puts a marker for the API
        version in front.

        Args:
            - ``target``: A target url (e.g. '/files') to build upon.
            - ``params``: A dictionary of parameters (name to value). [optional]

        Returns:
            - The path and parameters components of an API URL.
        """
        if six.PY2 and isinstance(target, six.text_type):
            target = target.encode("utf8")

        target_path = url_path_quote(target)

        params = params or {}
        params = params.copy()

        if self.locale:
            params['locale'] = self.locale

        if params:
            return "/%s%s?%s" % (self.API_VERSION, target_path, url_encode(params))
        else:
            return "/%s%s" % (self.API_VERSION, target_path)

    def build_url(self, host, target, params=None):
        """Build an API URL.

        This method adds scheme and hostname to the path
        returned from build_path.

        Args:
            - ``target``: A target url (e.g. '/files') to build upon.
            - ``params``: A dictionary of parameters (name to value). [optional]

        Returns:
            - The full API URL.
        """
        return "https://%s%s" % (host, self.build_path(target, params))

BaseSession.API_HOST = API_HOST
BaseSession.API_CONTENT_HOST = API_CONTENT_HOST
BaseSession.API_NOTIFICATION_HOST = API_NOTIFICATION_HOST
BaseSession.WEB_HOST = WEB_HOST

class DropboxSession(BaseSession):

    def set_token(self, access_token, access_token_secret):
        """Attach an access token to the DropboxSession.

        Note that the access 'token' is made up of both a token string
        and a secret string.
        """
        self.token = OAuthToken(access_token, access_token_secret)

    def set_request_token(self, request_token, request_token_secret):
        """Attach an request token to the DropboxSession.

        Note that the request 'token' is made up of both a token string
        and a secret string.
        """
        self.request_token = OAuthToken(request_token, request_token_secret)

    def build_authorize_url(self, request_token, oauth_callback=None):
        """Build a request token authorization URL.

        After obtaining a request token, you'll need to send the user to
        the URL returned from this function so that they can confirm that
        they want to connect their account to your app.

        Args:
            - ``request_token``: A request token from obtain_request_token.
            - ``oauth_callback``: A url to redirect back to with the authorized
              request token.

        Returns:
            - An authorization for the given request token.
        """
        params = {'oauth_token': request_token.key,
                  }

        if oauth_callback:
            params['oauth_callback'] = oauth_callback

        return self.build_url(self.WEB_HOST, '/oauth/authorize', params)

    def obtain_request_token(self):
        """Obtain a request token from the Dropbox API.

        This is your first step in the OAuth process.  You call this to get a
        request_token from the Dropbox server that you can then use with
        DropboxSession.build_authorize_url() to get the user to authorize it.
        After it's authorized you use this token with
        DropboxSession.obtain_access_token() to get an access token.

        NOTE:  You should only need to do this once for each user, and then you
        can store the access token for that user for later operations.

        Returns:
            - An :py:class:`OAuthToken` object representing the
              request token Dropbox assigned to this app. Also attaches the
              request token as self.request_token.
        """
        self.token = None  # clear any token currently on the request
        url = self.build_url(self.API_HOST, '/oauth/request_token')
        headers, params = self.build_access_headers()

        response = self.rest_client.POST(url, headers=headers, params=params, raw_response=True)
        self.request_token = self._parse_token(response.read())
        return self.request_token

    def obtain_access_token(self, request_token=None):
        """Obtain an access token for a user.

        After you get a request token, and then send the user to the authorize
        URL, you can use the authorized request token with this method to get the
        access token to use for future operations. The access token is stored on
        the session object.

        Args:
            - ``request_token``: A request token from obtain_request_token. [optional]
              The request_token should have been authorized via the
              authorization url from build_authorize_url. If you don't pass
              a request_token, the fallback is self.request_token, which
              will exist if you previously called obtain_request_token on this
              DropboxSession instance.

        Returns:
            - An :py:class:`OAuthToken` object with fields ``key`` and ``secret``
              representing the access token Dropbox assigned to this app and
              user. Also attaches the access token as self.token.
        """
        request_token = request_token or self.request_token
        assert request_token, "No request_token available on the session. Please pass one."
        url = self.build_url(self.API_HOST, '/oauth/access_token')
        headers, params = self.build_access_headers(request_token=request_token)

        response = self.rest_client.POST(url, headers=headers, params=params, raw_response=True)
        self.token = self._parse_token(response.read())
        return self.token

    def build_access_headers(self, params=None, request_token=None):
        """Build OAuth access headers for a future request.

        Args:
            - ``params``: A dictionary of parameters to add to what's already on the url.
              Typically, this would consist of POST parameters.

        Returns:
            - A tuple of (header_dict, params) where header_dict is a dictionary
              of header names and values appropriate for passing into dropbox.rest.RESTClient
              and params is a dictionary like the one that was passed in, but augmented with
              oauth-related parameters as appropriate.
        """
        if params is None:
            params = {}
        else:
            params = params.copy()

        oauth_params = {
            'oauth_consumer_key': self.consumer_creds.key,
            'oauth_timestamp': self._generate_oauth_timestamp(),
            'oauth_nonce': self._generate_oauth_nonce(),
            'oauth_version': self._oauth_version(),
        }

        token = request_token if request_token is not None else self.token

        if token:
            oauth_params['oauth_token'] = token.key

        self._oauth_sign_request(oauth_params, self.consumer_creds, token)

        headers = {
            'Authorization':
                'OAuth %s' % ','.join(
                    '%s="%s"' % (k, v) for k, v in six.iteritems(oauth_params))}

        return headers, params

    @classmethod
    def _oauth_sign_request(cls, params, consumer_pair, token_pair):
        params.update({'oauth_signature_method': 'PLAINTEXT',
            'oauth_signature': ('%s&%s' % (consumer_pair.secret, token_pair.secret)
                if token_pair is not None else '%s&' % (consumer_pair.secret,))})

    @classmethod
    def _generate_oauth_timestamp(cls):
        return int(time.time())

    @classmethod
    def _generate_oauth_nonce(cls, length=8):
        return ''.join([str(random.SystemRandom().randint(0, 9)) for _ in range(length)])

    @classmethod
    def _oauth_version(cls):
        return '1.0'

    @classmethod
    def _parse_token(cls, s):
        if not s:
            raise ValueError("Invalid parameter string.")

        params = parse_qs(s, keep_blank_values=False)
        if not params:
            raise ValueError("Invalid parameter string: %r" % s)

        if six.PY2:
            oauth_token_key = 'oauth_token'
            oauth_token_secret_key = 'oauth_token_secret'
        else:
            oauth_token_key = b'oauth_token'
            oauth_token_secret_key = b'oauth_token_secret'
        try:
            key = params[oauth_token_key][0]
        except Exception:
            raise ValueError("'oauth_token' not found in OAuth request.")

        try:
            secret = params[oauth_token_secret_key][0]
        except Exception:
            raise ValueError("'oauth_token_secret' not found in "
                             "OAuth request.")

        return OAuthToken(key, secret)

# Don't use this class directly.
class DropboxOAuth2Session(BaseSession):

    def __init__(self, oauth2_access_token, locale, rest_client=rest.RESTClient):
        super(DropboxOAuth2Session, self).__init__("", "", "auto",
            locale=locale, rest_client=rest_client)
        self.access_token = oauth2_access_token

    def build_access_headers(self, params=None, token=None):
        assert token is None
        headers = {"Authorization": "Bearer " + self.access_token}
        return headers, params
