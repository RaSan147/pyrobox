const DEBUGGING = true;



const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);


String.prototype.toHtmlEntities = function() {
	return this.replace(/./ugm, s => s.match(/[a-z0-9\s]+/i) ? s : "&#" + s.codePointAt(0) + ";");
};





// pass expected list of properties and optional maxLen
// returns obj or null
function safeJSONParse(str, propArray, maxLen) {
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
				propArray.forEach(function(prop) {
					if (parsedObj.hasOwnProperty(prop)) {
						safeObj[prop] = parsedObj[prop];
					}
				});
			}
			return safeObj;
		}
	} catch(e) {
		return null;

	}
}





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
		this.allow_Debugging = DEBUGGING;
		this.Debugging = false;
		this.is_touch_device = 'ontouchstart' in document.documentElement;


		this.previous_type = null;
		this.themes = ["Tron"];



		this.is_webkit = navigator.userAgent.indexOf('AppleWebKit') != -1;
		this.is_edge = navigator.userAgent.indexOf('Edg') != -1;

	}
}
var config = new Config();


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
		if (typeof(elm) == "string") {
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
	add_script(url){
		var script = createElement('script');
		script.src = url;
		document.body.appendChild(script);

		return script;
	}

	/**
	 * Enables debugging mode by adding the eruda script to the document head.
	 * @returns {void}
	 */
	enable_debug() {
		const that = this;
		if (!config.allow_Debugging) {
			alert("Debugging is not allowed");
			return;
		}
		if (config.Debugging) {
			return
		}
		config.Debugging = true;
		var script = this.add_script("//cdn.jsdelivr.net/npm/eruda");
		script.onload = function() {
			if(that.is_touch_device()){
				eruda.init()
			}
		};
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
		return typeof(obj) !== "undefined"
	}

	/**
	 * Toggles the scroll of the document body.
	 * @param {number} [allow=2] - Determines whether to allow scrolling. `0`: no scrolling, `1`: scrolling allowed, `2`: toggle scrolling.
	 * @param {string} [by="someone"] - The name of the function toggling the scroll.
	 */
	toggle_scroll(allow = 2, by = "someone") {
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
	download(dataurl, filename = null, new_tab=false) {
		const link = createElement("a");
		link.href = dataurl;
		link.download = filename;
		if(new_tab){
			link.target = "_blank";
		}
		link.click();
	}


	/**
	 * Pushes a new state object onto the history stack with a fake URL.
	 * Used to prevent the browser from navigating to a new page when a link is clicked.
	 */
	fake_push(state={}){
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
	full_path(rel_path){
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
	add_query(url, query, value=''){
		const url_obj = new URL(url);
		url_obj.searchParams.set(query, value);

		return url_obj.href;
	}

	/**
	 * Adds a query parameter to the current URL and returns the modified URL.
	 * @param {string} query - The query parameter to add.
	 * @param {string} [value=''] - The value of the query parameter. Defaults to an empty string.
	 * @returns {string} The modified URL with the added query parameter.
	 */
	add_query_here(query, value=''){
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
			return 1
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

			let ok=0;
				// here the magic happens
				if(document.execCommand('copy')) ok = 1

			textArea.remove();
			return ok

		}
	}

	async fetch_json(url){
		return fetch(url).then(r => r.json()).catch(e => {console.log(e); return null;})
	}

	/**
	 * Checks if the app is running in standalone mode.
	 *
	 * @returns {boolean} - `true` if the app is running in standalone mode, `false` otherwise.
	 */
	is_standalone(){
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
	is_touch_device(){
		return 'ontouchstart' in document.documentElement;
	}


	async is_installed(){
		var listOfInstalledApps = []
		if("getInstalledRelatedApps" in navigator){
			listOfInstalledApps  = await navigator.getInstalledRelatedApps();
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

		return listOfInstalledApps
	}

	get AMPM_time() {
		var date = new Date();
		var hours = date.getHours();
		var minutes = date.getMinutes();
		var ampm = hours >= 12 ? 'pm' : 'am';
		hours = hours % 12;
		hours = hours ? hours : 12; // the hour '0' should be '12'
		minutes = minutes < 10 ? '0'+minutes : minutes;
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
	setCookie(cname, cvalue, exdays=365) {
		const d = new Date();
		d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
		let expires = "expires="+d.toUTCString();
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
		for(let i = 0; i <ca.length; i++) {
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
}
var tools = new Tools();


'#########################################'
tools.enable_debug() // TODO: Disable this in production
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
		popup_bg.style.backgroundColor = "#000000EE";
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
		console.log("Popup closed");
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
	}
}
var popup_msg = new Popup_Msg();

/**
 * Represents a toaster object that can display toast messages on the screen.
 * @class
 */
class Toaster {
	constructor() {
		this.container = createElement("div")
		this.container.classList.add("toast-box")
		document.body.appendChild(this.container)

		this.default_bg = "#005165ed";

		this.queue = []; // queue to prevent multiple toasts from being displayed at the same time
	}


	/**
	 * Displays a toast message on the screen.
	 * @async
	 * @param {string} msg - The message to be displayed in the toast.
	 * @param {number} time - The duration for which the toast should be displayed, in milliseconds.
	 * @param {string} [bgcolor=''] - The background color of the toast. If not provided, the default background color will be used.
	 * @returns {Promise<void>}
	 */
	async toast(msg, time, bgcolor='') {
		// toaster is not safe as popup by design
				var sleep = 3000;

		while (this.queue.length > 2) {
			await tools.sleep(100)
		}
		this.queue.push(true)

		let toastBody = createElement("div")
		toastBody.classList.add("toast-body")

		this.container.appendChild(toastBody)

		await tools.sleep(50) // wait for dom to update

		// SET BG COLOR
		toastBody.style.backgroundColor = bgcolor || this.default_bg;

		toastBody.innerText = msg;
		toastBody.classList.add("visible")
		if(tools.is_defined(time)) sleep = time;
		await tools.sleep(sleep)
		toastBody.classList.remove("visible")
		await tools.sleep(500)
		toastBody.remove()

		this.queue.pop()

	}
}

var toaster = new Toaster()



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
function r_u_sure({y=null_func, n=null, head="Are you sure", body="", y_msg="Yes",n_msg ="No"}={}) {
	// popup_msg.close()
	var box = createElement("div")
	var msggg = createElement("p")
	msggg.innerHTML = body; //"This can't be undone!!!"
	box.appendChild(msggg)
	var y_btn = createElement("div");
	y_btn.innerText = y_msg;//"Continue"
	y_btn.className = "pagination center";
	y_btn.onclick = y;/*function() {
		that.menu_click('del-p', file);
	};*/
	var n_btn = createElement("div");
	n_btn.innerText = n_msg;//"Cancel"
	n_btn.className = "pagination center";
	n_btn.onclick = () => {return (n===null) ? popup_msg.close() : n()};
	box.appendChild(y_btn);
	box.appendChild(line_break());
	box.appendChild(n_btn);
	popup_msg.createPopup(head, box) ; //"Are you sure?"
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

		if(HISTORY_ACTION.length){
			let action = HISTORY_ACTION.pop()
			action()

			return false
		}

		const x = evt
		if (x.state && x.state.url==window.location.href){
			return false
		}
		location.reload(true);
};

}

