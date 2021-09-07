from http.client import responses
import pickle
import os
import secrets
from urllib.parse import urlencode
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

YOUTUBE_API = 'youtube'
YOUTUBE_API_VERSION = 'v3'

class YoutubeWebApi():
	channel_id = 'UC_x5XG1OV2P6uZZ5FSM9Ttw'
	api_key = 'AIzaSyB2gqF3jj_nCVxvcsTXarW-HqdrZYfQZBU'
	credentials = None
	token_file = 'token.pickle'
	secret_file = '_client_secret.json'
	scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']

	def __init__(self) -> None:
		self.endpoint = 'https://developers.google.com/apis-explorer/#p/youtube/v3/'

	@property
	def service(self):
		if not self.credentials or not self.credentials.valid:
			self.authenticate()
		return build(YOUTUBE_API, YOUTUBE_API_VERSION, credentials=self.credentials)

	def authenticate(self):
		# check token.pickle
		if os.path.exists(self.token_file):
			print(f'Loading credentials from {self.token_file}')
			with open(self.token_file, 'rb') as token:
				self.credentials = pickle.load(token)
				print(self.credentials)

		if not self.credentials or not self.credentials.valid:
			if self.credentials and self.credentials.expired and self.credentials.refresh_token:
				print('Refreshing token')
				self.credentials.refresh(Request())
			else:
				print('fetching new token..')
				self.get_new_credentials()
				self.persist_new_credentials()

	def get_new_credentials(self):
		flow = InstalledAppFlow.from_client_secrets_file(self.secret_file, scopes=self.scopes)
		flow.run_local_server(authorization_prompt_message='', port=8080)
		self.credentials = flow.credentials

	def persist_new_credentials(self):
		with open(self.token_file, 'wb') as f:
			print('Persisting new credentials')
			pickle.dump(self.credentials, f)

	def get_channel_id(self):
		'''
		Get my channel id
		'''
		request = self.service.channels().list(part='id', mine=True)
		response = request.execute()
		return response['items'][0]['id']

	def get_all_playlists(self, channel_id=None):
		'''
		Get all playlists from my channel
		'''
		page_token = None
		request = self.service.playlists().list(part='snippet', channelId=channel_id)
		while True:
			response_list = request.execute()
			for entry in response_list['items']:
				print(entry.get('id'))
			page_token = response_list.get('nextPageToken')
			if not page_token:
				break
			request = self.service.playlists().list(part='snippet', channelId=channel_id, pageToken=page_token)

	def create_playlist(self, playlist_name):
		print(f'creating playlist {playlist_name}')
		# playlist api
		# build POST body
		snippet = {
			'snippet': {
				'title': playlist_name
			}
		}

		request = self.service.playlists().insert(part='snippet', body=snippet)
		response = request.execute()
		# return playlist id
		return response['id']

	def insert_to_playlist(self, playlist_id, video_id):
		add_video_request = self.service.playlistItems().insert(
        part="snippet",
        body={
                'snippet': {
                  'playlistId': playlist_id, 
                  'resourceId': {
                          'kind': 'youtube#video',
                      'videoId': video_id
                    }
                }
			}
		)

		print(add_video_request.json())

	def get_song(self, search_term):
		'''
		Use song search term (title, artist) to get back songid
		Sample response:
		{
			"kind": "youtube#searchListResponse",
			"etag": "z33YhqW7Bf-blKegJBCPRhpdcmM",
			"nextPageToken": "CAUQAA",
			"regionCode": "CA",
			"pageInfo": {
				"totalResults": 1000000,
				"resultsPerPage": 5
			},
			"items": [
				{
				"kind": "youtube#searchResult",
				"etag": "ue9Se8FeuRIMPGYsp_qW4uNcTaM",
				"id": {
					"kind": "youtube#video",
					"videoId": "_64nc_NLE_I"
				}
			]
		}
		'''
		request = self.service.search().list(
			part='snippet',
			q=f"{search_term}"
		)

		response = request.execute()

		# get first result
		result = response['items'][0]['id']['videoId']
		print(f"{search_term} - {result}")
		return result