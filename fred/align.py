from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from os import path

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
		error_mxl, filename_mxl = handle_file_input('mxl-file', request.files, current_app.config["SCORE_ALLOWED_EXTENSIONS"])
		error_wav, filenames_wav = handle_file_input('wav-files', request.files, current_app.config["SONG_ALLOWED_EXTENSIONS"])
		
		# if there is no error
		if (error_mxl is None) and (error_wav is None):
			# save files
			filename_mxl = filename_mxl[0]
			request.files['mxl-file'].save(path.join(current_app.config["SCORE_UPLOAD_FOLDER"], filename_mxl))
			for file, filename in zip(request.files.getlist('wav-files'), filenames_wav):
				file.save(path.join(current_app.config["SONG_UPLOAD_FOLDER"], filename))

			# call align function to create JSON to be used by align page

			# redirect to song page
			return redirect(url_for("align.music"))

		if error_mxl is not None:
			flash(error_mxl)
		if error_wav is not None:
			flash(error_wav)
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
	allowed_extensions (array of string) - list of allowed extensions as in allowed_file
	"""
	error = None
	filenames = []

	if formname not in filedict:
		# Should never return this error message - only for when POST request is manually changed
		error = "No {} part in form".format(formname)
		return error, filenames

	files = filedict.getlist(formname)
	if (len(files) == 1) and (files[0].filename == ''):
		# In case no file was sent - Flask receives empty string as filename
		error = "No {} uploaded".format(formname)
		return error, filenames

	for file in files:
		if not allowed_file(file.filename, allowed_extensions):
			# check file extension - should never appear either, file format is handled in html
			error = "Extension not allowed for {}".format(formname)
			return error, filenames
		filenames.append(secure_filename(file.filename))

	return error, filenames

def allowed_file(filename, allowed_extensions):
	"""
	Function to check file extension is among the supported ones

	Arguments:
	filename (string) - name of the file being checked
	allowed_extensions (array of string) - array of strings containing file extensions without "." 
	"""
	return "." in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


