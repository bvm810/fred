import music21
import numpy as np
import matplotlib.pyplot as plt 
from midi2audio import FluidSynth
from flask import current_app
from librosa.core import load
from librosa.feature import chroma_stft
from librosa.sequence import dtw
from librosa.display import waveplot, specshow

default_params = {
	"norm": 2,
	"n_fft": 4096,
	"hop_length": 2048,
	"win_length": 4096,
	"window": "hanning",
	"center": False,
	"epsilon": 0.0001,
	"gamma": 10,
	"metric": "cosine",
	"step_sizes_sigma": np.asarray([(1,1), (1,0), (0,1)]),
	"weights_add": np.asarray([0, 0, 0]),
	"weights_mul": np.asarray([1, 3, 3]),
	"global_constraints": False,
	"band_rad": 0.0008
}


def mxl2midi(mxl_filepath, midi_filepath):
	m21_score = music21.converter.parse(mxl_filepath)
	m21_score.write("midi", midi_filepath)

def midi2wav(midi_filepath, wav_filepath):
	fs = FluidSynth(sound_font=current_app.config["SOUNDFONT_PATH"])
	fs.midi_to_audio(midi_filepath, wav_filepath)

def mxl2wav(mxl_filepath, midi_filepath, wav_filepath):
	mxl2midi(mxl_filepath, midi_filepath)
	midi2wav(midi_filepath, wav_filepath)

def plot_audio(filepath):
	x, fs = load(filepath, sr = None, mono = True)
	plt.figure(figsize=(16,4))
	waveplot(x,sr=fs)
	plt.title("Waveform for {}".format(filepath))
	plt.tight_layout()
	plt.show()

def chromagram(audio, fs, params):
	# params is dictionary with correct parameters for chroma_stft librosa convenience function
	# fill in docs with their meanings later on by checking librosa docs
	chromagram = chroma_stft(
		audio,
		fs,
		norm = params["norm"],
		n_fft = params["n_fft"],
		hop_length = params["hop_length"],
		win_length = params["win_length"],
		window = params["window"],
		center = params["center"]
	)

	# Normalization
	for column in chromagram.T:
		if np.linalg.norm(column, 2) < params["epsilon"]:
			column[...] = (1/np.sqrt(12)) * np.ones(12)

	# Compression
	chromagram = np.log10(1+params["gamma"]*chromagram)

	return chromagram

def plot_chroma(filepath, params):
	x, fs = load(filepath, sr = None, mono = True)
	cgram = chromagram(x, fs, params)

	plt.figure(figsize = (8,4))
	specshow(cgram, x_axis='time', y_axis='chroma', cmap='gray_r', hop_length=params["hop_length"])
	plt.title('Chroma Representation for {}'.format(filepath))
	plt.colorbar()
	plt.tight_layout()
	plt.show()


def align(filepath1, filepath2, params):
	x, fs_x = load(filepath1, sr = None, mono = True)
	y, fs_y = load(filepath2, sr = None, mono = True)

	if fs_x != fs_y:
		return Exception("Files have different sampling rates")

	fs = fs_x
	cgram_x = chromagram(x, fs, params)
	cgram_y = chromagram(y, fs, params)

	D, wp = dtw(
		X = cgram_x,
		Y = cgram_y,
		metric = params["metric"],
		step_sizes_sigma = params["step_sizes_sigma"],
		weights_add = params["weights_add"],
		weights_mul = params["weights_mul"],
		global_constraints = params["global_constraints"],
		band_rad = params["band_rad"]
		# add subseq, backtrack, return_steps
	)

	return D, wp, fs

def plot_align(filepath1, filepath2, params):
	D, wp, fs = align(filepath1, filepath2, params)
	wp_s = np.asarray(wp) * params["hop_length"]/fs

	fig = plt.figure(figsize=(6,6))
	ax = fig.add_subplot(1,1,1)
	specshow(D, x_axis='s', y_axis='s', cmap='gray_r', sr = fs, hop_length=params["hop_length"])
	imax = ax.imshow(D, cmap=plt.get_cmap('gray_r'), origin='lower', interpolation='nearest', aspect='auto')
	ax.plot(wp_s[:, 1], wp_s[:, 0], color='r', marker='o', markersize = 1)
	plt.title('Warping Path on Acc. Cost Matrix $D$')
	plt.colorbar()
	plt.show()

def align_audios(filepaths, params):
	frame_equivalences = {}
	for audio_i in filepaths:
		for audio_j in filepaths:
			ij_key = "{};{}".format(filepaths.index(audio_i), filepaths.index(audio_j))
			ji_key = "{};{}".format(filepaths.index(audio_j), filepaths.index(audio_i))
			if (audio_i != audio_j) and (ij_key not in frame_equivalences) and (ji_key not in frame_equivalences):
				_, frame_equivalence, fs = align(audio_i, audio_j, params)
				frame_equivalences["{};{}".format(filepaths.index(audio_i), filepaths.index(audio_j))] = frame_equivalence.tolist()
				frame_equivalences["{};{}".format(filepaths.index(audio_j), filepaths.index(audio_i))] = np.column_stack((frame_equivalence[:,1], frame_equivalence[:,0])).tolist()
	return frame_equivalences, fs

def test_align(filepaths, params):
	warp_dict = align_audios(filepaths, params)
	print(warp_dict)
	for key in warp_dict:
		audios = key.split(";")
		if not np.array_equal(warp_dict["{};{}".format(audios[0], audios[1])][:,0], warp_dict["{};{}".format(audios[1], audios[0])][:,1]):
			return False
		if not np.array_equal(warp_dict["{};{}".format(audios[0], audios[1])][:,1], warp_dict["{};{}".format(audios[1], audios[0])][:,0]):
			return False
	return True
	



