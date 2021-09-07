from models.BaseModel import BaseModel

class Playlist(BaseModel):
	def __init__(self, title, spotify_link, youtube_link) -> None:
		super().__init__(title, spotify_link, youtube_link)