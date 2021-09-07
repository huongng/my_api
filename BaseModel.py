class BaseModel(object):
	def __init__(self, title, spotify_link, youtube_link) -> None:
		self.title = title
		self.spotify_link = spotify_link
		self.youtube_link = youtube_link

def test():
	print('test')