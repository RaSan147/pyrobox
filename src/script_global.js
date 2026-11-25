const DEBUGGING = true;



const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);


String.prototype.toHtmlEntities = function () {
	return this.replace(/./ugm, s => s.match(/[a-z0-9\s]+/i) ? s : "&#" + s.codePointAt(0) + ";");
};











function null_func() {
	return true;
}

function line_break() {
	var br = createElement("br");
	return br;
}

function toggle_scroll() {
	document.body.classList.toggle('overflowHidden');
}

function go_link(type_code, locate) {
	// function to generate link for different types of actions
	return locate + "?" + type_code;
}

function goto(location) {
	var a = createElement("a");
	a.href = location;
	a.click();
}
// getting all the links in the directory

class Config {
	constructor() {
		this.total_popup = 0;
		this.popup_msg_open = false;
		this.allow_Debugging = true;
		this.Debugging = false;
		this.is_touch_device = 'ontouchstart' in document.documentElement;

		this.previous_type = null;
		this.themes = ["Tron"];

		this.is_webkit = navigator.userAgent.indexOf('AppleWebKit') != -1;
		this.is_edge = navigator.userAgent.indexOf('Edg') != -1;
	}
}
var config = new Config();

class PrefStoreManager {
	constructor(prefix = "pyrobox_pref_") {
		this.prefix = prefix;
	}

	set(key, value, useSession = false) {
		try {
			const storage = useSession ? sessionStorage : localStorage;
			storage.setItem(this.prefix + key, JSON.stringify(value));
		} catch (e) {
			console.error("Storage error:", e);
		}
	}

	get(key, defaultValue = null, useSession = false) {
		try {
			const storage = useSession ? sessionStorage : localStorage;
			const val = storage.getItem(this.prefix + key);
			return val ? JSON.parse(val) : defaultValue;
		} catch (e) {
			console.error("Storage error:", e);
			return defaultValue;
		}
	}
}
var pref_store = new PrefStoreManager();

class Tools {
	// various tools for the page
	refresh() {
		// refreshes the page
		window.location.reload();
	}
	sleep(ms) {
		// sleeps for a given time in milliseconds
		return new Promise(resolve => setTimeout(resolve, ms));
	}
	onlyInt(str) {
		if (this.is_defined(str.replace)) {
			return parseInt(str.replace(/\D+/g, ""));
		}
		return 0;
	}

	c_time() {
		// returns current time in milliseconds
		return new Date().getTime();
	}


	/**
	 * Returns the current date and time.
	 * @returns {Date} The current date and time.
	 */
	datetime() {
		return new Date(Date.now());
	}


	/**
	 * Returns the time offset in milliseconds.
	 * @returns {number} The time offset in milliseconds.
	 * @see {@link https://stackoverflow.com/questions/60207534/new-date-gettimezoneoffset-returns-the-wrong-time-zone}
	 */
	time_offset() {
		// for the reason of negative sign
		return new Date().getTimezoneOffset() * 60 * 1000 * -1;
	}


	/**
	 * Removes all child nodes of the given element.
	 * @param {string|HTMLElement} elm - The element or its ID to remove child nodes from.
	 */
	del_child(elm) {
		if (typeof (elm) == "string") {
			elm = byId(elm);
		}
		if (elm == null) {
			return;
		}
		while (elm.firstChild) {
			elm.removeChild(elm.lastChild);
		}
	}


	/**
	 * Toggles a boolean value.
	 * @param {boolean} bool - The boolean value to toggle.
	 * @returns {boolean} - The toggled boolean value.
	 */
	toggle_bool(bool) {
		return bool !== true;
	}


	exists(name) {
		return (typeof window[name] !== 'undefined');
	}


	/**
	 * Checks if an element has a given class.
	 * @param {Element} element - The element to check.
	 * @param {string} className - The class name to check for.
	 * @param {boolean} [partial=false] - Whether to check for a partial match of the class name.
	 * @returns {boolean} - Whether the element has the given class.
	 */
	hasClass(element, className, partial = false) {
		if (partial) {
			className = ' ' + className;
		} else {
			className = ' ' + className + ' ';
		}
		return (' ' + element.className + ' ').indexOf(className) > -1;
	}


