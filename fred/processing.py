import music21
from midi2audio import FluidSynth
from flask import current_app

def mxl2midi(mxl_filepath, midi_filepath):
	m21_score = music21.converter.parse(mxl_filepath)
	m21_score.write("midi", midi_filepath)

def midi2wav(midi_filepath, wav_filepath):
	fs = FluidSynth(sound_font=current_app.config["SOUNDFONT_PATH"])
	fs.midi_to_audio(midi_filepath, wav_filepath)

def mxl2wav(mxl_filepath, midi_filepath, wav_filepath):
	mxl2midi(mxl_filepath, midi_filepath)
	midi2wav(midi_filepath, wav_filepath)
