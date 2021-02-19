from flask import Flask

def create_app():
	"""
	Function used for initializing web app
	"""

	# create Flask app, use instance relative config later?
	app = Flask(__name__, instance_relative_config=True)

	# load basic config
	app.config.from_object("config.DevelopmentConfig")
	# load instance config
	app.config.from_pyfile('config.py')

	from . import about
	app.register_blueprint(about.bp)
	app.add_url_rule("/", endpoint="index")

	from . import align
	app.register_blueprint(align.bp)

	return app