	/**
	 * Adds a class to an element if it doesn't already have it.
	 * @param {Element} element - The element to add the class to.
	 * @param {string} className - The class name to add.
	 * @returns {void}
	 */
	addClass(element, className) {
		if (!this.hasClass(element, className)) {
			element.classList.add(className);
		}
	}

	/**
	 * Adds a script element to the document body with the specified URL.
	 * @param {string} url - The URL of the script to add.
	 * @returns {HTMLScriptElement} The newly created script element.
	 */
	add_script(src, { crossorigin = null, referrerpolicy = null, asyncLoad = null, integrity = null } = {}) {
		var script = createElement('script');
		script.src = src;
		if (crossorigin != null) script.crossorigin = crossorigin;
		if (referrerpolicy != null) script.referrerpolicy = referrerpolicy;
		if (asyncLoad != null) script.async = asyncLoad;
		if (integrity != null) script.integrity = integrity;


		if (typeof (document.body) === "undefined" || document.body === null) document.head.appendChild(script);
		else document.body.appendChild(script);

		return script;
	}

	add_css(href, { crossorigin = null, referrerpolicy = null, integrity = null } = {}) {
		var cssFile = createElement('link');
		cssFile.setAttribute("rel", "stylesheet");
		cssFile.href = href;
		if (crossorigin != null) cssFile.crossorigin = crossorigin;
		if (referrerpolicy != null) cssFile.referrerpolicy = referrerpolicy;
		if (integrity != null) cssFile.integrity = integrity;

		if (typeof (document.body) === "undefined") document.head.appendChild(cssFile);
		else document.body.appendChild(cssFile);

		return cssFile;
	}

	/**
	 * Enables debugging mode by adding the eruda script to the document head.
	 * @returns {void}
	 */
	enable_debug() {
		const that = this;
		if (!config.allow_Debugging) {
			return;
		}
		if (config.Debugging) {
			return
		}
		// config.Debugging = true;
		// var script = this.add_script("https://cdn.jsdelivr.net/npm/eruda");
		// script.onload = function () {
		// 	if (that.is_touch_device()) {
		// 		eruda.init()
		// 	}
		// };
	}


	/**
	 * Checks if an item is present in an array.
	 * @param {any} item - The item to check for.
	 * @param {Array} array - The array to search in.
	 * @returns {boolean} - Returns `true` if the item is present in the array, `false` otherwise.
	 */
	is_in(item, array) {
		return array.indexOf(item) > -1;
	}


	/**
	 * Checks if a given object is defined.
	 * @param {any} obj - The object to check.
	 * @returns {boolean} - Returns `true` if the object is defined, `false` otherwise.
	 */
	is_defined(obj) {
		return typeof (obj) !== "undefined"
	}

	/**
	 * Toggles the scroll of the document body.
	 * @param {number} [allow=2] - Determines whether to allow scrolling. `0`: no scrolling, `1`: scrolling allowed, `2`: toggle scrolling.
	 * @param {string} [by="someone"] - The name of the function toggling the scroll.
	 */
	toggle_scroll(allow = 2) {
		if (allow == 0) {
			document.body.classList.add('overflowHidden');
		} else if (allow == 1) {
			document.body.classList.remove('overflowHidden');
		} else {
			document.body.classList.toggle('overflowHidden');
		}
	}


	/**
	 * Downloads a file from a given data URL.
	 * @param {string} dataurl - The data URL of the file to download.
	 * @param {string|null} [filename=null] - The name to give the downloaded file. If null, the file will be named "download".
	 * @param {boolean} [new_tab=false] - Whether to open the download in a new tab.
	 */
	download(dataurl, filename = null, new_tab = false) {
		const link = createElement("a");
		link.href = dataurl;
		link.download = filename;
		if (new_tab) {
			link.target = "_blank";
		}
		link.click();
	}


	/**
	 * Pushes a new state object onto the history stack with a fake URL.
	 * Used to prevent the browser from navigating to a new page when a link is clicked.
	 */
	fake_push(state = {}) {
		history.pushState({
			url: window.location.href,
			state: state
		}, document.title, window.location.href)
	}

