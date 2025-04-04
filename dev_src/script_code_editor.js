class Text_Editor_Page extends Page {
	constructor(controller=page_controller, type="text", handle_part="text-editor-page") {
		super(controller, type, handle_part);

		this.player_source = document.getElementById("player_source");
		this.player_title = byId("player_title");
		this.player_warning = byId("player-warning");
		this.video_dl_url = byId("video_dl_url");


		this.player = null;

		if (typeof (Plyr) !== "undefined") {
			this.player = new Plyr('#player', {
				controls: this.controls
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


		this.player_title.innerText = title;
		this.player_warning.innerHTML = warning;
		this.video_dl_url.href = video;

		this.set_title(title);

		if (this.player) {
			this.player.source = {
				type: 'video',
				title: 'Example title',
				sources: [
					{
						src: video,
						type: content_type,
					},
				],
				poster: 'https://i.ibb.co/dLq2FDv/jQZ5DoV.jpg' // to keep preview hidden
			};

			this.init_online_player(); // Add double click to skip
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
		this.player_source.src = "";
		this.player_source.type = "";
		this.player_title.innerText = "";
		this.player_warning.innerHTML = "";
		this.video_dl_url.href = "";
	}

	init_online_player() {
		var player = this.player;
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
				this.count += 1;
				var xcount = this.count;
				this.timers.push(setTimeout(this.reset.bind(this, xcount), 500));
				return this.count;
			}
			reset_count(n) {
				console.log("reset");
				this.reseted = this.count;
				this.count = n;
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
				skip_ol.style.opacity = "0";
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

				counter.last_side = "L"
				if (panic && last_click != "L") {
					counter.reset_count(1);
					return;
				}
				skip_ol.style.opacity = "0.9";
				player.rewind(change);
				if (change == 10) {
					change = ((count - 1) * 10);
				} else {
					change = change.toFixed(1);
				}
				skip_ol.innerText = "⫷⪡" + "\n" + change + "s";
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
				skip_ol.style.opacity = "0.9";
				last_click = "R";
				player.forward(change);
				if (change == 10) {
					change = ((count - 1) * 10);
				} else {
					change = change.toFixed(1);
				}
				skip_ol.innerText = "⪢⫸ " + "\n" + change + "s";
			} else {
				player.togglePlay();
				counter.last_click = "C";
			}
		}
	}
}

page_controller.add_handler("text", Text_Editor_Page, "text-editor-page");