class Config(object):
	DEBUG=False
	TESTING=False
	SONG_ALLOWED_EXTENSIONS=["wav"]
	SCORE_ALLOWED_EXTENSIONS=["musicxml", "mxl"]

class DevelopmentConfig(Config):
	DEBUG=True
	ENV="development"
	SONG_UPLOAD_FOLDER="fred/static/tmp/songs"
	SCORE_UPLOAD_FOLDER="fred/static/tmp/scores"
	MIDI_FOLDER="fred/static/tmp/midi"
	SOUNDFONT_PATH="fred/soundfonts/fred_soundfont.sf2"
	SYNC_INFO_FOLDER="fred/static/tmp/json"
	SEND_FILE_MAX_AGE_DEFAULT = 0

class ProductionConfig(Config):
	ENV="production"