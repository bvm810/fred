# Fred - A performance analysis website

## Description

This repo contains the code for my term paper at Universidade Federal do Rio de Janeiro (UFRJ). It is a wbesite designed for music education through performance analysis, where it is possible to listen and switch between different versions of the same musical work while also interactively following the score on the page. The full text of my term paper can be found [here](http://www.repositorio.poli.ufrj.br/monografias/projpoli10035746.pdf)

The project was created using the [Flask](https://flask.palletsprojects.com/en/2.0.x/) Python framework for web developping and vanilla HTML/CSS/JS for the front end. Audio processing is mostly done using the [librosa](https://librosa.org) package, and score interaction and rendering is possible thanks to [OpenSheetMusicDisplay](https://opensheetmusicdisplay.github.io).

## Dependencies

- [Python 3.8](https://www.python.org/downloads/)
- [Flask](https://flask.palletsprojects.com/en/2.0.x/)
- [librosa](https://librosa.org)
- [music21](http://web.mit.edu/music21/)
- [FluidSynth](https://www.fluidsynth.org)
- [Howler.js](https://howlerjs.com)
- [OpenSheetMusicDisplay](https://opensheetmusicdisplay.github.io)

## Installation

To run the website locally, first of all clone the repository into your computer using a terminal
```
git clone https://github.com/bvm810/term-paper.git /path/to/directory
```

Then, create a [virtual environment](https://docs.python.org/3/library/venv.html) to install dependencies locally and avoid conflicts with packages already installed in your machine. This project was created using Python 3.8.0, so make sure you have it on your machine and that `python` is the alias for this version of Python!

To manage the different versions of Python that might exist in your computer, you can use [pyenv](https://github.com/pyenv/pyenv).

Create and access the virtual environment using
```
cd /path/to/directory
python -m venv venv
source ./venv/bin/activate
```

To make sure that the environment is activated, check if there is a `(venv)` tag before your command prompt.

The project dependencies can then be installed locally with the command
```
pip install -r requirements.txt
```

MusicXML files are synthesized to audio through MIDI thanks to the [midi2audio](https://pypi.org/project/midi2audio/) package, which uses the [FluidSynth](https://www.fluidsynth.org) synthesizer. The installation that should be used depends on your OS.

- MacOS
```
brew install fluidsynth --with-libsndfile
```

- Ubuntu
```
sudo apt-get install fluidsynth --with-libsndfile
```

- Windows

On Windows, FluidSynth needs to be built from source as per the [documentation](https://github.com/FluidSynth/fluidsynth/wiki/BuildingWithCMake#common-tips-for-compiling-from-source)

In order to use FluidSynth, a soundfont is required. Any `.sf2` file will work, but the project was tested using [this](https://drive.google.com/file/d/1e5nPbx7_yPY6mNr3H1pInUgTKmGM6cHo/view) Steinway piano font. Chose the soundfont carefully as it can directly impact the performance of the alignment with the synthesized score!

Once you have downloaded your preferred soundfont, place it in a folder called `soundfonts` inside of the `fred` folder under the name `fred_soundfont.sf2`.
```
mkdir ./fred/soundfonts
cp /path/to/soundfont ./fred/soundfonts/fred_soundfont.sf2
```

You also should create the secret key that is going to be used by Flask. Normally it would be used for signing cookies, but in the current state of the project no session information is saved. Regardless, Flask might complain if he does not find this key, so its better to create it 

It should be created in the instance folder, which can be generated with the command
```
mkdir ./fred/instance
```

Inside this folder, place a python file named `config.py`, and insert this single line into it

```
SECRET_KEY=b'7\xdeg\xf2!\xfcgb\x8d\xa62\x1d\xaai\xd8\xe3'
```

You can change the value of the secret key, but it must be a long secret number

Finally, run the following commands with an active virtual environment
```
export FLASK_APP=fred
export FLASK_ENV=development
flask run
```

This should serve the website on `localhost:5000/`. 

## Credits

This project is largely inspired by Meinard Muller's excellent book, [Fundamentals of Music Processing](https://www.amazon.com/Fundamentals-Music-Processing-Algorithms-Applications/dp/3319219448)!

## License

This project is licensed under the GNU General Public License v3.0

