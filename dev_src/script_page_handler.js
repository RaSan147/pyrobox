class Page {
	// this is the generic page with all the common functions
	// it will be used as a base class for all the other pages
	constructor(controller=page_controller, type=null, my_part=null) {
		this.type = type;
		this.controller = controller;
		// check if my_part is null
		if (my_part) {
			if (my_part instanceof HTMLElement) {
				this.my_part = my_part;
			} else {
				this.my_part = document.getElementById(my_part);
			}
		} else {
			this.my_part = document.createElement("div");
		}
		this.my_part.classList.add("page");


		
		this.dir_tree = document.getElementById("dir-tree");

		this.dir_tree.scrollLeft = this.dir_tree.scrollWidth;
		// convert scroll to horizontal
		this.dir_tree.addEventListener("wheel", function (event) {
			event.preventDefault();
			event.target.scrollBy({
				top: 0,
				left: event.deltaY,
				behavior: 'smooth'
			});
		}, { passive: true });
	}

	on_action_button() {
		// show add folder, sort, etc
	}

	async initialize(lazyload = false) {
		if (!lazyload) {
			this.clear();
		}
		// initialize the page
	}
	hide() {
		this.my_part.classList.remove("active");
	}
	show() {
		this.my_part.classList.add("active");
	}
	clear() {
		// clear the page
		this.my_part.innerHTML = "";
	}
	set_title(title) {
		this.controller.set_title(title);
	}
	set_actions_button_text(text) {
		this.controller.set_actions_button_text(text);
	}

	set_diplaypath(displaypath) {
		this.dir_tree.innerHTML = displaypath;
	}

	before_initialize() {
		this.update_displaypath();
	}
	
	after_initialize() {
	}
	
	update_displaypath() {
		const path = window.location.pathname;
		const dirs = path.replace(/\/{2,}/g, "/").split('/');
		const urls = ['/'];
		// const names = ['&#127968; HOME'];
		const names = ['🏠 HOME'];
		const r = [];

		for (let i = 1; i < dirs.length - 1; i++) {
			const dir = dirs[i];
			// urls.push(urls[i - 1] + encodeURIComponent(dir).replace(/'/g, "%27").replace(/"/g, "%22") + (dir.endsWith('/') ? '' : '/'));
			urls.push(urls[i - 1] + dir + '/');
			names.push(decodeURIComponent(dir));
		}

		for (let i = 0; i < names.length; i++) {
			// const tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>";
			const tag = document.createElement("a");
			tag.classList.add("dir_turns");
			tag.href = urls[i];
			tag.innerText = names[i]
			r.push(tag.outerHTML);
		}

		this.set_diplaypath(r.join('<span class="dir_arrow">&#10151;</span>'));
	}
}


class PageController {
	constructor() {
		this.container = byId('content_container');
		this.type = null;
		this.handler = new Page(this); // default handler

		this.actions_button = byId("actions-btn");
		this.actions_button_text = byId("actions-btn-text");

		this.handlers = {
			// "dir": fm_page,
			// "vid": video_page,
			// "admin": admin_page,
			// "error": error_page
		};



		this.initialize();
	}

	add_handler(type, handler_class, handle_part) {
		this.handlers[type] = new handler_class(this, type, handle_part);
	}

	get actions_loading_icon() {
		return byId("actions-loading-icon");
	}

	get actions_button_icon() {
		return byId("actions-btn-icon");
	}

	get_type() {
		let that = this;
		if (this.type) {
			return this.type;
		}
		const url = tools.add_query_here('type', '');
		return fetch(url)
			.then(data => { 
				that.type = data.text();
				return that.type;
			})
	}

	hide_all() {
		for (let handler of Object.values(this.handlers)) {
			handler.hide();
		}
	}

	clear() {
		this.handler.clear();
	}

	async initialize() {
		this.show_loading();

		this.container.style.display = "none";
		this.hide_all();

		this.type = await this.get_type();
		var type = this.type;

		var old_handler = this.handler;

		this.handler = null;

		if (ERROR_PAGE == "active") {
			this.type = "error";
		}
		//  else if (type == 'dir') {
		// 	this.handler = fm_page;
		// } else if (type == 'vid') {
		// 	this.handler = video_page;
		// } else if (type == "admin") {
		// 	this.handler = admin_page;
		// } else if (type == "zip") {
		// 	this.handler = zip_page;
		// }
		if (this.handlers[type]) {
			this.handler = this.handlers[type];
		}

		if (this.handler) {
			this.before_initialize();
			this.handler.initialize();
			this.after_initialize();
			this.handler.show();
		} else {
			// popup_msg.createPopup("This type of page is not ready yet");
			// popup_msg.show();

			this.handler = old_handler;
		}

		this.hide_loading();
		this.container.style.display = "block";
	}

	before_initialize() {
		this.handler.before_initialize();
	}

	after_initialize() {
		this.handler.after_initialize();
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

	refresh_dir() {
		if (this.type == "dir") {
			this.handler.initialize(true); // refresh the page
		}
	}
}

const page_controller = new PageController();

