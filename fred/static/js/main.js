const beatNamesAndValues = {
	double: 2,
	whole: 1,
	half: 1/2,
	quarter: 1/4,
	eighth: 1/8,
}

async function getMusicInfo(fetchUrl) {
	const response = await fetch(fetchUrl);
	const musicInfo = await response.json();
	return musicInfo;
}

async function loadMusicSheet(path, divId){
	// get sheet container and set styles
	const sheetContainer = document.getElementById(divId);
	sheetContainer.style.width = "90%";
	sheetContainer.style.margin = "auto";

	// create osmd object
	osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(
		sheetContainer,
		{
			autoResize: true, 
			backend: "svg", 
			drawTitle: false,
			drawComposer: false,
		}
	);

	// load sheet and render it
	await osmd.load(path);
	osmd.render();
	return osmd;
}

function loadRecording(path, index) {
	// create howl for the recording
	const sound = new Howl({
		src: [path],
		volume: 1,
		html5: true,
	});

	// on load change page appearance with titles and minutes
	sound.on("load", onLoadRecording(path, index));

	// return a playback objectcontaining all useful elements to be manipulated and the sound
	const playback = {
		sound: sound,
		idx: index,
		title: document.getElementById(`title-${index}`),
		recording: document.getElementById(`recording-${index}`),
		selector: document.getElementById(`selector-${index}`),
		progress: document.getElementById(`progress-${index}`),
	}
	return playback;
}

function onLoadRecording(path, index) {
	// set correct title
	const title = document.getElementById(`title-${index}`);
	title.innerHTML = path.split("/").slice(-1)[0].replace(".wav", '').replace(/_/g, ' ')

	// add song max and min times here to the progress bar here later as well
}


function play(playbacks) {
	playbacks.forEach((playback) => {
		if (playback.selector.checked && !playback.sound.playing())  {
			playback.sound.play()
		}
	})
}

function pause(playbacks) {
	playbacks.forEach((playback) => {[]
		playback.sound.pause()
	})
}

function stop(playbacks) {
	playbacks.forEach((playback) => {
		playback.sound.stop()
	})
}

function loadRecordings(paths) {
	// load recordings individually
	const playbacks = paths.map((path, index) => {
		return loadRecording(path, index)
	})

	// set play pause and stop functions
	const playBtn = document.getElementById("play-button");
	playBtn.addEventListener("click", () => play(playbacks));

	const pauseBtn = document.getElementById("pause-button");
	pauseBtn.addEventListener("click", () => pause(playbacks));

	const stopBtn = document.getElementById("stop-button");
	stopBtn.addEventListener("click", () => stop(playbacks));

	return playbacks;
}

function getCursorTimestamps(osmd) {

	// initialize variables
	let timestamps = [];
	let measure = null;
	let bpm = 0;
	let beat = 0;

	// reset cursor
	osmd.cursor.reset()

	// get iterator and sheet music objects
	const sheet = osmd.sheet
	const iterator = osmd.cursor.iterator

	while (!iterator.EndReached) {
		// since OSMD only renders one speed instruction per measure, we can accept this constraint and base ourselves on it
		measure = sheet.SourceMeasures[iterator.CurrentMeasureIndex]
		if (measure.TempoExpressions.length > 0) {
			beat = beatNamesAndValues[measure.TempoExpressions[0].InstantaneousTempo.beatUnit]
			if (measure.TempoExpressions[0].InstantaneousTempo.dotted) {
				beat = beat * 1.5;
			}
			bpm = measure.TempoInBPM;
		}
			
		timestamps.push(iterator.currentTimeStamp.realValue * (1/beat) * 60/bpm);
		iterator.moveToNext()
	}
	return timestamps;
}

function moveCursor(songEquivalentTime, cursor, timestamps) {
	while(songEquivalentTime >= timestamps[1]) {
		cursor.next()
		timestamps.shift();
	}
}

function updateCursor(playback, osmd, timestamps, referencePlayback, musicInfo) {
	const cback = setInterval(() => {
		const songEquivalentTime = getEquivalentTime(playback, referencePlayback, musicInfo)
		console.log(songEquivalentTime)
		moveCursor(songEquivalentTime, osmd.cursor, timestamps)
	}, 10)
	playback.sound.on("stop", () => {
		clearInterval(cback);
	});
}

