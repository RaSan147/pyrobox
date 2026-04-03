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

	destroy() {
		// Base class cleanup - subclasses should override for their specific cleanup
		this.clear();
	}
	clear() {
		// clear the page
		this.my_part.innerHTML = "";
	}
	set_title(title) {
		this.controller.set_title(title);
	}
	set_actions_button_text(text, icon = null, override_action = null) {
		this.controller.set_actions_button_text(text, icon, override_action);
	}
	
	set_action_tools(tools_list) {
		this.controller.set_action_tools(tools_list);
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


class ActionBtnController {
	constructor() {
		this.btn = byId("actions-btn");
		this.text = byId("actions-btn-text");
		this.icon = byId("actions-btn-icon");
		this.menu = byId("actions-menu");
		this.is_expanded = false;
		this.tools_list = [];
		this.override_action = null;
		
		// Start hidden
		if (this.btn) {
			this.btn.classList.add("hidden-btn");
		}

		// Add window click listener to close menu when clicking outside
		window.addEventListener('click', (e) => {
			if (this.is_expanded && !this.btn.contains(e.target) && !this.menu.contains(e.target)) {
				this.collapse();
			}
		});
	}

	set_tools(tools_list) {
		this.tools_list = tools_list;
		this.render_menu();
	}

	render_menu() {
		if (!this.menu) return;
		this.menu.innerHTML = '';
		
		let valid_tools = this.tools_list.filter(t => !t.condition || t.condition());
		let total = valid_tools.length;
		
		valid_tools.forEach((tool, idx) => {
			const item = document.createElement("div");
			item.className = `action-menu-item disable_selection ${tool.className || ''}`;
			
			// Set stagger index for CSS transition delay
			item.style.setProperty('--btn-idx', idx);
			item.style.setProperty('--btn-rev-idx', total - 1 - idx);
			
			const iconSpan = document.createElement("span");
			iconSpan.className = `action-menu-item-icon fa ${tool.icon_class || ''}`;
			iconSpan.innerHTML = tool.icon_text || '';
			
			const textSpan = document.createElement("span");
			textSpan.innerText = tool.text;

			item.appendChild(iconSpan);
			item.appendChild(textSpan);
			
			item.onclick = (e) => {
				e.stopPropagation();
				this.collapse();
				if (tool.action) tool.action();
			};
			
			this.menu.appendChild(item);
			
			if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
				theme_controller.del_fa_alt(item);
			}
		});
	}

	toggle() {
		if (this.override_action) {
			this.override_action();
			return;
		}

		if (this.is_expanded) {
			this.collapse();
		} else {
			this.expand();
		}
	}

	expand() {
		if (!this.menu || this.tools_list.length === 0) return;
		this.is_expanded = true;
		this.menu.classList.remove("hidden");
		
		// Swap main icon to cross/close when expanded
		this.set_main_style("Close", { class: "fa-solid fa-xmark", text: "✖" });
	}

	collapse() {
		if (!this.menu) return;
		this.is_expanded = false;
		this.menu.classList.add("hidden");
		
		// Reset back to whatever default the current page set
		if (this._default_text) {
			this.set_main_style(this._default_text, this._default_icon);
		}
	}

	show() {
		if (this.btn) {
			this.btn.style.display = "flex";
			// small delay to allow display block to apply
			setTimeout(() => {
				this.btn.classList.remove("hidden-btn");
			}, 10);
		}
	}

	hide() {
		if (this.btn) {
			this.btn.classList.add("hidden-btn");
			setTimeout(() => {
				if (this.btn.classList.contains("hidden-btn")) {
					this.btn.style.display = "none";
				}
			}, 300); // match transition time
		}
		this.collapse();
	}

	set_main_style(text, icon = null) {
		if (!this.text) return;
		this.text.innerHTML = text + "&nbsp;";
		
		let icon_el = byId("actions-btn-icon");
		if (icon) {
			if (icon_el) {
				let new_icon = document.createElement("span");
				new_icon.id = "actions-btn-icon";
				new_icon.className = `fa ${icon.class}`;
				new_icon.innerHTML = icon.text;
				
				icon_el.parentNode.replaceChild(new_icon, icon_el);
				this.icon = new_icon;
				
				if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
					theme_controller.del_fa_alt(new_icon);
				}
			}
		} else {
			if (icon_el) {
				let new_icon = document.createElement("span");
				new_icon.id = "actions-btn-icon";
				new_icon.className = "fa fa-solid fa-wrench";
				new_icon.innerHTML = "<b>+</b>";
				
				icon_el.parentNode.replaceChild(new_icon, icon_el);
				this.icon = new_icon;
				
				if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
					theme_controller.del_fa_alt(new_icon);
				}
			}
		}
	}

	set_default(text, icon = null, override_action = null) {
		this._default_text = text;
		this._default_icon = icon;
		this.override_action = override_action;
		this.set_main_style(text, icon);
	}

	get actions_loading_icon() {
		return byId("actions-loading-icon");
	}

	get actions_button_icon() {
		return byId("actions-btn-icon");
	}

	show_loading() {
		if (this.btn) {
			this.btn.classList.add("loading");
			const icon = this.actions_loading_icon;
			const btn_icon = this.actions_button_icon;
			if (icon) icon.classList.remove("hidden");
			if (btn_icon) btn_icon.classList.add("hidden");
			if (this.text) this.text.classList.add("hidden");
		}
	}

	hide_loading() {
		if (this.btn) {
			this.btn.classList.remove("loading");
			const icon = this.actions_loading_icon;
			const btn_icon = this.actions_button_icon;
			if (icon) icon.classList.add("hidden");
			if (btn_icon) btn_icon.classList.remove("hidden");
			if (this.text) this.text.classList.remove("hidden");
		}
	}
}

const action_btn_controller = new ActionBtnController();

class PageController {
	constructor() {
		this.container = byId('content_container');
		this.type = null;
		this.handler = new Page(this); // default handler

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
			// Cleanup old handler if switching to a different one
			if (old_handler && old_handler !== this.handler && typeof old_handler.destroy === 'function') {
				old_handler.destroy();
			}

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
		action_btn_controller.show_loading();
	}

	hide_loading() {
		action_btn_controller.hide_loading();
	}


	// Compatibility wrapper
	show_actions_button() {
		action_btn_controller.show();
	}

	hide_actions_button() {
		action_btn_controller.hide();
	}

	set_actions_button_text(text, icon = null, override_action = null) {
		action_btn_controller.set_default(text, icon, override_action);
	}

	set_action_tools(tools_list) {
		action_btn_controller.set_tools(tools_list);
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

