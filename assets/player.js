
var script = document.createElement('script'); script.src = "//cdn.jsdelivr.net/npm/eruda"; document.body.appendChild(script); script.onload = function () { eruda.init() };



const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);



//const player = new Plyr('#player');
var controls =
	[
		'play-large', // The large play button in the center
		//'restart', // Restart playback
		'rewind', // Rewind by the seek time (default 10 seconds)
		'play', // Play/pause playback
		'fast-forward', // Fast forward by the seek time (default 10 seconds)
		'progress', // The progress bar and scrubber for playback and buffering
		'current-time', // The current time of playback
		'duration', // The full duration of the media
		'mute', // Toggle mute
		'volume', // Volume control // Will be hidden on Android as they have Device Volume controls
		//'captions', // Toggle captions
		'settings', // Settings menu
		//'pip', // Picture-in-picture (currently Safari only)
		//'airplay', // Airplay (currently Safari only)
		//'download', // Show a download button with a link to either the current source or a custom URL you specify in your options
		'fullscreen' // Toggle fullscreen
	];

//CUSTOMIZE MORE USING THIS:
// https://stackoverflow.com/a/61577582/11071949

var player = new Plyr('#player', { controls });

// Remove all dblclick stuffs
player.eventListeners.forEach(function (eventListener) {
	if (eventListener.type === 'dblclick') {
		eventListener.element.removeEventListener(eventListener.type, eventListener.callback, eventListener.options);
	}
});


// Create overlay that will show the skipped time
const skip_ol = createElement("div");
skip_ol.id = "plyr__time_skip"
byClass("plyr")[0].appendChild(skip_ol)

// A class to manage multi click count and remember last clicked side (may cause issue otherwise)

class multiclick_counter {
	constructor() {
		this.timers = []; // collection of timers. Important 
		this.count = 0; // click count
		this.reseted = 0; // before resetting what was the count
		this.last_side = null; // L C R 3sides
	}

	clicked() {
		this.count += 1
		var xcount = this.count; // will be checked if click count increased in the time
		this.timers.push(setTimeout(this.reset.bind(this, xcount), 500)); // wait till 500ms for next click

		return this.count
	}

	reset_count(n) {
		// Reset count if clicked on the different side
		this.reseted = this.count
		this.count = n
		for (var i = 0; i < this.timers.length; i++) {
			clearTimeout(this.timers[i]);
		}
		this.timer = []

	}

	reset(xcount) {
		if (this.count > xcount) { return } // return if clicked after timer started
		// Reset otherwise
		this.count = 0;
		this.last_side = null;
		this.reseted = 0;
		skip_ol.style.opacity = "0";
		this.timer = []
	}

}

var counter = new multiclick_counter();


const poster = byClass("plyr__poster")[0]
// We will target the poster since this is the only thing sits between video and controls

poster.onclick = function (e) {
	const count = counter.clicked()
	if (count < 2) { return } // if not double click

	const rect = e.target.getBoundingClientRect();
	const x = e.clientX - rect.left; //x position within the element.
	const y = e.clientY - rect.top;  //y position within the element.

	// The relative position of click on video

	const width = e.target.offsetWidth;
	const perc = x * 100 / width;

	var panic = true; // panic if the side needs to be checked
	var last_click = counter.last_side

	if (last_click == null) {
		panic = false
	}
	if (perc < 40) {
		counter.last_side = "L"
		if (panic && last_click != "L") {
			counter.reset_count(1)
			return
		}

		skip_ol.style.opacity = "0.9";
		player.rewind()
		skip_ol.innerText = "⫷⪡" + "\n" + ((count - 1) * 10) + "s";

	}
	else if (perc > 60) {
		counter.last_side = "R"
		if (panic && last_click != "R") {
			counter.reset_count(1)
			return
		}

		skip_ol.style.opacity = "0.9";
		last_click = "R"
		player.forward()
		skip_ol.innerText = "⪢⫸ " + "\n" + ((count - 1) * 10) + "s";

	}
	else {
		player.togglePlay()
		counter.last_click = "C"
	}

}
