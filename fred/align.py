from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, json
from werkzeug.utils import secure_filename
from pathlib import Path
import numpy as np
import wave
import uuid
from fred.processing import mxl2wav, align_audios, default_params
from fred.exceptions import AlignmentError, ParamInputError, FileHandlingError, PostError


bp = Blueprint("align", __name__, url_prefix = "/align")

# route upload files page
@bp.route("/upload", methods = ("GET", "POST"))
def upload():
	"""
	Function to be executed when upload page is accessed.
	Handles POSTs by redirecting to the align page and calling the alignment function
	"""

	# change here to try except methods

	if request.method == "POST":
		try:
			# handle user input
			filename_mxl = handle_file_input('mxl-file', request.files, current_app.config["SCORE_ALLOWED_EXTENSIONS"])
			filenames_wav = handle_file_input('wav-files', request.files, current_app.config["SONG_ALLOWED_EXTENSIONS"])
			
			# check number of scores here?
			
			# get files and filenames
			filenames = filename_mxl + filenames_wav
			files = request.files.getlist('mxl-file') + request.files.getlist('wav-files')

			# save files
			filepaths = save_files(files, filenames)
			write_info_json(filepaths, request.form)

			# redirect to song page
			return redirect(url_for("align.recordings", num_audios=len(filenames_wav)+1))

		# handle input errors
		except (AlignmentError, FileHandlingError, ParamInputError) as e:
			flash(str(e))

		# handle bad post request errors
		except PostError as e:
			return render_template("error.html",
									error_code=400,
									error="Bad Request",
									message=str(e)), 400

		# if something goes wrong despite error handling -> send 500 error code
		except Exception as e:
			return render_template("error.html", 
									error_code=500, 
									error="Server Internal Error",
									message=str(e)), 500

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
	json_filepath = Path(current_app.config["SYNC_INFO_FOLDER"], "music_info.json")
	with json_filepath.open() as info_json:
		return json.load(info_json)

