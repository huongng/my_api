from models.Search import Search
import requests
from models.Playlist import Playlist
from urllib.parse import urlencode

class PlaylistSearch(Search):

	def __init__(self, access_token) -> None:
		super().__init__(access_token)

	def get_data(self, data=None):
		if data is None:
			return ''
		data_token = {}
		for kvp in data:
			data_token.update(kvp)

		return data_token

	def get_user_playlists(self, user_id):
		'''
		Get all playlists from specific user
		'''
		self.endpoint = f'https://api.spotify.com/v1/users/{user_id}/playlists'
		data = urlencode(self.get_data())
		lookup_url = self.build_url_lookup(data)
		print(lookup_url)
		r = requests.get(lookup_url, headers=self.get_headers())

		user_playlists = list()
		for i in r.json()['items']:
			playlist = Playlist(i['name'], i['href'], '')
			user_playlists.append(playlist)
		return user_playlists

	def get_songs_from_playlist(self, playlist_name, playlist_id, cursor):
		# self.endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
		fields = 'items(track(name,href,artists(name)))'
		data = { 'fields': fields }

		r = requests.get(url=f'{playlist_id}/tracks', params=urlencode(data), headers=self.get_headers())

		is_valid_response = r.status_code in range(200, 299)
		if is_valid_response:
			song_lists = r.json()['items']
			for song in song_lists:
				song = song['track']
				artist = song['artists'][0]['name']
				song_args = [song['name'], artist, song['href'], playlist_name]
				cursor.insert_to_table('song', song_args)
