class Video_Page extends Page {
	constructor(controller=page_controller, type="vid", handle_part="video-page") {
		super(controller, type, handle_part);

		// this.my_part = byId(handle_part);
		// this.type = type;
		// this.controller = controller;

		this.controls = [
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

		this.player_source = document.getElementById("player_source")
		this.player_title = byId("player_title")
		this.player_warning = byId("player-warning")
		this.video_dl_url = byId("video_dl_url")


		this.player = null;

		if (typeof (Plyr) !== "undefined") {
			this.player = new Plyr('#player', {
				controls: this.controls,
				keyboard: {
					global: true,
					focused: false,
				},
				disableContextMenu: false,
			});
		}
	}

	async initialize() {
		this.controller.hide_actions_button(); // Hide actions button, not needed here


		var url = tools.add_query_here("vid-data")

		var data = await fetch(url)
			.then(data => { return data.json() })
			.catch(err => { console.error(err) })

		var video = data.video
		var title = data.title
		var content_type = data.content_type
		var warning = data.warning

		var subtitles = data.subtitles

		this.player_title.innerText = title
		this.player_warning.innerHTML = warning
		this.video_dl_url.href = video

		this.set_title(title)

		if (this.player) {
			this.player.source = {
				type: 'video',
				title: 'Example title',
				sources: [
					{
						src: video,
						// type: content_type,
					},
				],
				poster: 'https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@9fb9f51/assets/youtube-logo.webp', // to keep preview hidden
				keyboard: {
					global: true,
					focused: false,
				},
				tracks: subtitles,
				volume: 1
			};

			this.init_online_player() // Add double click to skip
		} else {
			this.player_source.src = video;
			this.player_source.type = content_type;
		}
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
		this.player_source.src = ""
		this.player_source.type = ""
		this.player_title.innerText = ""
		this.player_warning.innerHTML = ""
		this.video_dl_url.href = ""
	}




	init_online_player() {
		var player = this.player;
		player.elements.container.tabIndex = 0;
		player.eventListeners.forEach(function (eventListener) {
			if (eventListener.type === 'dblclick') {
				eventListener.element.removeEventListener(eventListener.type, eventListener.callback, eventListener
					.options);
			}
		});
		//function create_time_overlay(){
		const skip_ol = createElement("div");
		// ol.classList.add("plyr__control--overlaid");
		skip_ol.id = "plyr__time_skip"
		byClass("plyr")[0].appendChild(skip_ol)
		//}
		//create_time_overlay()
		class multiclick_counter {
			constructor() {
				this.timers = [];
				this.count = 0;
				this.reseted = 0;
				this.last_side = null;
			}
			clicked() {
				this.count += 1
				var xcount = this.count;
				this.timers.push(setTimeout(this.reset.bind(this, xcount), 500));
				return this.count
			}
			reset_count(n) {
				console.log("reset")
				this.reseted = this.count
				this.count = n
				for (var i = 0; i < this.timers.length; i++) {
					clearTimeout(this.timers[i]);
				}
				this.timer = []
			}
			reset(xcount) {
				if (this.count > xcount) {
					return
				}
				this.count = 0;
				this.last_side = null;
				this.reseted = 0;
				skip_ol.style.opacity = "0";
				this.timer = []
			}
		}
		var counter = new multiclick_counter();
		const poster = byClass("plyr__poster")[0]
		poster.onclick = function (e) {
			const count = counter.clicked()
			if (count < 2) {
				return
			}
			const rect = e.target.getBoundingClientRect();
			const x = e.clientX - rect.left; //x position within the element.
			const y = e.clientY - rect.top; //y position within the element.
			console.log("Left? : " + x + " ; Top? : " + y + ".");
			const width = e.target.offsetWidth;
			const perc = x * 100 / width;
			var panic = true;
			var change = 10;
			var last_click = counter.last_side
			if (last_click == null) {
				panic = false
			}
			if (perc < 40) {
				if (player.currentTime == 0) {
					return false
				}
				if (player.currentTime < 10) {
					change = player.currentTime
				}

				log(change)
				counter.last_side = "L"
				if (panic && last_click != "L") {
					counter.reset_count(1)
					return
				}
				skip_ol.style.opacity = "0.9";
				player.rewind(change)
				if (change == 10) {
					change = ((count - 1) * 10)
				} else {
					change = change.toFixed(1);
				}
				skip_ol.innerText = "⫷⪡" + "\n" + change + "s";
			} else if (perc > 60) {
				if (player.currentTime == player.duration) {
					return false
				}
				counter.last_side = "R"
				if (panic && last_click != "R") {
					counter.reset_count(1)
					return
				}
				if (player.currentTime > (player.duration - 10)) {
					change = player.duration - player.currentTime;
				}
				skip_ol.style.opacity = "0.9";
				last_click = "R"
				player.forward(change)
				if (change == 10) {
					change = ((count - 1) * 10)
				} else {
					change = change.toFixed(1);
				}
				skip_ol.innerText = "⪢⫸ " + "\n" + change + "s";
			} else {
				player.togglePlay()
				counter.last_click = "C"
			}
		}
	}
}

page_controller.add_handler("vid", Video_Page, "video-page");