class Config(object):
	DEBUG=False
	TESTING=False
	SONG_ALLOWED_EXTENSIONS=["wav"]
	SCORE_ALLOWED_EXTENSIONS=["musicxml", "mxl"]

class DevelopmentConfig(Config):
	DEBUG=True
	ENV="development"
	SONG_UPLOAD_FOLDER="tmp/songs"
	SCORE_UPLOAD_FOLDER="tmp/scores"
	SYNC_INFO_FOLDER="tmp/json"

class ProductionConfig(Config):
	ENV="production"