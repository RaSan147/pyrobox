class Video_Page extends Page {
	constructor(controller = page_controller, type = "vid", handle_part = "video-page") {
		super(controller, type, handle_part);

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
			'volume', // Volume control
			//'captions', // Toggle captions
			'settings', // Settings menu
			//'pip', // Picture-in-picture (currently Safari only)
			//'airplay', // Airplay (currently Safari only)
			//'download', // Show a download button with a link to either the current source or a custom URL you specify in your options
			'fullscreen' // Toggle fullscreen
		];

		//CUSTOMIZE MORE USING THIS:
		// https://stackoverflow.com/a/61577582/11071949

		this.player_source = document.getElementById("player_source");
		this.player_title = byId("player_title");
		this.player_warning = byId("player-warning");
		this.video_dl_url = byId("video_dl_url");
		this.video_backdrop = byId("video-backdrop");

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

		var url = tools.add_query_here("vid-data");

		var data = await fetch(url)
			.then(data => { return data.json() })
			.catch(err => { console.error(err) });

		var video = data.video;
		var title = data.title;
		var content_type = data.content_type;
		var warning = data.warning;
		var subtitles = data.subtitles;

		this.player_title.innerText = title;
		this.player_warning.innerHTML = warning;
		this.video_dl_url.href = video;

		this.set_title(title);

		if (this.player) {
			this.player.source = {
				type: 'video',
				title: title,
				sources: [
					{
						src: video,
						// type: content_type,
					},
				],
				poster: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><defs><linearGradient id="a" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="%23b0b5ba"/><stop offset="15%" stop-color="%2355585b"/><stop offset="85%" stop-color="%232a2c2e"/><stop offset="100%" stop-color="%238a8580"/></linearGradient><linearGradient id="d" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%23a81a1a"/><stop offset="100%" stop-color="%234a0808"/></linearGradient><linearGradient id="e" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="%23855"/><stop offset="100%" stop-color="%23211"/></linearGradient><radialGradient id="b" cx="50%" cy="50%" r="70%" fx="50%" fy="50%"><stop offset="0%" stop-color="%235a6066"/><stop offset="60%" stop-color="%232c2e33"/><stop offset="100%" stop-color="%23141518"/></radialGradient><filter id="c" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8" result="blur"/></filter></defs><rect width="100%" height="100%"/><rect x="70" y="110" width="260" height="180" rx="55" fill="url(%23a)"/><rect x="74" y="114" width="252" height="172" rx="51" fill="url(%23b)"/><rect x="74" y="114" width="252" height="172" rx="51" fill="none" stroke="%23050505" stroke-width="2" opacity=".7"/><path fill="red" filter="url(%23c)" opacity=".3" d="M172 165v70l60-35z"/><path fill="url(%23d)" stroke="url(%23e)" stroke-width="3" stroke-linejoin="round" d="M172 165v70l60-35z"/></svg>', // inline SVG poster — no CDN
				keyboard: {
					global: true,
					focused: false,
				},
				tracks: subtitles,
				volume: 1
			};

			// Fade in ambient backdrop once Plyr is ready
			if (this.video_backdrop) {
				this.player.once('ready', () => {
					this.video_backdrop.classList.add('loaded');
				});
			}

			this.init_online_player(); // Add double click to skip
		} else {
			this.player_source.src = video;
			this.player_source.type = content_type;

			// REQUIRED: dynamically changing <source> src does not trigger reload;
			// must call load() explicitly so the browser picks up the new source.
			const nativeVideo = document.getElementById('player');
			if (nativeVideo) {
				nativeVideo.load();
			}

			// Fallback backdrop for native player
			if (this.video_backdrop && nativeVideo) {
				nativeVideo.addEventListener('loadedmetadata', () => {
					this.video_backdrop.classList.add('loaded');
				}, { once: true });
			}
		}
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
		this.player_source.src = "";
		this.player_source.type = "";
		this.player_title.innerText = "";
		this.player_warning.innerHTML = "";
		this.video_dl_url.href = "";
		// Reset backdrop
		if (this.video_backdrop) {
			this.video_backdrop.classList.remove('loaded');
		}
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
		skip_ol.id = "plyr__time_skip";
		skip_ol.innerHTML = '<span class="skip-chevrons"></span><span class="skip-seconds"></span>';
		byClass("plyr")[0].appendChild(skip_ol);
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
				return this.count;
			}
			reset_count(n) {
				console.log("reset");
				this.reseted = this.count;
				this.count = n
				for (var i = 0; i < this.timers.length; i++) {
					clearTimeout(this.timers[i]);
				}
				this.timer = [];
			}
			reset(xcount) {
				if (this.count > xcount) {
					return;
				}
				this.count = 0;
				this.last_side = null;
				this.reseted = 0;
				skip_ol.classList.remove("active", "bump");
				this.timer = []
			}
		}
		var counter = new multiclick_counter();
		const poster = byClass("plyr__poster")[0];
		poster.onclick = function (e) {
			const count = counter.clicked();
			if (count < 2) {
				return;
			}
			const rect = e.target.getBoundingClientRect();
			const x = e.clientX - rect.left; //x position within the element.
			const y = e.clientY - rect.top; //y position within the element.
			console.log("Left? : " + x + " ; Top? : " + y + ".");
			const width = e.target.offsetWidth;
			const perc = x * 100 / width;
			var panic = true;
			var change = 10;
			var last_click = counter.last_side;
			if (last_click == null) {
				panic = false;
			}
			if (perc < 40) {
				if (player.currentTime == 0) {
					return false;
				}
				if (player.currentTime < 10) {
					change = player.currentTime;
				}

				counter.last_side = "L";
				if (panic && last_click != "L") {
					counter.reset_count(1);
					return;
				}
				player.rewind(change);
				if (change == 10) {
					change = ((count - 1) * 10);
				} else {
					change = change.toFixed(1);
				}
				skip_ol.dataset.side = "L";
				skip_ol.querySelector(".skip-chevrons").textContent = "\u25C0\u25C0";
				skip_ol.querySelector(".skip-seconds").textContent = change + "s";
				skip_ol.classList.remove("bump");
				void skip_ol.offsetWidth; // force reflow for animation restart
				skip_ol.classList.add("active", "bump");
			} else if (perc > 60) {
				if (player.currentTime == player.duration) {
					return false;
				}
				counter.last_side = "R";
				if (panic && last_click != "R") {
					counter.reset_count(1);
					return;
				}
				if (player.currentTime > (player.duration - 10)) {
					change = player.duration - player.currentTime;
				}
				player.forward(change);
				if (change == 10) {
					change = ((count - 1) * 10);
				} else {
					change = change.toFixed(1);
				}
				skip_ol.dataset.side = "R";
				skip_ol.querySelector(".skip-chevrons").textContent = "\u25B6\u25B6";
				skip_ol.querySelector(".skip-seconds").textContent = change + "s";
				skip_ol.classList.remove("bump");
				void skip_ol.offsetWidth; // force reflow for animation restart
				skip_ol.classList.add("active", "bump");
			} else {
				player.togglePlay();
				counter.last_click = "C";
			}
		}
	}
}

page_controller.add_handler("vid", Video_Page, "video-page");