	/**
	 * Returns the full URL path for a given relative path.
	 * @param {string} rel_path - The relative path to convert to a full URL path.
	 * @returns {string} - The full URL path for the given relative path.
	 */
	full_path(rel_path) {
		let fake_a = createElement("a")
		fake_a.href = rel_path;
		return fake_a.href;
	}




	/**
	 * Adds a query parameter to the given URL.
	 *
	 * @param {string} url - The URL to add the query parameter to.
	 * @param {string} query - The name of the query parameter to add.
	 * @param {string} [value=''] - The value of the query parameter to add.
	 * @returns {string} The updated URL with the added query parameter.
	 */
	add_query(url, query, value = '') {
		var url_ = this.full_path(url);
		const url_obj = new URL(url_);
		url_obj.searchParams.set(query, value);

		return url_obj.href;
	}

	/**
	 * Adds a query parameter to the current URL and returns the modified URL.
	 * @param {string} query - The query parameter to add.
	 * @param {string} [value=''] - The value of the query parameter. Defaults to an empty string.
	 * @returns {string} The modified URL with the added query parameter.
	 */
	add_query_here(query, value = '') {
		return this.add_query(window.location.href, query, value);
	}



	/**
	 * Copies the given text to the clipboard using the Navigator Clipboard API if available and the context is secure (https).
	 * Otherwise, it uses a textarea element to copy the text to the clipboard.
	 * @param {Event} ev - The event that triggered the copy action.
	 * @param {string} textToCopy - The text to be copied to the clipboard.
	 * @returns {Promise<number>} - A promise that resolves to 1 if the text was successfully copied to the clipboard, or 0 otherwise.
	 */
	async copy_2(ev, textToCopy) {
		// navigator clipboard api needs a secure context (https)
		if (navigator.clipboard && window.isSecureContext) {
			// navigator clipboard api method'
			await navigator.clipboard.writeText(textToCopy);
			return 1;
		} else {
			// text area method
			let textArea = createElement("textarea");
			textArea.value = textToCopy;
			// make the textarea out of viewport
			textArea.style.position = "fixed";
			textArea.style.left = "-999999px";
			textArea.style.top = "-999999px";
			document.body.appendChild(textArea);
			textArea.focus();
			textArea.select();

			let ok = 0;
			// here the magic happens
			if (document.execCommand('copy')) ok = 1;

			textArea.remove();
			return ok;

		}
	}

	async fetch_json(url) {
		return fetch(url)
			.then(r => r.json())
			.catch(e => {
				console.log(e); return null;
			})
	}

	/**
	 * Checks if the app is running in standalone mode.
	 *
	 * @returns {boolean} - `true` if the app is running in standalone mode, `false` otherwise.
	 */
	is_standalone() {
		const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
		if (document.referrer.startsWith('android-app://')) {
			return true; // twa-pwa
		} else if (navigator.standalone || isStandalone) {
			return true;
		}
		return false;
	}

	/**
	 * Checks if the current device has touch capabilities.
	 *
	 * @returns {boolean} - `true` if the device has touch capabilities, `false` otherwise.
	 */
	is_touch_device() {
		return 'ontouchstart' in document.documentElement;
	}


	async is_installed() {
		var listOfInstalledApps = []
		if ("getInstalledRelatedApps" in navigator) {
			listOfInstalledApps = await navigator.getInstalledRelatedApps();
		}
		// console.log(listOfInstalledApps)
		for (const app of listOfInstalledApps) {
			// These fields are specified by the Web App Manifest spec.
			console.log('platform:', app.platform);
			console.log('url:', app.url);
			console.log('id:', app.id);

			// This field is provided by the UA.
			console.log('version:', app.version);
		}

		return listOfInstalledApps;
	}

	get AMPM_time() {
		var date = new Date();
		var hours = date.getHours();
		var minutes = date.getMinutes();
		var ampm = hours >= 12 ? 'pm' : 'am';
		hours = hours % 12;
		hours = hours ? hours : 12; // the hour '0' should be '12'
		minutes = minutes < 10 ? '0' + minutes : minutes;
		var strTime = hours + ':' + minutes + ' ' + ampm;
		return strTime;
	}


