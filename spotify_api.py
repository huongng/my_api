import base64
import time
from types import resolve_bases
from typing import List
import requests
import datetime
from urllib.parse import urlencode, urlparse, parse_qsl
import sys

from requests.models import Response
from models.Playlist import Playlist
from models.Song import Song
from db import MyDb
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from CacheFileHandler import CacheFileHandler
import logging

logger = logging.getLogger(__name__)

#####
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.auth_code = self.server.error = None
        try:
            state, auth_code = SpotifyOAuth.parse_auth_response_url(self.path)
            self.server.state = state
            self.server.auth_code = auth_code
        except Exception as error:
            self.server.error = error

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if self.server.auth_code:
            status = "successful"
        elif self.server.error:
            status = "failed ({})".format(self.server.error)
        else:
            self._write("<html><body><h1>Invalid request</h1></body></html>")
            return

        self._write("""<html>
<script>
window.close()
</script>
<body>
<h1>Authentication status: {}</h1>
This window can be closed.
<script>
window.close()
</script>
<button class="closeButton" style="cursor: pointer" onclick="window.close();">Close Window</button>
</body>
</html>""".format(status))

    def _write(self, text):
        return self.wfile.write(text.encode("utf-8"))

    def log_message(self, format, *args):
        return

def start_local_http_server(port=8080, handler=RequestHandler):
	server = HTTPServer(("localhost", port), handler)
	server.allow_reuse_address = True
	server.auth_code = None
	server.auth_token_form = None
	server.error = None
	return server


class SpotifyOAuth(object):
	client_id = '839c66965568435aadf5bbf8f4c9dd82'
	client_secret = '7c13eaf0552a46f484b3fc8835681e15'
	redirect_uri = "http://localhost:8080"
	scopes = ['user-read-email']
	OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
	OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"

	def __init__(self) -> None:
		from requests import api
		self._session = api
		self.cache_hander = CacheFileHandler()

	@staticmethod
	def parse_auth_response_url(url):
		query_s = urlparse(url).query
		form = dict(parse_qsl(query_s))
		if "error" in form:
			raise Exception("Received error from auth server: "
									"{}".format(form["error"]),
									error=form["error"])
		return tuple(form.get(param) for param in ["state", "code"])

	def get_authorization_url(self):
		data = {
			"client_id": self.client_id,
			"response_type": "code",
			"redirect_uri":  self.redirect_uri,
			"scope": " ".join(self.scopes),
			"show_dialog": True
		}

		urlparams = urlencode(data)
		return f'{self.OAUTH_AUTHORIZE_URL}?{urlparams}'

	def get_auth_response(self):
		print('authenticating...')
		return self._get_auth_response_local_server()

	def get_access_token(self, check_cache=True):
		if check_cache:
			token_info = self.validate_token(self.cache_hander.get_cached_token())
			if token_info is not None:
				if self.is_token_expired(token_info):
					token_info = self.refresh_access_token(token_info['refresh_token'])
				return token_info['access_token']

		payload = {
			'redirect_uri': self.redirect_uri,
			'code': self.get_auth_response(),
			'grant_type': 'authorization_code',
			'scope': ' '.join(self.scopes)
		}

		headers = self._make_authorization_headers()
		logger.debug(f"sending POST request to {self.OAUTH_AUTHORIZE_URL} with header {headers} and body {payload}")
		try:
			response = self._session.post(
				self.OAUTH_TOKEN_URL,
				data=payload,
				headers=headers,
				verify=True
			)
			response.raise_for_status()
			token_info = response.json()
			self._add_additional_data_to_token(token_info)
			self.cache_hander.save_token_to_cache(token_info)
			print(token_info)
			return token_info["access_token"]
		except requests.exceptions.HTTPError as httpError:
			print(payload)
			print(self.OAUTH_TOKEN_URL)
			self._handle_oauth_error(httpError)

	def refresh_access_token(self, refresh_token):
		data = {
			"client_id": self.client_id,
			"grant_type": "refresh_token",
			"refresh_token": refresh_token
		}
		headers = {"Content-Type": "application/x-www-form-urlencoded"}
		logger.debug(f"sending POST request to {self.OAUTH_AUTHORIZE_URL} with header {headers} and body {data}")

		try:
			response = self._session.post(
				self.OAUTH_TOKEN_URL,
				data=data,
				headers=headers,
				verify=True
			)
			response.raise_for_status()
			token_info = response.json()
			self._add_additional_data_to_token(token_info)
			self.cache_hander.save_token_to_cache(token_info)
			return token_info["access_token"]
		except requests.exceptions.HTTPError as httpError:
			self._handle_oauth_error(httpError)

	def validate_token(self, token_info):
		if token_info is None:
			return None

		if self.is_token_expired(token_info):
			token_info = self.refresh_access_token(token_info['refresh_token'])
		return token_info

	def _open_auth_url(self):
		auth_url = self.get_authorization_url()
		try:
			webbrowser.open(auth_url)
		except webbrowser.Error:
			print(f'error for {auth_url}')

	def _get_auth_response_local_server(self):
		server = start_local_http_server()
		self._open_auth_url()
		server.handle_request()

		return server.auth_code

	def _handle_oauth_error(self, error):
		print(error)

	def _make_authorization_headers(self):
		return self.get_token_headers()

	def _add_additional_data_to_token(self, token_info):
		token_info['expires_at'] = int(time.time()) + token_info['expires_in']

	def get_token_credentials(self) -> str:
		"""
		Returns a base64 encoded string
		"""
		client_creds = f"{self.client_id}:{self.client_secret}"
		client_creds_b64 = base64.b64encode(client_creds.encode())

		return client_creds_b64.decode()

	def get_token_headers(self) -> dict:
		token_headers = {
			"Authorization": f"Basic {self.get_token_credentials()}"
		}
		return token_headers

	def is_token_expired(self, token_info):
		now = int(time.time())
		print(token_info)
		return token_info['expires_at'] - now < 0

class SpotifyWebApi:
	# default const values
	client_id = '839c66965568435aadf5bbf8f4c9dd82'
	client_secret = '7c13eaf0552a46f484b3fc8835681e15'
	token_url = 'https://accounts.spotify.com/api/token'
	
	access_token = None
	access_token_expires = datetime.datetime.now
	is_access_token_expires = True

	def __init__(self) -> None:
		# encode the client id and secret 
		return

	def get_token_credentials(self) -> str:
		"""
		Returns a base64 encoded string
		"""
		client_creds = f"{self.client_id}:{self.client_secret}"
		client_creds_b64 = base64.b64encode(client_creds.encode())

		return client_creds_b64.decode()

	def get_token_headers(self) -> dict:
		token_headers = {
			"Authorization": f"Basic {self.get_token_credentials()}"
		}
		return token_headers

	def get_token_data(self):
		token_data = {
			'grant_type': 'client_credentials'
		}
		return token_data

	def authenticate(self) -> bool:
		# check access token available
		r = requests.post(headers=self.get_token_headers(), data=self.get_token_data(), url=self.token_url)
		is_valid_request = r.status_code in range(200, 300) # 400 above is invalid

		if not is_valid_request:
			return False

		now = datetime.datetime.now()
		token_response_data = r.json()
		self.access_token = token_response_data["access_token"]
		expires_in = token_response_data["expires_in"] # seconds
		self.expires = now + datetime.timedelta(seconds=expires_in)
		self.is_access_token_expires = self.expires > now

		# save access token
		return True
