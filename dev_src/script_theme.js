var vh = 0,
	vw = 0;

class Theme_Controller {
	// TRON theme controller
	constructor() {
		this.fa_ok = false;
	}

	switch_init() {
		var that = this;
		this.switch_btn = byClass("tron-switch");

		for (var i = 0; i < this.switch_btn.length; i++) {
			let id = this.switch_btn[i].id;

			// fix initial state
			that.set_switch_mode(id, that.switch_mode(id));

			// set click action
			this.switch_btn[i].onclick = function () {
				that.set_switch_mode(id, that.switch_mode(id), true);
			};
		}
	}

	switch_mode(id) {
		let btn = byId(id + "-mode");
		if (btn.innerText == "ON") {
			return true;
		} else return false;
	}

	set_switch_mode(id, mode, not = false) {
		// not: do the inverse of current mode
		let btn = byId(id + "-mode");
		let parent = byId(id);

		function toggle_panel(disable) {
			let Guncle = parent.parentElement.nextElementSibling; // Guncle = Grand Uncle => next element of grand-parent
			if (tools.is_in(id, panel2disable)) {
				if (disable == true) {
					Guncle.classList.add("disabled");
					Guncle.disabled = true;
				} else {
					Guncle.classList.remove("disabled");
					Guncle.disabled = false;
				}
			}
		}
		if (not) {
			if (mode == "ON" || mode === true) {
				btn.innerText = "OFF";
				parent.classList.remove("active");
				{
					toggle_panel(true);
				}
			} else {
				btn.innerText = "ON";
				parent.classList.add("active");
				toggle_panel(false);
			}
		} else {
			if (mode == "ON" || mode === true) {
				btn.innerText = "ON";
				parent.classList.add("active");
				toggle_panel(false);
			} else {
				btn.innerText = "OFF";
				parent.classList.remove("active");
				toggle_panel(true);
			}
		}
	}

	getViewportSize() {
		// var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
		// var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)

		// vh = byId("brightness").clientHeight;
		// vw = byId("brightness").clientWidth;

		vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
		vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)

	}
	async del_fa_alt() {
		if (this.fa_ok) {
			document.querySelectorAll(".fa").forEach(e => {
				const i = document.createElement("i");
				i.className = e.className;
				i.style = e.style.cssText;  // Ensure styles are retained
				i.id = e.id;
				e.parentNode.replaceChild(i, e);
			});
		}
	}
	
	async load_fa() {
		const that = this;
		const link = document.createElement("link");
	
		link.rel = "stylesheet";
		link.type = "text/css";
		link.media = "print";  // Load in print mode first to avoid blocking render
	
		const cache_buster = Math.random();  // Force new font fetch (fixes Tofu issue)
		link.href = "https://cdn.jsdelivr.net/gh/RaSan147/fabkp@2f5670e/css/all.min.css" + "?no_cache=" + cache_buster;
	
		link.onload = function () {
			console.log("FA loaded at:", new Date().toISOString());
	
			// Wait for all fonts, including WOFF, to be fully loaded
			document.fonts.ready.then(() => {
				console.log("Fonts fully loaded at:", new Date().toISOString());
	
				that.fa_ok = true;  // Only set when confirmed fully loaded
				that.del_fa_alt();  // Swap placeholders
				link.media = "all";  // Apply styles properly
			});
		};
	
		document.head.appendChild(link);
	}
}

var theme_controller = new Theme_Controller();

theme_controller.getViewportSize();
theme_controller.load_fa()






const MAIN_JS = true;
const V = "0.0.1";

if (typeof datas === "undefined") { window["datas"] = {} } // if datas is not defined

class Local_Data_Manager {
	// local data manager, UNUSED
	constructor() { }


