from flask import Flask

def create_app():
	"""
	Function used for initializing web app

	%%%%%%% Add config here later? %%%%%%%
	"""

	# create Flask app, use instance relative config
	app = Flask(__name__, instance_relative_config = True)

	# add config treatment code here if used

	from . import about
	app.register_blueprint(about.bp)
	app.add_url_rule("/", endpoint="index")

	from . import align
	app.register_blueprint(align.bp)

	return app


