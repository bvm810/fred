from flask import Blueprint, render_template, request, redirect, url_for, flash

bp = Blueprint("align", __name__, url_prefix = "/align")

# route upload files page
@bp.route("/upload", methods = ("GET", "POST"))
def upload():
	"""
	Function to be executed when upload page is accessed.
	Handles POSTs by redirecting to the align page and calling the alignment function
	"""
	if request.method == "POST":
		# handle user input
		if error is None:
			# call align function to create JSON to be used by align page
			return redirect(url_for("align.music"))
		# flash error messages if any
		flash(error)
	return render_template("align/upload.html")

@bp.route("/music")
def music():
	"""
	Having the JSON with the files' infos we only need to render the template.
	It will be responsible for calling the necessary JS for the page to work.
	"""
	return render_template("align/music.html")