	show_last_opened() {
		var self = this;
		log("show_last_opened used get_local_data");
		var link = null;

		this.click_last_link = function (evt) {
			evt.preventDefault();
			popup_msg.close();

			datas.current_page_index = datas.last_opened;
			self.update_data();
			handle_json_request(link + "/index.html");
		};

		if (!this.get_local_data()) {
			return 0;
		}

		if (
			datas.last_opened == "undefined" ||
			datas.last_opened == null ||
			datas.last_opened == -1
		) {
			datas.last_opened = datas.current_page_index;
			//log("show_last_opened used set_local_data");
			this.update_data();
			return;
		}


		// CASE: Currently open CHAPTER-LIST
		if (
			datas.current_page_index == -1 &&
			datas.last_opened != datas.current_page_index
		) {
			let header = "Psst!";
			//log("last_opened", datas.last_opened);
			let content =
				"You left the page on <a id= 'lastleft' href='" +
				datas.pages_list[datas.last_opened] +
				"/index.html'>" +
				datas.pages_list[datas.last_opened] +
				"</a><br> Click on the link to go there<hr>Close this dialog to continue from here";

			link = datas.pages_list[datas.last_opened];
			popup_msg.createPopup(header, content);

			byId("lastleft").onclick = this.click_last_link;

			popup_msg.onclose = function () {
				self.update_data();
			};

			popup_msg.open_popup();

			config.popup_msg_open = popup_msg;
		}
	}

	get_or_set(key, global = false) {
		const data = localStorage.getItem(key)
		if (data == "undefined" || data == null) {
			if (global) {
				this.set_global_data()
			}
			else {
				this.set_local_data()
			}
			return this.get_or_set(key, global)
		}
		return data;
	}

	get_global_data() {
		var data = this.get_or_set("config", true);


		data = JSON.parse(data);

		datas.allow_preload = data["preload"]
	}

	get_local_data() {
		// gets data from local storage
		// proj_name : [page_index, theme_index, [style...]]

		const that = this;
		function read_chapter_data() {
			var data = that.get_or_set(datas.proj_name)

			data = JSON.parse(data);

			datas.last_opened = data[0];

			datas.theme = data[1];
			datas.current_style = data[2];

			return true;
		}
		if (config.page_type == "CHAPTER") {
			return read_chapter_data();
		}

		if (config.page_type == "CHAPTER-LIST") {
			return read_chapter_data();
		}
		return true;
	}

	set_global_data() {
		const data = {
			"preload": datas.allow_preload,
		}

		localStorage.setItem("config", JSON.stringify(data))
	}

	set_local_data() {
		// sets data to local storage

		if (config.page_type == "CHAPTER") {
			datas.theme = 0;
		}

		datas.last_opened = datas.current_page_index;

		var data = [datas.last_opened, datas.theme, datas.current_style];

		localStorage.setItem(datas.proj_name, JSON.stringify(data));
	}

	set_last_manga() {
		datas.last_opened_manga = [datas.proj_name, datas.current_page_index];
		localStorage.setItem(
			"$last_open",
			JSON.stringify(datas.last_opened_manga)
		);
	}

	get_last_pointer() {
		datas.last_opened_manga = JSON.parse(
			localStorage.getItem("$last_open")
		);
		return datas.last_opened_manga;
	}

	update_data() {
		this.set_global_data(); // for all manga
		this.set_local_data(); // for the specific manga
	}
}

var local_data_manager = new Local_Data_Manager();


class Top_Bar {
	constructor() {
		this.dont_move = false;
		this.prevScrollpos = window.scrollY;
		this.top_bar = byId("TopBar");
	}

	set_title(title) {
		// if (vw < 300) {
		// 	this.app_name.innerHTML = " WL";
		// } else {
		// 	this.app_name.innerHTML = "WL Reader";
		// }
		this.app_name.innerText = title;
	}

	set_profile_pic(url) {
		this.profile_pic.src = url;
	}
	show() {
		if (!this.top_bar) return false;

		this.top_bar.style.top = "0";
		document.body.style.top = "50px";
		// this.top_bar.classList.remove("inactive");
	}

	hide() {
		if (!this.top_bar) return false;

		this.top_bar.style.top = "-50px";
		document.body.style.top = "0";
	}

}

var top_bar = new Top_Bar();
top_bar.show();