	/**
	 * Sets a cookie with the given name, value and expiration days.
	 *
	 * @param {string} cname - The name of the cookie.
	 * @param {string} cvalue - The value of the cookie.
	 * @param {number} [exdays=365] - The number of days until the cookie expires.
	 */
	setCookie(cname, cvalue, exdays = 365) {
		const d = new Date();
		d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
		let expires = "expires=" + d.toUTCString();
		document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
	}

	/**
	 * Retrieves the value of a cookie with the given name.
	 *
	 * @param {string} cname - The name of the cookie to retrieve.
	 * @returns {string} The value of the cookie, or an empty string if the cookie does not exist.
	 */
	getCookie(cname) {
		let name = cname + "=";
		let decodedCookie = decodeURIComponent(document.cookie);
		let ca = decodedCookie.split(';');
		for (let i = 0; i < ca.length; i++) {
			let c = ca[i];
			while (c.charAt(0) == ' ') {
				c = c.substring(1);
			}
			if (c.indexOf(name) == 0) {
				return c.substring(name.length, c.length);
			}
		}
		return "";
	}

	/**
	 * Clears all cookies by setting their expiration date to the past.
	 */
	clear_cookie() {
		document.cookie.split(";").forEach(c => {
			document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
		}
		);
	}

	// pass expected list of properties and optional maxLen
	// returns obj or null
	safeJSONParse(str, propArray, maxLen) {
		var parsedObj, safeObj = {};
		try {
			if (maxLen && str.length > maxLen) {
				return null;
			} else {
				parsedObj = JSON.parse(str);
				if (typeof parsedObj !== "object" || Array.isArray(parsedObj)) {
					safeObj = parsedObj;
				} else {
					// copy only expected properties to the safeObj
					propArray.forEach(function (prop) {
						if (parsedObj.hasOwnProperty(prop)) {
							safeObj[prop] = parsedObj[prop];
						}
					});
				}
				return safeObj;
			}
		} catch (e) {
			return null;

		}
	}
}
var tools = new Tools();


'#########################################'
tools.enable_debug(); // TODO: Disable this in production
'#########################################'

/**
 * Represents a popup message.
 * @class
 */
class Popup_Msg {
	/**
	 * Creates an instance of Popup_Msg.
	 */
	constructor() {
		this.made_popup = false;
		this.init();
		this.create();
		this.opened = false;
	}

	/**
	 * Cleans the header and content of the popup.
	 */
	clean() {
		tools.del_child(this.header);
		tools.del_child(this.content);
	}

	/**
	 * Initializes the popup message.
	 */
	init() {
		this.onclose = null_func;
		this.scroll_disabled = false;

		this.popup_container = byId("popup-container");
		if (this.popup_container == null || !this.popup_container) {
			log("Popup container not found");
			log("Creating new popup container");
			this.popup_container = createElement("div");
			this.popup_container.id = "popup-container";
			document.body.appendChild(this.popup_container);
			const style = createElement("style");
			style.innerHTML = `
				.modal_bg {
					display: inherit;
					position: fixed;
					z-index: 1;
					padding-top: inherit;
					left: 0;
					top: 0;
					width: 100vw;
					height: 100vh;
					overflow: auto;
				}

				.popup {
					position: fixed;
					z-index: 22;
					left: 50%;
					top: 50%;
					width: 100%;
					height: 100%;
					overflow: hidden;
					transition: all .5s ease-in-out;
					transform: translate(-50%, -50%) scale(1)
				}

				.popup-box {
					/*Proxy, reinitialized in html_style.css*/
					display: block;
					/*display: inline;*/
					/*text-align: center;*/
					position: fixed;
					top: 50%;
					left: 50%;
					color: #e9f4ff;
					transition: all 400ms ease-in-out;
					background: #292929;
					width: 95%;
					max-width: 500px;
					z-index: 23;
					padding: 20px;
					box-sizing: border-box;
					max-height: min(600px, 80%);
					height: max-content;
					min-height: 300px;
					overflow: auto;
					border-radius: 6px;
					text-align: center;
					overflow-wrap: anywhere;
				}

				.popup-close-btn {
					cursor: pointer;
					position: absolute;
					right: 20px;
					top: 20px;
					width: 30px;
					height: 30px;
					background: #222;
					color: #fff;
					font-size: 25px;
					font-weight: 600;
					line-height: 30px;
					text-align: center;
					border-radius: 50%
				}

				.popup:not(.active) {
					transform: translate(-50%, -50%) scale(0);
					opacity: 0;
				}

				.popup.active .popup-box {
					transform: translate(-50%, -50%) scale(1);
					opacity: 1;
				}
			`;
			document.body.appendChild(style);
		}
	}

