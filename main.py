from models.PlaylistSearch import PlaylistSearch
from db import MyDb
from spotify_api import SpotifyOAuth
from youtube_api import YoutubeWebApi


def main():
	create_db()
	update_spotify_db()
	update_youtube_db()
	songsdb = MyDb('youtube')
	songs = songsdb.get_distinct_colums('youtube', 'playlist_name')
	for s in songs:
		print(s)
		count = songsdb.get_value_with_condition('youtube', 'search_term', 0, {'playlist_name':s[0]})
		print(f'Has total {len(count.fetchall())} songs')

def print_db(name):
	db = MyDb(name)
	db.print_table(name)

def update_spotify_db():
	mydb = MyDb('playlist')
	songdb = MyDb('song')

	access_token = get_access_token()
	playlistSearch = PlaylistSearch(access_token)
	playlists = playlistSearch.get_user_playlists('.huong.')

	# filter playlist
	def should_use(title):
		titles = ['portlanding', 'throwwww', 'four-letter word', 'jam', 'old goodies', 'monicaxchandler', 'evening by the beach']
		return title in titles

	# get all the playlists from spotify
	for i in playlists:
		if should_use(i.title):
			mydb.insert_to_table('playlist', [i.title, i.spotify_link, i.youtube_link])

	# get all the song list from spotify, schema (name, spotify_link, playlist_name, youtube_link)
	mydb.process_data_from_table('playlist',
		lambda row: playlistSearch.get_songs_from_playlist(row['name'], row['spotify_link'], songdb), 0)

def update_youtube_db():
	db_name = 'song'
	songdb = MyDb(db_name)
	playlists = songdb.get_distinct_colums(db_name, 'playlist_name')
	youtubedb = MyDb('youtube')

	youtubeapi = YoutubeWebApi()
	youtubeapi.authenticate()

	for p in playlists:
		cond = {'playlist_name': p[0]}
		songdb.process_data_from_table(
			db_name,
			lambda row: youtubedb.insert_to_table(
				'youtube', (
					f"{row['name']} {row['artist']}",        # search_term
					youtubeapi.get_song(f"{row['name']} {row['artist']}"), # video_id
					p[0],                                     # playlist_name
					youtubeapi.create_playlist(p[0]))
				),
			0,
			cond
		)

def get_access_token():
	# api = SpotifyWebApi()
	# api.authenticate()
	api = SpotifyOAuth()
	return api.get_access_token()

def create_db():
	mydb = MyDb('playlist')
	mydb.build_db('playlist', args=('name', 'spotify_link', 'youtube_link'))
	songdb = MyDb('song')
	songdb.build_db('song', args=('name', 'artist', 'spotify_link', 'playlist_name'))

	# youtube db
	youtubedb = MyDb('youtube')
	youtubedb.build_db('youtube', args=('search_term', 'video_id', 'playlist_name', 'playlist_id'))

if __name__ == '__main__':
	main()