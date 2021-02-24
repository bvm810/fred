from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from os import path
from flask import json

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

			# get files and filenames
			filenames = filename_mxl + filenames_wav
			files = request.files.getlist('mxl-file') + request.files.getlist('wav-files')

			# save files
			try:
				filepaths = save_files(files, filenames)
			except:
				# if something goes wrong despite error handling, something is wrong during save
				# then send 500 error code
				return render_template("error.html", 
										error_code=500, 
										error="Server Internal Error",
										message="We're really sorry, but something went wrong while we were processing your files"), 500

			# write file infos to json
			write_info_json(filepaths)

			# redirect to song page
			return redirect(url_for("align.recordings", num_audios=len(filenames_wav)+1))

		if error_mxl is not None:
			flash(error_mxl)
		if error_wav is not None:
			flash(error_wav)
	return render_template("align/upload.html")

@bp.route("/<int:num_audios>/recordings")
def recordings(num_audios):
	"""
	Having the JSON with the files' infos we only need to render the template.
	It will be responsible for calling the necessary JS for the page to work.
	"""
	n_audios = num_audios
	return render_template("align/recordings.html", num_audios=n_audios)

@bp.route("/fetch")
def fetch():
	"""
	View used only to pass the music info JSON to the JS running in the browser

	Add session info here later on
	"""
	json_filepath = path.join(current_app.config["SYNC_INFO_FOLDER"], "music_info.json")
	with open(json_filepath, "r") as info_json:
		return json.load(info_json)


def handle_file_input(formname, filedict, allowed_extensions):
	"""
	Function for checking if file of type formname is in the filelist sent by the request and has appropriate extension
	
	Arguments:
	formname (string) - filelist dict key to search
	filedict (object) - request.files object
	allowed_extensions (array of string) - list of allowed extensions as in allowed_file

	Returns:
	If there is an error, returns a string to be flashed with the error message and an empty array.
	Otherwise returns None and an array of strings containing the filenames
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

	Returns:
	True if file is allowed, false otherwise
	"""
	return "." in filename and filename.rsplit('.', 1)[-1].lower() in allowed_extensions

def save_files(files, filenames):
	"""
	Function responsible for saving files for backend. 

	Arguments:
	files (array of objects) - array containing the file objects to be saved
	filenames (array of strings) - array containing the names to be given to the file

	Returns:
	An array of strings containing the filepaths where the files were saved.
	If an invalid extension is given, raises an exception
	"""

	filepaths = []
	for file, filename in zip(files, filenames):
		if filename.rsplit('.', 1)[-1].lower() in current_app.config["SCORE_ALLOWED_EXTENSIONS"]:
			filepath = path.join(current_app.config["SCORE_UPLOAD_FOLDER"], filename)
		elif filename.rsplit('.', 1)[-1].lower() in current_app.config["SONG_ALLOWED_EXTENSIONS"]:
			filepath = path.join(current_app.config["SONG_UPLOAD_FOLDER"], filename)
		else:
			# should never raise this exception - it means something went wrong during error handling
			raise Exception("Unallowed file extension")
		file.save(filepath)
		filepaths.append(filepath)
	return filepaths

def write_info_json(filepaths):
	"""
	Function for writing in json information about the score and recordings' filepath as well as frame sync equivalence.

	Arguments:
	filepaths (array of string) - array containing the filepaths of the files to be used in music page (mxl + wav)
	"""

	# data is the dictionary that will be serialized to json
	data = {}

	# store filenames in json dict
	data["score"] = [filepath for filepath in filepaths if filepath.rsplit('.', 1)[-1].lower() in current_app.config["SCORE_ALLOWED_EXTENSIONS"]]
	data["recordings"] = [filepath for filepath in filepaths if filepath.rsplit('.', 1)[-1].lower() in current_app.config["SONG_ALLOWED_EXTENSIONS"]]

	# synthesize midi
	

	# insert code for frame sync info here

	# write json file
	json_filepath = path.join(current_app.config["SYNC_INFO_FOLDER"], "music_info.json")
	with open(json_filepath, "w") as info_json:
		json.dump(data, info_json)







