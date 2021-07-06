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

function loadRecording(path, index, paths) {
	// create howl for the recording
	const sound = new Howl({
		src: [path],
		volume: 1,
		html5: true,
		onload: () => onLoadRecording(path, index, sound, paths.length)
	});

	// return a playback object containing all useful elements to be manipulated and the sound
	const playback = {
		sound: sound,
		idx: index,
		title: document.getElementById(`title-${index}`),
		recording: document.getElementById(`recording-${index}`),
		selector: document.getElementById(`selector-${index}`),
		progress: document.getElementById(`progress-${index}`),
		currentTime: document.getElementById(`current-time-${index}`)
	}
	return playback;
}

function onLoadRecording(path, index, sound, numberOfPaths) {
	// set correct title
	const title = document.getElementById(`title-${index}`);
	title.innerHTML = path.split("/").slice(-1)[0].replace(".wav", '').replace(/_/g, ' ')

	if (index === numberOfPaths-1) {
		title.innerHTML = title.innerHTML.replace(/sid [0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}$/i, '')
	}

	// set progress bar to zero
	const progressBar = document.getElementById(`progress-${index}`)
	progressBar.style.width = 0

	// set current time to zero
	const currentTime = document.getElementById(`current-time-${index}`)
	currentTime.innerHTML = "00:00"

	// set correct song length
	const songLength = sound.duration()
	const endTime = document.getElementById(`end-time-${index}`)
	endTime.innerHTML = secondToMinuteString(Math.round(songLength))
}


function play(playbacks) {
	playbacks.forEach((playback) => {
		if (playback.selector.checked && !playback.sound.playing())  {
			playback.sound.play()
		}
	})
}

