
class Page {
	constructor() {
		this.container = byId('content_container')
		this.type = null;
		this.handler = fm_page; // default handler

		this.actions_button = byId("actions-btn")
		this.actions_button_text = byId("actions-btn-text")


		this.dir_tree = document.getElementById("dir-tree")

		this.dir_tree.scrollLeft = this.dir_tree.scrollWidth;
		// convert scroll to horizontal
		this.dir_tree.onwheel = function (event) {
			event.preventDefault();
			// scroll to left
			event.target.scrollBy({
				top: 0,
				left: event.deltaY,
				behavior: 'smooth'
			})
			event.deltaY < 0;
		}


		this.handlers = {
			"dir": fm_page,
			"vid": video_page,
			"admin": admin_page,
			"error": error_page
		}



		this.initialize()
	}

	get actions_loading_icon() {
		return byId("actions-loading-icon")
	}

	get actions_button_icon() {
		return byId("actions-btn-icon")
	}

	get_type() {
		const url = tools.add_query_here('type', '');
		return fetch(url)
			.then(data => { return data.text() })
	}

	hide_all() {
		for (let handler of Object.values(this.handlers)) {
			handler.hide();
		}
	}

	clear() {
		this.handler.clear()
	}

	async initialize() {
		/*for(let t=3; t>0; t--){
			console.log("Loading page in " + t)
			await tools.sleep (1000)
		}*/

		this.show_loading();

		this.container.style.display = "none";
		this.hide_all();
		this.update_displaypath();

		this.type = await this.get_type();
		var type = this.type;

		var old_handler = this.handler;

		this.handler = null;

		console.log("Page type: " + type)

		if (ERROR_PAGE == "active") {
			this.handler = error_page;
		} else if (type == 'dir') {
			this.handler = fm_page;
		} else if (type == 'vid') {
			this.handler = video_page;
		} else if (type == "admin") {
			this.handler = admin_page;
		} else if (type == "zip") {
			this.handler = zip_page;
		}

		if (this.handler) {
			this.handler.initialize();
			this.handler.show();
		} else {
			// popup_msg.createPopup("This type of page is not ready yet");
			// popup_msg.show();

			this.handler = old_handler;
		}

		this.hide_loading();
		this.container.style.display = "block";

	}

	show_loading() {
		this.actions_loading_icon.classList.remove("hidden");
		this.actions_button_icon.classList.add("hidden");
		this.actions_button_text.classList.add("hidden");
	}

	hide_loading() {
		this.actions_loading_icon.classList.add("hidden");
		this.actions_button_icon.classList.remove("hidden");
		this.actions_button_text.classList.remove("hidden");
	}


	show_actions_button() {
		this.actions_button.style.display = "flex";
	}

	hide_actions_button() {
		this.actions_button.style.display = "none";
	}

	on_action_button() {
		this.handler.on_action_button();
	}

	set_actions_button_text(text) {
		this.actions_button_text.innerHTML = text;
	}

	set_title(title) {
		window.document.title = title;
	}

	set_diplaypath(displaypath) {
		this.dir_tree.innerHTML = displaypath;
	}

	update_displaypath() {
		const path = window.location.pathname;
		const dirs = path.replace(/\/{2,}/g, "/").split('/');
		const urls = ['/'];
		const names = ['&#127968; HOME'];
		const r = [];

		for (let i = 1; i < dirs.length - 1; i++) {
			const dir = dirs[i];
			// urls.push(urls[i - 1] + encodeURIComponent(dir).replace(/'/g, "%27").replace(/"/g, "%22") + (dir.endsWith('/') ? '' : '/'));
			urls.push(urls[i - 1] + dir + '/');
			names.push(decodeURIComponent(dir));
		}

		for (let i = 0; i < names.length; i++) {
			const tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>";
			r.push(tag);
		}

		this.set_diplaypath(r.join('<span class="dir_arrow">&#10151;</span>'));
	}

	refresh_dir() {
		console.log(this)
		if (this.type == "dir") {
			fm_page.initialize(true); // refresh the page
		}
	}
}

const page = new Page();