	/**
	 * Checks if the popup is active.
	 * @returns {boolean} True if the popup is active, false otherwise.
	 */
	is_active() {
		return this.popup_obj.classList.contains("active");
	}

	/**
	 * Creates the popup message.
	 */
	create() {
		var that = this;
		let popup_id, popup_obj, popup_bg, close_btn, popup_box;

		popup_id = config.total_popup;
		config.total_popup += 1;

		popup_obj = createElement("div");
		popup_obj.id = "popup-" + popup_id;
		popup_obj.classList.add("popup");

		popup_bg = createElement("div");
		popup_bg.classList.add("modal_bg");
		popup_bg.id = "popup-bg-" + popup_id;
		popup_bg.onclick = function () {
			that.close();
		};

		popup_obj.appendChild(popup_bg);

		this.popup_obj = popup_obj;
		this.popup_bg = popup_bg;

		popup_box = createElement("div");
		popup_box.classList.add("popup-box");

		close_btn = createElement("div");
		close_btn.className = "popup-btn disable_selection popup-close-btn";
		close_btn.onclick = function () {
			that.close();
		};
		close_btn.innerHTML = "&times;";
		popup_box.appendChild(close_btn);

		this.header = createElement("h1");
		this.header.style.marginBottom = "10px";
		this.header.id = "popup-header-" + popup_id;
		popup_box.appendChild(this.header);

		this.hr = createElement("hr");
		this.hr.style.width = "95%";
		popup_box.appendChild(this.hr);

		this.content = createElement("div");
		this.content.id = "popup-content-" + popup_id;
		popup_box.appendChild(this.content);
		this.popup_obj.appendChild(popup_box);

		byId("popup-container").appendChild(this.popup_obj);
	}

	/**
	 * Closes the popup message.
	 */
	async close() {
		this.onclose();
		await this.dismiss();
		config.popup_msg_open = false;
		this.init();
		console.debug("Popup closed");
	}

	/**
	 * Hides the popup message.
	 */
	hide() {
		this.opened = false;
		this.popup_obj.classList.remove("active");
		tools.toggle_scroll(1);
	}

	/**
	 * Dismisses the popup message.
	 */
	async dismiss() {
		if (!this.is_active()) {
			return;
		}

		history.back(); //this.hide()

		await tools.sleep(200);

		tools.del_child(this.header);
		tools.del_child(this.content);
		this.made_popup = false;
	}

	/**
	 * Toggles the popup message.
	 * @param {boolean} [toggle_scroll=true] - Whether to toggle the scroll or not.
	 */
	async togglePopup(toggle_scroll = true) {
		if (!this.made_popup) {
			return;
		}
		this.popup_obj.classList.toggle("active");
		if (toggle_scroll) {
			tools.toggle_scroll();
		}
		// log(tools.hasClass(this.popup_obj, "active"))
		if (!tools.hasClass(this.popup_obj, "active")) {
			this.close();
		}
	}

	/**
	 * Opens the popup message.
	 * @param {boolean} [allow_scroll=false] - Whether to allow scrolling or not.
	 */
	async open_popup(allow_scroll = false) {
		if (!this.made_popup) {
			return;
		}

		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(this.popup_obj);
		}

		this.popup_obj.classList.add("active");
		config.popup_msg_open = this;

		if (!allow_scroll) {
			tools.toggle_scroll(0);
			this.scroll_disabled = true;
		}

		this.opened = true;
		tools.fake_push();

