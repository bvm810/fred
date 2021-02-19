class Config(object):
	DEBUG=False
	TESTING=False

class DevelopmentConfig(Config):
	DEBUG=True
	ENV="development"

class ProductionConfig(Config):
	ENV="production"