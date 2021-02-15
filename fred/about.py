from flask import Blueprint, render_template

# define blueprint
bp = Blueprint("about", __name__)

# route homepage
@bp.route("/")
def index():
	"""
	Function for rendering homepage template.
	Simple render template call, the page has just links and text
	"""
	return render_template("about/index.html")

@bp.route("/howitworks")
def howitworks():
	"""
	Same as homepage route
	"""
	return render_template("about/howitworks.html")

