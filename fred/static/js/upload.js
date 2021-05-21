/**
 * Function to add selected files to the uploaded files object
 * @param input {[DOM element]} Input tag of file upload form
 * @param uploadedFiles {[object]} Object containing name-file pair of uploaded files
 * @param ulID {[string]} Element ID of the unordered list of the filenames
 */
function addFile(input, uploadedFiles, ulId) {
	// get element where files are stored
	const submittedFiles = input.files
	// add them to the object containing the uploaded files 
	for (let i=0; i<submittedFiles.length; i++) {
		let filename = submittedFiles[i].name
		if(uploadedFiles[filename] === undefined) {
			uploadedFiles[filename] = submittedFiles[i]
		}
	}
	// add filenames to the ul element showing them
	fillUL(uploadedFiles, ulId)
}

/**
 * Removes a file from the uploadedFiles object
 * @param  uploadedFiles {[object]} Object containing all files as name-file pairs
 * @param  filename {[string]} Name of the file. Should be a key inside the object
 */
function removeFile(uploadedFiles, filename, ulId) {
	delete uploadedFiles[filename]
	fillUL(uploadedFiles, ulId)
}

/**
 * Function to fill in unordered list based on uploaded files object
 * @param  uploadedFiles {[object]} Object containing name-file pairs for uploaded files
 * @param  ulId {[string]} Element ID of the unordered list of the filenames
 */
function fillUL(uploadedFiles, ulId) {
	// fill in this function later with html elements to create nice list design
	const ul = document.getElementById(ulId)
	ul.innerHTML = ""
	for (let filename in uploadedFiles) {
		let li = document.createElement('li')
		li.textContent = filename
		let img = document.createElement('img')
		img.setAttribute('src', '/static/img/trash.svg')
		img.addEventListener('click', () => removeFile(uploadedFiles, filename, ulId))
		li.append(img)
		ul.append(li)
	}
}

/**
 * Right before submit, all the files in the uploadedFiles object need to be
 * in the input element so that they can be fetched correctly
 * @param  uploadedFiles {[object]} object containing all submitted files in name-file pairs
 * @param  input {[DOM Element]} Input element holding files
 */
function compileFiles(uploadedFiles, input) {
	// need to use data transfer to pass files from object to form
	const dt = new DataTransfer()
	for (let filename in uploadedFiles) {
		dt.items.add(uploadedFiles[filename])
	}
	input.files = dt.files
}

/**
 * Function to set up all buttons in page
 */
function main() {
	// set up mxl file submission
	let uploadedMxlFiles = {}
	const mxlFileInput = document.getElementById("mxlFileInput")
	mxlFileInput.addEventListener("change", () => {
		uploadedMxlFiles = {}
		addFile(mxlFileInput, uploadedMxlFiles, "mxl-file-ul")
	})

	// set up wav file submission
	const uploadedWavFiles = {}
	const wavFileInput = document.getElementById("wavFileInput")
	wavFileInput.addEventListener("change", () => {
		addFile(wavFileInput, uploadedWavFiles, "wav-file-ul")
	})

	// send correct files for submission
	const fileForm = document.getElementById("upload-form")
	fileForm.addEventListener("submit", () => {
		compileFiles(uploadedWavFiles, wavFileInput)
		compileFiles(uploadedMxlFiles, mxlFileInput)
	})

	// hide band radius input if needed
	const bandInput = document.getElementById("band")
	const radiusInput = document.getElementById("radius-input")
	bandInput.addEventListener("change", () => {
		if (bandInput.value === "true") {
			radiusInput.style.visibility = "visible"
		} else {
			radiusInput.style.visibility = "hidden"
		}
	})
}

main()