function handleSelection(oldSelectorStates, selectorStates, playbacks, musicInfo) {
	oldSelectorStates = selectorStates
	selectorStates = Array.from(document.querySelectorAll(".song-selector"), selector => selector.checked)

	// get playback objects that we are moving to/from
	const oldPlayback = playbacks.filter((playback, index) => oldSelectorStates[index] === true)[0]
	const newPlayback = playbacks.filter((playback, index) => selectorStates[index] === true)[0]

	// flag used to see if audio was playing before selection -> if true should continue playing
	const wasPlaying = oldPlayback.sound.playing()

	// pause, then find where to set audio then set and play if was playing before
	pause(playbacks)
	const songEquivalentTime = getEquivalentTime(newPlayback, oldPlayback, musicInfo)
	newPlayback.sound.seek(songEquivalentTime)
	if (wasPlaying) play(playbacks)

	return [selectorStates, oldSelectorStates]
}

function getEquivalentTime(toPlayback, fromPlayback, musicInfo) {
	const currentSongTime = fromPlayback.sound.seek()
	if (fromPlayback.idx === toPlayback.idx) return currentSongTime
	const currentSongFrame = secondToFrame(currentSongTime, musicInfo["chroma"]["hop_length"], musicInfo["chroma"]["sampling_rate"])
	const equivalentFrames = musicInfo["frame_equivalence"][`${fromPlayback.idx};${toPlayback.idx}`]
		.filter((eqArray) => eqArray[0] === currentSongFrame)
		.map((eqArray) => eqArray[1])
	// add switch case for methods here ?
	// add handling if list is empty ?
	if (equivalentFrames.length <= 0) throw new Error("No equivalence between frames")
	const songEquivalentFrame = Math.round(equivalentFrames.reduce((sum, frame) => sum + frame)/equivalentFrames.length)
	const songEquivalentTime = frameToSecond(songEquivalentFrame, musicInfo["chroma"]["hop_length"], musicInfo["chroma"]["sampling_rate"])
	return songEquivalentTime
}

function secondToFrame(time, hopLength, samplingRate) {
	return Math.round((time * samplingRate)/hopLength)
}

function frameToSecond(frame, hopLength, samplingRate) {
	return (frame * hopLength)/samplingRate
}

async function main() {
	try {
		// get music info 
		const musicInfo = await getMusicInfo('/align/fetch');
		// get score file path
		const scoreFile = musicInfo['score'].map(s => s.replace('fred', ''));

		// Normally this is checked in the html of the upload form and in the backend, here for debug
		if (scoreFile.length > 1) {
			throw new Error('More than one file for music score')
		}
		// load sheet
		const osmd = await loadMusicSheet(scoreFile[0], 'score')
		let timestamps = getCursorTimestamps(osmd)

		// get recordings file paths
		const recordingFiles = musicInfo['recordings'].map(s => s.replace('fred', ''));
		// load recordings
		const playbacks = loadRecordings(recordingFiles)
		const referencePlayback = playbacks[playbacks.length - 1]

		// selector handling
		const selectors = Array.from(document.querySelectorAll(".song-selector"))
		let oldSelectorStates = []
		let selectorStates = selectors.map(selector => selector.checked)

		selectors.forEach((selector) => {
			selector.onclick = () => {
				[selectorStates, oldSelectorStates] = handleSelection(oldSelectorStates, selectorStates, playbacks, musicInfo)
			}
		})

		// show cursor
		osmd.cursor.show();

		// set callback for updating cursor
		playbacks.forEach((playback) => {
			let timestampsCopy = [...timestamps]
			playback.sound.on("play", () => {
				if (playback.sound.seek() === 0) {
					updateCursor(playback, osmd, timestampsCopy, referencePlayback, musicInfo)
				}
			})
			playback.sound.on("stop", () => {
				osmd.cursor.reset()
				timestampsCopy = [...timestamps]
			})
		})

	} catch(err) {
		console.log("Error: ", err)
	}
}

main();