function pause(playbacks) {
	playbacks.forEach((playback) => {
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
	const playbacks = paths.map((path, index, paths) => {
		return loadRecording(path, index, paths)
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


// function getCursorTimestamps(osmd) {

// 	// initialize variables
// 	let timestamps = [];
// 	let notes = [];
// 	let note = null;
// 	let timestamp = 0;
// 	let measure = null;
// 	let bpm = 0;
// 	let beat = 0;

// 	// reset cursor
// 	osmd.cursor.reset()

// 	// get iterator and sheet music objects
// 	const sheet = osmd.sheet
// 	const iterator = osmd.cursor.iterator

// 	while (!iterator.EndReached) {
// 		// since OSMD only renders one speed instruction per measure, we can accept this constraint and base ourselves on it
// 		measure = sheet.SourceMeasures[iterator.CurrentMeasureIndex]
// 		if (measure.TempoExpressions.length > 0) {
// 			beat = beatNamesAndValues[measure.TempoExpressions[0].InstantaneousTempo.beatUnit]
// 			if (measure.TempoExpressions[0].InstantaneousTempo.dotted) {
// 				beat = beat * 1.5;
// 			}
// 			bpm = measure.TempoInBPM;
// 		}
// 		timestamp = iterator.currentTimeStamp.realValue * (1/beat) * 60/bpm
// 		timestamps.push(timestamp);
// 		iterator.moveToNext()
// 	}
// 	return timestamps
// }

function getCursorTimestampsAndNotes(osmd) {

	// initialize variables
	let timestamps = [];
	let notes = [];
	let note = null;
	let timestamp = 0;
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
		timestamp = iterator.currentTimeStamp.realValue * (1/beat) * 60/bpm
		timestamps.push(timestamp);
		for (let i = 0; i < iterator.CurrentVoiceEntries.length; i++) {
			for (let j = 0; j < iterator.CurrentVoiceEntries[i].notes.length; j++) {
				note = iterator.CurrentVoiceEntries[i].notes[j]
				if((note != null) && (note.halfTone != 0)) {
					notes.push({"noteObject": note, "absoluteTimestamp": timestamp})
				}
			}
		}
		iterator.moveToNext()
	}
	return [timestamps, notes];
}

function moveCursor(songEquivalentTime, osmd, timestamps) {
	while(songEquivalentTime >= timestamps[1]) {
		osmd.cursor.next()
		timestamps.shift();
		osmd.cursor.cursorElement.scrollIntoView({behavior: "smooth", block: "center"})
	}
	return timestamps
}

function updateCursor(playback, osmd, timestamps, referencePlayback, musicInfo) {
	const cback = setInterval(() => {
		const songEquivalentTime = getEquivalentTime(referencePlayback, playback, musicInfo)
		timestamps = moveCursor(songEquivalentTime, osmd, timestamps)
	}, 10)
	playback.sound.on("stop", () => {
		clearInterval(cback);
	});
	playback.sound.on("pause", () => {
		clearInterval(cback);
	});
	return timestamps
}

function updateProgressBar(playback, timeValue) {
	const progressBar = playback.progress
	progressBar.style.width = `${(timeValue/playback.sound.duration())*100}%`
	progressBar.ariaValueNow = `${(timeValue/playback.sound.duration())*100}`
}

function updateProgressBars(playback, playbacks, musicInfo) {
	const cback = setInterval(() => {
		playbacks.forEach((plybck) => {
			const equivalentTime = getEquivalentTime(plybck, playback, musicInfo)
			updateProgressBar(plybck, equivalentTime)
		})
	}, 10)
	playback.sound.on("stop", () => {
		clearInterval(cback)
		playbacks.forEach((plybck) => {
			plybck.progress.style.width = 0
		})
	})
	playback.sound.on("pause", () => {
		clearInterval(cback)
	})
}

function updateElapsedTime(playback, timeValue) {
	const currentTime = playback.currentTime
	currentTime.innerHTML = secondToMinuteString(Math.round(timeValue))
}

function updateElapsedTimes(playback, playbacks, musicInfo) {
	const cback = setInterval(() => {
		playbacks.forEach((plybck) => {
			const equivalentTime = getEquivalentTime(plybck, playback, musicInfo)
			updateElapsedTime(plybck, equivalentTime)
		})
	}, 10)
	playback.sound.on("stop", () => {
		clearInterval(cback)
		currentTime.innerHTML = "00:00"
	})
	playback.sound.on("pause", () => {
		clearInterval(cback)
	})
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
	const [currentSongFrame, conversionError] = secondToFrame(currentSongTime, musicInfo["chroma"]["hop_length"], musicInfo["chroma"]["sampling_rate"])
	const equivalentFrames = musicInfo["frame_equivalence"][`${fromPlayback.idx};${toPlayback.idx}`]
		.filter((eqArray) => eqArray[0] === Math.floor(currentSongFrame))
		.map((eqArray) => eqArray[1])
	// add switch case for methods here ?
	// add handling if list is empty ?
	if (equivalentFrames.length <= 0) throw new Error("No equivalence between frames")
	const songEquivalentFrame = Math.round(equivalentFrames.reduce((sum, frame) => sum + frame)/equivalentFrames.length)
	const songEquivalentTime = frameToSecond(songEquivalentFrame, conversionError, musicInfo["chroma"]["hop_length"], musicInfo["chroma"]["sampling_rate"])
	return songEquivalentTime
}

function secondToFrame(time, hopLength, samplingRate) {
	frame = Math.round((time * samplingRate)/hopLength)
	error = (time * samplingRate)/hopLength - frame
	return [frame, error]
}

function frameToSecond(frame, error, hopLength, samplingRate) {
	return ((frame + error) * hopLength)/samplingRate
}

function secondToMinuteString(duration) {
	const minutes = (Math.floor(duration/60)).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false})
	const seconds = (duration % 60).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false})
	return `${minutes}:${seconds}`
}

function getProgressClickedPosition(progressContainer, mouseClick) {
	// essentially subtract container left bound from click position
	const elapsedProgress = mouseClick.pageX - progressContainer.offsetLeft
	// then multiply by the incremental value (max value/width)
	return elapsedProgress * 100 / progressContainer.offsetWidth
}

function onClickProgress(event, playback, playbacks, musicInfo) {
	// get progress bar and container for click handling
	const progressBar = playback.progress
	const progressBarContainer = progressBar.parentNode
	// get clicked position in progress bar (% of elapsed audio) and desired time for audio
	const clickedPosition = getProgressClickedPosition(progressBarContainer, event)
	const desiredTime = (clickedPosition/100) * playback.sound.duration()
	// seek desired position in correct playback
	playback.sound.seek(desiredTime)
	// adjust all other playbacks
	playbacks.forEach((plybck) => {
		const songEquivalentTime = getEquivalentTime(plybck, playback, musicInfo)
		plybck.sound.seek(songEquivalentTime)
		updateProgressBar(plybck, songEquivalentTime)
		updateElapsedTime(plybck, songEquivalentTime)
	})
}

