from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

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
		error = None
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

def handle_file_input(formname, filedict, allowed_extensions):
	"""
	Function for checking if file of type formname is in the filelist sent by the request and has appropriate extension
	
	Arguments:
	formname (string) - filelist dict key to search
	filedict (object) - request.files object
	allowed_extensions (array of string) - list of allowed extensions
	"""
	error = None
	filenames = []

	if formname not in filedict:
		# Should never return this error message - only for when POST request is manually changed
		error = "No {} part in form".format(formname)
		return error, filenames

	if filedict[formname] == "":
		# In case no file was sent - Flask receives empty string as filename
		error = "No {} file was uploaded".format(formname)
		return error, filenames

	files = filedict.getlist(formname)
	for file in files:
		if not allowed_file(file.filename, allowed_extensions):
			error = "Extension not allowed for {} file".format(formname)
			return error, filenames
		filenames.append(secure_filename(file.filename))

	return error, filenames

def allowed_file(filename, allowed_extensions):
	return "." in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


