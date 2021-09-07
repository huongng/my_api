class Search(object):
	endpoint = 'https://api.spotify.com/v1/search'
	access_token = None

	def __init__(self, access_token) -> None:
		super().__init__()
		self.access_token = access_token

	def get_headers(self):
		header = f'Authorization: Bearer {self.access_token}'
		return {
			'Authorization': f'Bearer {self.access_token}'
		}

	def build_url_lookup(self, data):
		if data is None or data == '':
			return self.endpoint
		url_lookup = f'{self.endpoint}?{data}'
		return url_lookup