		HISTORY_ACTION.push(this.hide.bind(this));
	}

	/**
	 * Shows the popup message.
	 * @param {boolean} [allow_scroll=false] - Whether to allow scrolling or not.
	 */
	async show(allow_scroll = false) {
		this.open_popup(allow_scroll);
	}

	/**
	 * Creates a popup message.
	 * @param {string|Element} [header=""] - The header of the popup message.
	 * @param {string|Element} [content=""] - The content of the popup message.
	 * @param {boolean} [hr=true] - Whether to display a horizontal rule or not.
	 * @param {function} [onclose=null_func] - The function to call when the popup message is closed.
	 */
	async createPopup(header = "", content = "", hr = true, onclose = null_func, script = "") {
		this.init();
		this.clean();
		this.onclose = onclose;
		this.made_popup = true;
		if (typeof header === "string" || header instanceof String) {
			this.header.innerHTML = header;
		} else if (header instanceof Element) {
			this.header.appendChild(header);
		}
		if (typeof content === "string" || content instanceof String) {
			this.content.innerHTML = content;
		} else if (content instanceof Element) {
			this.content.appendChild(content);
		}
		if (hr) {
			this.hr.style.display = "block";
		} else {
			this.hr.style.display = "none";
		}

		if (script) {
			var script_tag = createElement("script");
			script_tag.innerHTML = script;
			this.content.appendChild(script_tag);
		}

		if (typeof theme_controller !== 'undefined' && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(this.popup_obj);
		}
	}
}
var popup_msg = new Popup_Msg();

/**
 * Represents a toaster object that can display toast messages on the screen.
 * @class
 */
class Toaster {
	constructor() {
		this.container = createElement("div");
		this.container.classList.add("toast-box");
		if (document.body) {
			document.body.appendChild(this.container);
		} else {
			window.addEventListener("DOMContentLoaded", () => {
				document.body.appendChild(this.container);
			});
		}

		this.maxToasts = 5;
		this.activeToasts = [];
		this._recentRegistry = new Map();
	}

	/**
	 * Displays a toast notification on the screen.
	 * @param {string|Object} msg - The message to be displayed or an options object.
	 * @param {number|string} [time] - Duration in ms, or category/background color if passed as a string.
	 * @param {string} [bgcolor=''] - The category or background color of the toast.
	 * @returns {Promise<void> & { close: Function, el: HTMLElement }}
	 */
	toast(msg, time, bgcolor = '') {
		let text = msg;
		let duration = time;
		let customBg = bgcolor;
		let type = "";
		let icon = "";
		let closeable = true;

		if (typeof msg === "object" && msg !== null && !(msg instanceof Element)) {
			text = msg.message || msg.msg || msg.text || "";
			duration = tools.is_defined(msg.duration) ? msg.duration : (tools.is_defined(msg.time) ? msg.time : undefined);
			customBg = msg.bgcolor || msg.color || msg.category || "";
			type = msg.type || msg.category || "";
			icon = msg.icon || "";
			if (tools.is_defined(msg.closeable)) closeable = Boolean(msg.closeable);
		}

		// If duration was passed as category/color string
		if (typeof duration === "string" && !customBg && isNaN(Number(duration))) {
			customBg = duration;
			duration = undefined;
		}

		let sleepTime = 3500;
		if (tools.is_defined(duration)) {
			sleepTime = Number(duration);
		} else if (typeof text === "string") {
			sleepTime = Math.max(3000, Math.min(8000, text.length * 60));
		}

		// Normalize semantic type
		const rawCat = (type || customBg || "").toLowerCase();
		if (rawCat.includes("green") || rawCat.includes("185") || rawCat.includes("10b981") || rawCat.includes("success")) {
			type = "success";
		} else if (rawCat.includes("red") || rawCat.includes("225") || rawCat.includes("239") || rawCat.includes("f43f5e") || rawCat.includes("danger") || rawCat.includes("error")) {
			type = "error";
		} else if (rawCat.includes("orange") || rawCat.includes("yellow") || rawCat.includes("230") || rawCat.includes("245") || rawCat.includes("warning") || rawCat.includes("warn")) {
			type = "warning";
		} else if (rawCat.includes("blue") || rawCat.includes("cyan") || rawCat.includes("136") || rawCat.includes("165") || rawCat.includes("skyblue") || rawCat.includes("00b4d8") || rawCat.includes("info")) {
			type = "info";
		} else if (!type) {
			type = "info";
		}

		// De-duplication (suppress duplicate toast within 1.5s)
		const textStr = String(text instanceof Element ? text.innerText : text);
		const dedupKey = type + "::" + textStr;
		const now = Date.now();
		for (const [k, ts] of this._recentRegistry.entries()) {
			if (now - ts > 1500) this._recentRegistry.delete(k);
		}
		if (this._recentRegistry.has(dedupKey)) {
			const resolvedPromise = Promise.resolve();
			resolvedPromise.close = () => {};
			return resolvedPromise;
		}
		this._recentRegistry.set(dedupKey, now);

		// Dismiss oldest toast if maximum reached
		while (this.activeToasts.length >= this.maxToasts) {
			const oldest = this.activeToasts[0];
			if (oldest && typeof oldest.dismiss === "function") {
				oldest.dismiss();
			} else {
				break;
			}
		}

		const toastBody = createElement("div");
		toastBody.classList.add("toast-body");
		if (type) toastBody.classList.add("toast-" + type);

		// Icon logic matching FinanceManager
		const categoryIcons = {
			info: { fa: "fa-solid fa-circle-info", emoji: "ℹ️" },
			success: { fa: "fa-solid fa-circle-check", emoji: "✅" },
			warning: { fa: "fa-solid fa-triangle-exclamation", emoji: "⚠️" },
			error: { fa: "fa-solid fa-circle-xmark", emoji: "❌" }
		};

		const hasLeadingIconOrEmoji = /^(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff]|<i\s|<span\s)/i.test(textStr.trim());