window.onscroll = function () {
	var currentScrollPos = window.scrollY;

	if (top_bar.dont_move) {
		return false;
	}

	if (top_bar.prevScrollpos > currentScrollPos + 5) {
		top_bar.show();
	}
	if (top_bar.prevScrollpos < currentScrollPos - 15) {
		top_bar.hide();
	}
	top_bar.prevScrollpos = currentScrollPos;
};

var clientX, clientY;
window.addEventListener('touchstart', (e) => {
	// Cache the client X/Y coordinates
	clientX = e.touches[0].clientX;
	clientY = e.touches[0].clientY;
}, false);

window.addEventListener('touchend', (e) => {
	let deltaX;
	let deltaY;


	// if(appConfig.page_type=="chat") return false;

	// Compute the change in X and Y coordinates.
	// The first touch point in the changedTouches
	// list is the touch point that was just removed from the surface.
	deltaX = e.changedTouches[0].clientX - clientX;
	deltaY = e.changedTouches[0].clientY - clientY;

	// Process the data…
	if (deltaY > 15) {
		top_bar.show();
	}
}, false);


// r_u_sure()


{ // why bracket? To make is isolated, coz I don't want variable names conflict with these mini functions or things
	const resizer = () => {
		theme_controller.getViewportSize();
		document.body.style.minHeight = vh + "px";
	}

	window.addEventListener("resize", (_e) => resizer());

	document.addEventListener("DOMContentLoaded", (_e) => resizer());
}




class SidebarControl {
	constructor() {
		this.right_bar = byId("mySidebarR");
		this.sidebar_bg = byId("sidebar_bg");

		if (this.sidebar_bg == null) {
			this.sidebar_bg = document.createElement("div");
			this.sidebar_bg.id = "sidebar_bg";
			document.body.appendChild(this.sidebar_bg);
		}


		this.sidebar_bg.onclick = function () {
			sidebar_control.closeNav();
		};


	}



	is_open(side) {
		return tools.hasClass(
			byId("mySidebar" + side),
			"mySidebar-active",
			true
		);
	}

	openNavR() {
		tools.fake_push()

		tools.toggle_scroll(0);
		this.sidebar_bg.style.display = "block";
		this.right_bar.classList.add("mySidebar-active");
		this.right_bar.classList.remove("mySidebar-inactive");
		HISTORY_ACTION.push(this._closeNavR.bind(this))
		// byId("app_header").classList.toggle("top-titleR-active");
	}

	toggleNavR() {
		if (this.is_open("R")) {
			this.closeNavR();
			return;
		}

		this.openNavR()
	}

	_closeNavR() {
		this.right_bar.classList.remove("mySidebar-active");
		this.right_bar.classList.add("mySidebar-inactive");

		this.sidebar_bg.style.display = "none";

		tools.sleep(3000);
		tools.toggle_scroll(1);

		top_bar.dont_move = false; // allow moving the top bar
	}


	closeNavR() {
		if (this.is_open("R")) {
			history.back();
		}
	}

	closeNav() {
		this.closeNavR();
	}
}

var sidebar_control = new SidebarControl()




class Accordion_ {
	constructor() {
		this.acc = byClass("accordion");

		var that = this;
		for (let i = 0; i < this.acc.length; i++) {
			this.acc[i].addEventListener("click", function () {
				var panel = this.nextElementSibling;
				if (panel && panel.classList.contains("accordion-panel")) {
					this.classList.toggle("accordion-active");
					if (panel.style.display === "block") {
						panel.style.display = "none";
					} else {
						panel.style.display = "block";
					}
				}
			});
		}
	}
}

var accordion = new Accordion_();

class SwitchBtn_ {
	constructor() {
		theme_controller.switch_init();
	}

	switch_mode(id) {
		return theme_controller.switch_mode(id);
	}

	set_switch_mode(id, mode, not = false) {
		return theme_controller.set_switch_mode(id, mode, not);
	}
}

var switchBtn = new SwitchBtn_();
