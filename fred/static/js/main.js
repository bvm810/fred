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
	} catch(err) {
		console.log("Error: ", err)
	}
}

main();