		if (icon || (!hasLeadingIconOrEmoji && categoryIcons[type])) {
			const iconEl = createElement("span");
			iconEl.classList.add("toast-icon");
			if (icon) {
				if (typeof icon === "string" && (icon.startsWith("<") || icon.includes("fa-") || icon.length > 2)) {
					if (icon.includes("fa-")) {
						iconEl.className = "toast-icon fa " + icon;
					} else {
						iconEl.innerHTML = icon;
					}
				} else {
					iconEl.textContent = icon;
				}
			} else {
				const catInfo = categoryIcons[type] || categoryIcons.info;
				iconEl.innerHTML = `<span class="fa ${catInfo.fa}">${catInfo.emoji}</span>`;
			}
			toastBody.appendChild(iconEl);
		}

		// Message element
		const msgEl = createElement("div");
		msgEl.classList.add("toast-message");
		if (text instanceof Element) {
			msgEl.appendChild(text);
		} else if (typeof text === "string") {
			if (text.includes("<") && text.includes(">")) {
				msgEl.innerHTML = text;
			} else {
				msgEl.innerText = text;
			}
		} else {
			msgEl.innerText = String(text);
		}
		toastBody.appendChild(msgEl);

		// Close button
		let dismissHandler = () => {};
		if (closeable) {
			const closeBtn = createElement("button");
			closeBtn.classList.add("toast-close-btn");
			closeBtn.setAttribute("type", "button");
			closeBtn.setAttribute("aria-label", "Close notification");
			closeBtn.innerHTML = '<span class="fa fa-solid fa-xmark">✕</span>';
			closeBtn.onclick = (e) => {
				e.stopPropagation();
				dismissHandler();
			};
			toastBody.appendChild(closeBtn);
		}

		// Strip emoji fallbacks if Font Awesome is loaded
		if (typeof theme_controller !== "undefined" && theme_controller.fa_ok) {
			theme_controller.del_fa_alt(toastBody);
		}

		let closePromiseResolver;
		const promise = new Promise((resolve) => {
			closePromiseResolver = resolve;
		});

		let timerId = null;
		let startTime = Date.now();
		let remainingTime = sleepTime;
		let isDismissed = false;

		const dismiss = () => {
			if (isDismissed) return;
			isDismissed = true;
			clearTimeout(timerId);
			const idx = this.activeToasts.indexOf(toastRef);
			if (idx !== -1) this.activeToasts.splice(idx, 1);

			toastBody.classList.remove("visible");
			toastBody.classList.add("closing");
			setTimeout(() => {
				if (toastBody.parentNode) toastBody.remove();
				closePromiseResolver();
			}, 350);
		};