@bp.after_request
def add_no_cache_header(response):
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Pragma"] = "no-cache"
	response.headers["Expires"] = "0"
	response.headers['Cache-Control'] = 'public, max-age=0'
	return response

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

	# adapt here to raise exceptions?

	# error = None
	filenames = []

	if formname not in filedict:
		# Should never return this error message - only for when POST request is manually changed
		# error = "No {} part in form".format(formname)
		# return error, filenames
		raise PostError("No {} part in form".format(formname))

	files = filedict.getlist(formname)
	if (len(files) == 1) and (files[0].filename == ''):
		# In case no file was sent - Flask receives empty string as filename
		# error = "No {} uploaded".format(formname)
		# return error, filenames
		raise FileHandlingError("No {} uploaded".format(formname))

	for file in files:
		if not allowed_file(file.filename, allowed_extensions):
			# check file extension - should never appear either, file format is handled in html
			# error = "Extension not allowed for {}".format(formname)
			# return error, filenames
			raise FileHandlingError("Extension not allowed for {}".format(formname))
		filenames.append(secure_filename(file.filename))

	# return error, filenames
	return filenames

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
	An array of Path objects containing the filepaths where the files were saved.
	If an invalid extension is given, raises an exception. Path objects are easier to handle
	than strings and allow for creting directories more easily
	"""

	# create necessary directories, in case they do not exist
	create_tmp_dirs()

	filepaths = []
	for file, filename in zip(files, filenames):
		if filename.rsplit('.', 1)[-1].lower() in current_app.config["SCORE_ALLOWED_EXTENSIONS"]:
			filepath = Path(current_app.config["SCORE_UPLOAD_FOLDER"], filename)
		elif filename.rsplit('.', 1)[-1].lower() in current_app.config["SONG_ALLOWED_EXTENSIONS"]:
			filepath = Path(current_app.config["SONG_UPLOAD_FOLDER"], filename)
		else:
			# should never raise this exception - it means something went wrong during error handling
			raise FileHandlingError("Unallowed file extension")
		file.save(filepath)
		filepaths.append(filepath)
	return filepaths

def create_tmp_dirs():
	"""
	Procedure for creating tmp dirs required for fetching .wav, .mxl, and json, as well as saving midi files.

	"""
	Path(current_app.config["SONG_UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
	Path(current_app.config["SCORE_UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
	Path(current_app.config["MIDI_FOLDER"]).mkdir(parents=True, exist_ok=True)
	Path(current_app.config["SYNC_INFO_FOLDER"]).mkdir(parents=True, exist_ok=True)

def handle_params(form, fs):
	"""
	Function for properly handling form inputs and serve them to the alignment functions

	Arguments:
	form (ImmutableMultiDict) - Flask class for receiving form input. Behaves as dictionary
	fs (float) - Sampling frequency of one of the recordings. Used here to handle window size input 
	""" 
	
	# if new step size possibilities are added, other if statements should be added heres
	step_sizes = None
	if form["stepsize"] == "standard":
		step_sizes = np.asarray([(1,1), (1,0), (0,1)])
		weights = np.asarray([float(form["W1"]), float(form["W2"]), float(form["W3"])])

	params = {
		"n_fft": int(form["nfft"]),
		"window": form["window"],
		"win_length": int(round((float(form["winsize"])/1000)*fs)),
		"hop_length": int(round((1 - (float(form["overlap"])/100))*round((float(form["winsize"])/1000)*fs))),
		"center": True, # user does not get a choice on this parameter
		"norm": np.inf if form["norm"] == "inf" else int(form["norm"]),
		"epsilon": float(form["epsilon"]),
		"gamma": float(form["gamma"]),
		"metric": form["distance"],
		"step_sizes_sigma": step_sizes,
		"weights_add": np.asarray([0, 0, 0]), #user does not get a choice on this parameter
		"weights_mul": weights,
		"global_constraints": False if form["band"] == "false" else True,
		"band_rad": float(form["radius"])
	}

	if float(form["overlap"]) > 100:
		raise ParamInputError("Overlap cannot be greater than 100%")

	numerical_params = [params["n_fft"], params["win_length"], params["hop_length"], params["epsilon"], params["gamma"], params["band_rad"]]
	if any(i <= 0 for i in numerical_params):
		raise ParamInputError("All numerical parameters must be greater than zero")


	# Normally should not raise this error message. Something went wrong with POST request if this shows up
	if params["step_sizes_sigma"] is None:
		raise PostError("Invalid allowed steps")

	return params

def write_info_json(filepaths, form):
	"""
	Function for writing in json information about the score and recordings' filepath as well as frame sync equivalence.

	Arguments:
	filepaths (array of string) - array containing the filepaths of the files to be used in music page (mxl + wav)
	form (ImmutableMultiDict) - Flask class containing form values
	"""

	# data is the dictionary that will be serialized to json
	data = {}

	# store filenames in json dict
	data["score"] = [str(filepath) for filepath in filepaths if str(filepath).rsplit('.', 1)[-1].lower() in current_app.config["SCORE_ALLOWED_EXTENSIONS"]]
	data["recordings"] = [str(filepath) for filepath in filepaths if str(filepath).rsplit('.', 1)[-1].lower() in current_app.config["SONG_ALLOWED_EXTENSIONS"]]

	# synthesize midi
	data["recordings"].append(str(Path(current_app.config["SONG_UPLOAD_FOLDER"], "Synthesized_Score_" + "sid_" + str(uuid.uuid4()) + ".wav")))
	mxl2wav(data["score"][0], str(Path(current_app.config["MIDI_FOLDER"], "synthesized-score.mid")), data["recordings"][-1])

	# clean form params for use here
	# first off get sampling rate of first audio to go from win length in samples to win duration in seconds
	# since all audios are supposed to have the same fs, there should be no problem
	# if there is, align audios raises an exception that will be caught 
	with wave.open(data["recordings"][0], "rb") as wavfile:
		fs = wavfile.getframerate()

	params = handle_params(form, fs)

	# get frame sync info
	data["frame_equivalence"], fs = align_audios(data["recordings"], params)

	# write chroma params and dtw params for reference
	# put params separated by category inside data before submit
	data["chroma"] = {
		"sampling_rate": fs,
		"n_fft": params["n_fft"],
		"window": params["window"],
		"hop_length": params["hop_length"],
		"win_length": params["win_length"],
		"norm": "inf" if np.isinf(params["norm"]) else params["norm"],
		"epsilon": params["epsilon"],
		"gamma": params["gamma"]
	}

	data["dtw"] = {
		"distance": params["metric"],
		"allowed_steps": params["step_sizes_sigma"].tolist(),
		"weights_mul": params["weights_mul"].tolist(),
		"global_constraints": params["global_constraints"],
		"band_rad": params["band_rad"]
	}

	json_filepath = Path(current_app.config["SYNC_INFO_FOLDER"], "music_info.json")
	with json_filepath.open(mode="w") as info_json:
		json.dump(data, info_json)






