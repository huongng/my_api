import json
import errno
import os
import logging

logger = logging.getLogger(__name__)
CLIENT_CREDS_ENV_VARS = {
    "client_id": "SPOTIPY_CLIENT_ID",
    "client_secret": "SPOTIPY_CLIENT_SECRET",
    "client_username": "SPOTIPY_CLIENT_USERNAME",
    "redirect_uri": "SPOTIPY_REDIRECT_URI",
}

class CacheFileHandler(object):
	"""
    Handles reading and writing cached Spotify authorization tokens
    as json files on disk.
    """

	def __init__(self,
                 cache_path=None,
                 username=None):
		if cache_path:
			self.cache_path = cache_path
		else:
			cache_path = ".cache"
			username = (username or os.getenv(CLIENT_CREDS_ENV_VARS["client_username"]))
			if username:
				cache_path += "-" + str(username)
			self.cache_path = cache_path

	def get_cached_token(self):
		token_info = None

		try:
			f = open(self.cache_path)
			token_info_string = f.read()
			f.close()
			token_info = json.loads(token_info_string)

		except IOError as error:
			if error.errno == errno.ENOENT:
				logger.debug("cache does not exist at: %s", self.cache_path)
			else:
				logger.warning("Couldn't read cache at: %s", self.cache_path)
		return token_info

	def save_token_to_cache(self, token_info):
		try:
			print(self.cache_path)
			print(token_info)
			f = open(self.cache_path, "w")
			f.write(json.dumps(token_info))
			f.close()
		except IOError:
			logger.warning('Couldn\'t write token to cache at: %s',
						self.cache_path)