		dismissHandler = dismiss;
		const toastRef = { el: toastBody, dismiss: dismiss };
		this.activeToasts.push(toastRef);

		// Pause / resume countdown on hover
		if (sleepTime > 0 && isFinite(sleepTime)) {
			const startTimer = () => {
				startTime = Date.now();
				timerId = setTimeout(dismiss, remainingTime);
			};

			const pauseTimer = () => {
				clearTimeout(timerId);
				const elapsed = Date.now() - startTime;
				remainingTime = Math.max(0, remainingTime - elapsed);
			};

			toastBody.addEventListener("mouseenter", pauseTimer);
			toastBody.addEventListener("mouseleave", () => {
				if (!isDismissed && remainingTime > 0) {
					startTimer();
				}
			});
		}

		this.container.appendChild(toastBody);

		// Trigger entrance animation
		requestAnimationFrame(() => {
			toastBody.classList.add("visible");
			if (sleepTime > 0 && isFinite(sleepTime)) {
				startTime = Date.now();
				timerId = setTimeout(dismiss, sleepTime);
			}
		});

		promise.close = dismiss;
		promise.el = toastBody;
		return promise;
	}

	success(msg, time) {
		return this.toast({ msg, time, type: "success" });
	}

	error(msg, time) {
		return this.toast({ msg, time, type: "error" });
	}

	warning(msg, time) {
		return this.toast({ msg, time, type: "warning" });
	}

	warn(msg, time) {
		return this.warning(msg, time);
	}

	info(msg, time) {
		return this.toast({ msg, time, type: "info" });
	}

	clear() {
		const list = [...this.activeToasts];
		for (const t of list) {
			t.dismiss();
		}
	}
}

var toaster = new Toaster();
window.flash = (msg, category, timeout) => toaster.toast(msg, timeout, category);



/**
 * A function to display a confirmation popup with yes and no buttons.
 * @param {Object} options - An object containing the following properties:
 * @param {function} options.y - The function to execute when the user clicks the "yes" button.
 * @param {function} [options.n=null] - The function to execute when the user clicks the "no" button. If not provided, the popup will simply close.
 * @param {string} [options.head="Head"] - The text to display in the popup header.
 * @param {string} [options.body="Body"] - The text to display in the popup body.
 * @param {string} [options.y_msg="Yes"] - The text to display on the "yes" button.
 * @param {string} [options.n_msg="No"] - The text to display on the "no" button.
 */
function r_u_sure({ y = null_func, n = null, head = "Are you sure?", body = "", y_msg = "Continue", n_msg = "Cancel" } = {}) {
	var box = createElement("div");
	box.className = "popup-dialog";
	var msggg = createElement("p");
	msggg.className = "popup-dialog-msg";
	msggg.innerHTML = body;
	box.appendChild(msggg);

	var actionsRow = createElement("div");
	actionsRow.className = "popup-actions-row";

	var y_btn = createElement("button");
	y_btn.type = "button";
	y_btn.innerText = y_msg;
	y_btn.className = "btn btn-danger";
	y_btn.onclick = y;

	var n_btn = createElement("button");
	n_btn.type = "button";
	n_btn.innerText = n_msg;
	n_btn.className = "btn";
	n_btn.onclick = () => { return (n === null) ? popup_msg.close() : n() };

	actionsRow.appendChild(y_btn);
	actionsRow.appendChild(n_btn);
	box.appendChild(actionsRow);

	popup_msg.createPopup(head, box);
	popup_msg.open_popup();
}






















var HISTORY_ACTION = [];


if (window.history && "pushState" in history) {
	// because JSHint told me to
	// handle forward/back buttons
	window.onpopstate = async function (evt) {
		"use strict";
		evt.preventDefault();
		// guard against popstate event on chrome init
		//log(evt.state)

		if (HISTORY_ACTION.length) {
			let action = HISTORY_ACTION.pop();
			action();

			return false;
		}

		const x = evt;
		if (x.state && x.state.url == window.location.href) {
			return false;
		}
		location.reload(true);
	};

}