function onClickScore(event, osmd, scoreContainer, notes, playbacks, referencePlayback, musicInfo) {
	const clickLocation = new opensheetmusicdisplay.PointF2D(event.pageX, event.pageY);
	const sheetLocation = getOSMDCoordinates(clickLocation, scoreContainer);
	const maxDist = new opensheetmusicdisplay.PointF2D(1,1);
	const nearestNote = osmd.GraphicSheet.GetNearestNote(sheetLocation, maxDist);
	const noteTimestamp = notes.filter((obj) => obj.noteObject === nearestNote.sourceNote)[0].absoluteTimestamp
	if(noteTimestamp === undefined) return null
	referencePlayback.sound.seek(noteTimestamp)
	playbacks.forEach((playback) => {
		const songEquivalentTime = getEquivalentTime(playback, referencePlayback, musicInfo)
		playback.sound.seek(songEquivalentTime)
		updateProgressBar(playback, songEquivalentTime)
		updateElapsedTime(playback, songEquivalentTime)
	})
	return [nearestNote, noteTimestamp]
}

function getOSMDCoordinates(clickLocation, scoreContainer) {
	const sheetX = (clickLocation.x - scoreContainer.offsetLeft) / 10;
	const sheetY = (clickLocation.y - scoreContainer.offsetTop) / 10;
	return new opensheetmusicdisplay.PointF2D(sheetX, sheetY);
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
		let [timestamps, notes] = getCursorTimestampsAndNotes(osmd)
		// let timestamps = getCursorTimestamps(osmd)
		let timestampsCopy = [...timestamps]

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

		// set click event graphic sheet
		scoreContainer = document.getElementById("score")
		scoreContainer.addEventListener("click", (e) => {
			const wasPlaying = playbacks.filter((plybck) => plybck.sound.playing()).length > 0
			pause(playbacks)
			const clickedNoteData = onClickScore(e, osmd, scoreContainer, notes, playbacks, referencePlayback, musicInfo)
			if (clickedNoteData !== null) {
				osmd.cursor.reset()
				timestampsCopy = [...timestamps]
				playbacks.forEach((playback) => timestampsCopy = updateCursor(playback, osmd, timestampsCopy, referencePlayback, musicInfo))
			}
			if (wasPlaying) play(playbacks)
		})
		
		osmd.cursor.show()
		

		// set callback for updating cursor and progress bar
		playbacks.forEach((playback) => {
			// progress bar click event for playback control
			playback.progress.parentNode.addEventListener("click", (e) => {
				const wasPlaying = playbacks.filter((plybck) => plybck.sound.playing()).length > 0
				pause(playbacks)
				onClickProgress(e, playback, playbacks, musicInfo)
				osmd.cursor.reset()
				timestampsCopy = [...timestamps]
				timestampsCopy = updateCursor(playback, osmd, timestampsCopy, referencePlayback, musicInfo)
				if (wasPlaying) play(playbacks)
			})
			// callbacks for updating cursor, progress bars and time
			playback.sound.on("play", () => {
				timestampsCopy = updateCursor(playback, osmd, timestampsCopy, referencePlayback, musicInfo)
				updateProgressBars(playback, playbacks, musicInfo)
				updateElapsedTimes(playback, playbacks, musicInfo)
			})
			playback.sound.on("stop", () => {
				osmd.cursor.reset()
				timestampsCopy = [...timestamps]
			})
			playback.sound.on("end", () => {
				osmd.cursor.reset()
				timestampsCopy = [...timestamps]
				playbacks.forEach((plybck) => {
					plybck.progress.style.width = 0
					plybck.currentTime.innerHTML = "00:00"
				})
			})
		})

		// unload sounds when user leaves page
		window.addEventListener("beforeunload", (event) => {
			Howler.unload()
			return null
		})

	} catch(err) {
		console.log("Error: ", err)
	}
}

main();





