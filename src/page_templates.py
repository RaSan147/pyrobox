from string import Template as _Template # using this because js also use {$var} and {var} syntax and py .format is often unsafe

__all__ = [
	"directory_explorer_header",
	"global_script",
	"file_list",
	"upload_form",
	"js_script",
	"video_script",
	"zip_script",
	"admin_page",
	"error_page",
]


# ---------------------------x--------------------------------

# PAGE TEMPLATES
##############################################################


class Template(_Template):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __add__(self, other):
		if isinstance(other, _Template):
			return Template(self.template + other.template)
		return Template(self.template + str(other))
	

enc = "utf-8"


class config:
	dev_mode = False
	file_list = {}

pt_config = config()


def get_template(path):
	if pt_config.dev_mode:
		with open(path, encoding=enc) as f:
			return Template(f.read())

	return Template(pt_config.file_list[path])

def directory_explorer_header():
	return get_template("html_page.html")


def global_script():
	return get_template("global_script.html")

def file_list():
	return global_script() + get_template("html_file_list.html")

def upload_form():
	return get_template("html_upload.html")

def js_script():
	return global_script() + get_template("html_script.html")

def video_script():
	return global_script() + get_template("html_vid.html")

def zip_script():
	return global_script() + get_template("html_zip_page.html")

def admin_page():
	return global_script() + get_template("html_admin.html")

def error_page():
	return directory_explorer_header() + get_template("html_error.html")








config.file_list["html_page.html"] = r"""
<!DOCTYPE HTML>
<!-- test1 -->
<html lang="en">
<head>
<meta charset="{UTF-8}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href='https://fonts.googleapis.com/css?family=Open Sans' rel='stylesheet'>
<title>${PY_PAGE_TITLE}</title>
</head>

<body>
<script>
const public_url = "${PY_PUBLIC_URL}";
</script>

<style type="text/css">

#content_list {
	/* making sure this don't get visible if js enabled */
	/* otherwise that part makes a wierd flash */
	display: none;
}


body {
	position: relative;
	min-height: 100vh;
	overflow-x: hidden;
}

html,
body,
input,
textarea,
select,
button {
	border-color: #736b5e;
	color: #e8e6e3;
	background-color: #181a1b;
}

* {
	scrollbar-color: #0f0f0f #454a4d;
	font-family: "Open Sans", sans-serif;
}


.center {
	text-align: center;
	margin: auto;
}

.dir_arrow {
	position: relative;
	top: -3px;
	padding: 4px;
	color: #e8e6e3;
	font-size: 12px;
}

.disable_selection {
	-webkit-touch-callout: none;
	/* iOS Safari */
	-webkit-user-select: none;
	/* Safari */
	-khtml-user-select: none;
	/* Konqueror HTML */
	-moz-user-select: none;
	/* Old versions of Firefox */
	-ms-user-select: none;
	/* Internet Explorer/Edge */
	user-select: none;
	/* Non-prefixed version, currently */
	-webkit-tap-highlight-color: rgba(0, 0, 0, 0);
}

a {
	/*line-height: 200%;*/
	font-size: 20px;
	font-weight: 600;
	text-decoration: none;
	color: #00BFFF;

	letter-spacing: .1em;
}

.dir_item {
	display: inline;
}



.all_link {
	display: block;
	white-space: wrap;
	overflow-wrap: anywhere;
	position: relative;
	border-radius: 5px;
}

.dir_item:active .link_name {
	color: red;
}

.dir_item:active .all_link, .dir_item:hover .all_link {
	background-color: #25a2c222;
}

.link_name {
	display: inline-block;
	font-size: .8em;
	word-wrap: break-all;
	padding: 5px;
	left: 50px;
	position: relative;
}

.link_icon {
	display: inline-block;
	font-size: 2em;
	left:0%;
	width: 40px;
}



.context_menu {
	margin-left: 10px;
}


.link {
	color: #1589FF;
	/* background-color: #1589FF; */
}

.vid {
	color: #8A2BE2;
	/* font-weight: 300; */
}

.file {
	color: #c07cf7;
}



::-webkit-scrollbar-track {
	background: #222;
}

::-webkit-scrollbar {
	width: 7px;
	height: 7px;
	opacity: 0.3;
}

::-webkit-scrollbar:hover {
	opacity: 0.9;
}

::-webkit-scrollbar-thumb {
	background: #333;
	border-radius: 10px;
}

:hover::-webkit-scrollbar-thumb {
	background: #666;
}

::-webkit-scrollbar-thumb:hover {
	background: #aaa;
}



#dir-tree {
	overflow-x: auto;
	overflow-y: hidden;
	white-space: nowrap;
	word-wrap: break-word;
	max-width: 98vw;
	border: #075baf 2px solid;
	border-radius: 5px;
	background-color: #0d29379f;
	padding: 0 5px;
	height: 50px;
}

.dir_turns {
	padding: 4px;
	border-radius: 5px;
	font-size: .6em;

}

.dir_turns:hover {
	background-color: #90cdeb82;
	color: #ffffff;
}



#drag-file-list {
	width: 98%;
	max-height: 300px;
	overflow: auto;
	padding: 20px 0;
	align-items: center;
}

.upload-file-item {
  display: block;
  border: 1px solid #ddd;
  margin-top: -1px; /* Prevent double borders */
  background-color: #f6f6f6;
  padding: 12px;
  text-decoration: none;
  font-size: 18px;
  color: black;
  position: relative;
  border-radius: 5px;

  max-width: 100%;
}

.file-size, .link_size {
	font-size: .6em;
	font-weight: 600;
	background-color: #19a6c979;
	padding: 3px;
	display: inline-block;
	color: #fff;
	border-radius: 4px;

}

.file-size, .file-remove, .link_icon {
	white-space: nowrap;

	position: absolute;
	top: 50%;
	transform: translate(0%, -50%);
}



.file-name, .link_name {
	display: inline-block;
	word-wrap: break-all;
	overflow-wrap: anywhere;
	width: 70%;
}

.link_name {
	width: calc(100% - 57px);

}


.file-remove {
  padding: 5px 7px;
  margin: 0 5px;
  margin-right: 10px;
  cursor: pointer;
  font-size: 23px;
  color: #fff;
  background-color: #505050;
  border-radius: 5px;
  font-weight: 900;
  right: 0%;

}


#footer {
	position: absolute;
	bottom: 0;
	width: 100%;
	height: 2.5rem;
	/* Footer height */
}


.overflowHidden {
	overflow: hidden !important
}


/* POPUP CSS */

.modal_bg {
	display: inherit;
	position: fixed;
	z-index: 1;
	padding-top: inherit;
	left: 0;
	top: 0;
	width: 100%;
	height: 100%;
	overflow: auto;
}


.popup {
	position: fixed;
	z-index: 22;
	left: 50%;
	top: 50%;
	width: 100%;
	height: 100%;
	overflow: none;
	transition: all .5s ease-in-out;
	transform: translate(-50%, -50%) scale(1)
}

.popup-box {
	display: block;
	/*display: inline;*/
	/*text-align: center;*/
	position: fixed;
	top: 50%;
	left: 50%;
	color: #BBB;
	transition: all 400ms ease-in-out;
	background: #222;
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



.pagination {
	cursor: pointer;
	width: 150px;
	max-width: 800px
}

.pagination {
	font: bold 20px Arial;
	text-decoration: none;
	background-color: #8a8b8d6b;
	color: #1f83b6;
	padding: 2px 6px;
	border-top: 1px solid #828d94;
	box-shadow: 4px 4px #5050506b;
	border-left: 1px solid #828D94;
}

.pagination:hover {
	background-color: #4e4f506b;
	color: #00b7ff;
	box-shadow: 4px 4px #8d8d8d6b;
	border: none;
	border-right: 1px solid #959fa5;
	border-bottom: 1px solid #959fa5
}

.pagination:active {
	position: relative;
	top: 4px;
	left: 4px;
	box-shadow: none
}



.menu_options {
	background: #333;
	width: 95%;
	padding: 5px;
	margin: 5px;
	text-align: left;
	cursor: pointer;
}

.menu_options:hover,
.menu_options:focus {
	background: #337;

}


ul{
	list-style-type: none; /* Remove bullets */
	padding-left: 5px;
	margin: 0;
}

.upload-pass {
	background-color: #000;
	padding: 5px;
	border-radius: 4px;
	font: 1.5em sans-serif;
}

.upload-pass-box {
	/* make text field larger */
	font-size: 1.5em;
	border: #aa00ff solid 2px;;
	border-radius: 4px;
	background-color: #0f0f0f;
}


.upload-box {
	display: flex;
	align-items: center;
	justify-content: center;
}
.drag-area{
	border: 2px dashed #fff;
	height: 300px;
	width: 95%;
	border-radius: 5px;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-direction: column;
}
.drag-area.active{
	border: 2px solid #fff;
}
.drag-area .drag-icon{
	font-size: 100px;
	color: #fff;
}
.drag-area header{
	font-size: 25px;
	font-weight: 500;
	color: #fff;
}
.drag-area span{
	font-size: 20px;
	font-weight: 500;
	color: #fff;
	margin: 10px 0 15px 0;
}
.drag-browse, #submit-btn{
	padding: 10px 25px;
	font-size: 20px;
	font-weight: 500;
	outline: none;
	background: #fff;
	color: #5256ad;
	border-radius: 5px;
	border: solid 2px #00ccff;
	cursor: pointer;
}

.toast-box {
	z-index: 99;

	position: fixed;
	bottom: 0;
	right: 0;
	max-width: 100%;
	overflow-wrap: anywhere;
	transform: translateY(100%);
	opacity: 0;

	transition:
		opacity 500ms,
		transform 500ms;
}

.toast-box.visible {
	transform: translateY(0);
	opacity: 1;
}


.toast-body {
	max-height: 100px;
	overflow-y: auto;
	margin: 28px;
	padding: 10px;

	font-size: 1em;
	background-color: #005165ed;
	color: #fff;

	border-radius: 4px;
}


.update_text {
	font-size: 1.5em;
	padding: 5px;
	margin: 5px;
	border: solid 2px;
	border-radius: 4px;
}



</style>

<noscript>
	<style>
		.jsonly {
			display: none !important
		}

		#content_list {
			/* making sure its visible */
			display: block;
		}
	</style>
</noscript>

<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.png?raw=true" type="image/png">



<div id="popup-container"></div>

<h1 id="dir-tree">${PY_DIR_TREE_NO_JS}</h1>
<hr>

<script>
const dir_tree = document.getElementById("dir-tree");
dir_tree.scrollLeft = dir_tree.scrollWidth;
</script>

<hr>
"""



#######################################################

#######################################################

config.file_list["global_script.html"] = r"""
<script>
const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);


String.prototype.toHtmlEntities = function() {
	return this.replace(/./ugm, s => s.match(/[a-z0-9\s]+/i) ? s : "&#" + s.codePointAt(0) + ";");
};









function null_func() {
	return true
}

function line_break() {
	var br = createElement("br")
	return br
}

function toggle_scroll() {
	document.body.classList.toggle('overflowHidden');
}

function go_link(typee, locate) {
	// function to generate link for different types of actions
	return locate + "?" + typee;
}
// getting all the links in the directory

class Config {
	constructor() {
		this.total_popup = 0;
		this.popup_msg_open = false;
		this.allow_Debugging = true
		this.Debugging = false;
	}
}
var config = new Config()


class Tools {
	// various tools for the page
	sleep(ms) {
		// sleeps for a given time in milliseconds
		return new Promise(resolve => setTimeout(resolve, ms));
	}
	onlyInt(str) {
		if (this.is_defined(str.replace)) {
			return parseInt(str.replace(/\D+/g, ""))
		}
		return 0;
	}
	del_child(elm) {
		if (typeof(elm) == "string") {
			elm = byId(elm)
		}
		while (elm.firstChild) {
			elm.removeChild(elm.lastChild);
		}
	}
	toggle_bool(bool) {
		return bool !== true;
	}
	exists(name) {
		return (typeof window[name] !== 'undefined')
	}
	hasClass(element, className, partial = false) {
		if (partial) {
			className = ' ' + className;
		} else {
			className = ' ' + className + ' ';
		}
		return (' ' + element.className + ' ').indexOf(className) > -1;
	}
	addClass(element, className) {
		if (!this.hasClass(element, className)) {
			element.classList.add(className);
		}
	}
	enable_debug() {
		if (!config.allow_Debugging) {
			alert("Debugging is not allowed");
			return;
		}
		if (config.Debugging) {
			return
		}
		config.Debugging = true;
		var script = createElement('script');
		script.src = "//cdn.jsdelivr.net/npm/eruda";
		document.body.appendChild(script);
		script.onload = function() {
			eruda.init()
		};
	}
	is_in(item, array) {
		return array.indexOf(item) > -1;
	}
	is_defined(obj) {
		return typeof(obj) !== "undefined"
	}
	toggle_scroll(allow = 2, by = "someone") {
		if (allow == 0) {
			document.body.classList.add('overflowHidden');
		} else if (allow == 1) {
			document.body.classList.remove('overflowHidden');
		} else {
			document.body.classList.toggle('overflowHidden');
		}
	}
	download(dataurl, filename = null, new_tab=false) {
		const link = createElement("a");
		var Q = "?dl"
		// if ? in URL as Query, then use & to add dl
		if(dataurl.indexOf("?") > -1){
			Q = "&dl"
		}
		link.href = dataurl+Q;
		link.download = filename;
		if(new_tab){
			link.target = "_blank";
		}
		link.click();
	}

	full_path(rel_path){
		let fake_a = createElement("a")
		fake_a.href = rel_path;
		return fake_a.href;
	}


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

	fetch_json(url){
		return fetch(url).then(r => r.json()).catch(e => {console.log(e); return null;})
	}
}
let tools = new Tools();




'#########################################'
tools.enable_debug() // TODO: Disable this in production
'#########################################'

class Popup_Msg {
	constructor() {
		this.create()
		this.made_popup = false;
		this.init()
	}
	init() {
		this.onclose = null_func;
		this.scroll_disabled = false;
	}
	create() {
		var that = this;
		let popup_id, popup_obj, popup_bg, close_btn, popup_box;

		popup_id = config.total_popup;



		popup_obj = createElement("div")
		popup_obj.id = "popup-" + popup_id;
		popup_obj.classList.add("popup")

		popup_bg = createElement("div")
		popup_bg.classList.add("modal_bg")
		popup_bg.id = "popup-bg-" + popup_id;
		popup_bg.style.backgroundColor = "#000000EE";
		popup_bg.onclick = function() {
			that.close()
		}

		popup_obj.appendChild(popup_bg);

		this.popup_obj = popup_obj
		this.popup_bg = popup_bg


		popup_box = createElement("div");
		popup_box.classList.add("popup-box")

		close_btn = createElement("div");
		close_btn.classList.add("popup-close-btn")
		close_btn.onclick = function() {
			that.close()
		}
		close_btn.innerHTML = "&times;";
		popup_box.appendChild(close_btn)
		this.header = createElement("h1")
		this.header.id = "popup-header-" + popup_id;
		popup_box.appendChild(this.header)
		this.hr = createElement("popup-hr-" + popup_id);
		this.hr.style.width = "95%"
		popup_box.appendChild(this.hr)
		this.content = createElement("div")
		this.content.id = "popup-content-" + popup_id;
		popup_box.appendChild(this.content)
		this.popup_obj.appendChild(popup_box)

		byId("popup-container").appendChild(this.popup_obj)
		config.total_popup += 1;
	}
	close() {
		this.onclose()
		this.dismiss()
		config.popup_msg_open = false;
		this.init()
	}
	hide() {
		this.popup_obj.classList.remove("active");
		tools.toggle_scroll(1)
	}
	dismiss() {
		this.hide()
		tools.del_child(this.header);
		tools.del_child(this.content);
		this.made_popup = false;
	}
	async togglePopup(toggle_scroll = true) {
		if (!this.made_popup) {
			return
		}
		this.popup_obj.classList.toggle("active");
		if (toggle_scroll) {
			tools.toggle_scroll();
		}
		// log(tools.hasClass(this.popup_obj, "active"))
		if (!tools.hasClass(this.popup_obj, "active")) {
			this.close()
		}
	}
	async open_popup(allow_scroll = false) {
		if (!this.made_popup) {
			return
		}
		this.popup_obj.classList.add("active");
		if (!allow_scroll) {
			tools.toggle_scroll(0);
			this.scroll_disabled = true;
		}
	}
	async createPopup(header = "", content = "", hr = true) {
		this.init()
		this.made_popup = true;
		if (typeof header === 'string' || header instanceof String) {
			this.header.innerHTML = header;
		} else if (header instanceof Element) {
			this.header.appendChild(header)
		}
		if (typeof content === 'string' || content instanceof String) {
			this.content.innerHTML = content;
		} else if (content instanceof Element) {
			this.content.appendChild(content)
		}
		if (hr) {
			this.hr.style.display = "block";
		} else {
			this.hr.style.display = "none";
		}

	}
}
let popup_msg = new Popup_Msg();

class Toaster {
	constructor() {
		this.container = createElement("div")
		this.container.classList.add("toast-box")
		this.toaster = createElement("div")
		this.toaster.classList.add("toast-body")

		this.container.appendChild(this.toaster)
		document.body.appendChild(this.container)

		this.BUSY = 0;
	}


	async toast(msg,time) {
		// toaster is not safe as popup by design
		var sleep = 3000;

		this.BUSY = 1;
		this.toaster.innerText = msg;
		this.container.classList.add("visible")
		if(tools.is_defined(time)) sleep = time;
		await tools.sleep(sleep)
		this.container.classList.remove("visible")
		this.BUSY = 0
	}
}

let toaster = new Toaster()



function r_u_sure({y=null_func, n=null, head="Head", body="Body", y_msg="Yes",n_msg ="No"}={}) {
	popup_msg.close()
	var box = createElement("div")
	var msggg = createElement("p")
	msggg.innerHTML = body //"This can't be undone!!!"
	box.appendChild(msggg)
	var y_btn = createElement("div")
	y_btn.innerText = y_msg//"Continue"
	y_btn.className = "pagination center"
	y_btn.onclick = y/*function() {
		that.menu_click('del-p', file);
	};*/
	var n_btn = createElement("div")
	n_btn.innerText = n_msg//"Cancel"
	n_btn.className = "pagination center"
	n_btn.onclick = () => {return (n==null) ? popup_msg.close() : n()};
	box.appendChild(y_btn)
	box.appendChild(line_break())
	box.appendChild(n_btn)
	popup_msg.createPopup(head, box) //"Are you sure?"
	popup_msg.open_popup()
}



</script>

"""



#####################################################

#####################################################


config.file_list["html_script.html"] = r"""

<script>

const r_li = ${PY_LINK_LIST};
const f_li = ${PY_FILE_LIST};
const s_li = ${PY_FILE_SIZE};




class ContextMenu {
	constructor() {
		this.old_name = null;
	}
	async on_result(self) {
		var data = false;
		if (self.status == 200) {
			data = JSON.parse(self.responseText);
		}
		popup_msg.close()
		await tools.sleep(300)
		if (data) {
			popup_msg.createPopup(data["head"], data["body"]);
			if (data["script"]) {
				var script = document.createElement("script");
				script.innerHTML = data["script"];
				document.body.appendChild(script);
			}
		} else {
			popup_msg.createPopup("Failed", "Server didn't respond<br>response: " + self.status);
		}
		popup_msg.open_popup()
	}
	menu_click(action, link, more_data = null) {
		var that = this
		popup_msg.close()

		var url = ".?"+action;
		var xhr = new XMLHttpRequest();
		xhr.open("POST", url);
		xhr.onreadystatechange = function() {
			if (this.readyState === 4) {
				that.on_result(this)
			}
		};
		var formData = new FormData();
		formData.append("post-type", action);
		formData.append("post-uid", 123456); // TODO: add uid
		formData.append("name", link);
		formData.append("data", more_data)
		xhr.send(formData);
	}
	rename_data() {
		var new_name = byId("rename").value;

		this.menu_click("rename", this.old_name, new_name)
		// popup_msg.createPopup("Done!", "New name: "+new_name)
		// popup_msg.open_popup()
	}
	rename(link, name) {
		popup_msg.close()
		popup_msg.createPopup("Rename",
			"Enter new name: <input id='rename' type='text'><br><br><div class='pagination center' onclick='context_menu.rename_data()'>Change!</div>"
			);
		popup_msg.open_popup()
		this.old_name = link;
		byId("rename").value = name;
		byId("rename").focus()
	}
	show_menus(file, name, type) {
		var that = this;
		var menu = createElement("div")

		var new_tab = createElement("div")
			new_tab.innerText = "↗️" + " New tab"
			new_tab.classList.add("menu_options")
			new_tab.onclick = function() {
				window.open(file, '_blank');
				popup_msg.close()
			}
			menu.appendChild(new_tab)
		if (type != "folder") {
			var download = createElement("div")
			download.innerText = "📥" + " Download"
			download.classList.add("menu_options")
			download.onclick = function() {
				tools.download(file, name);
				popup_msg.close()
			}
			menu.appendChild(download)
			var copy_url = ""
		}
		if (type == "folder") {
			var dl_zip = createElement("div")
			dl_zip.innerText = "📦" + " Download as Zip"
			dl_zip.classList.add("menu_options")
			dl_zip.onclick = function() {
				popup_msg.close()
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			}
			menu.appendChild(dl_zip)
		}

		var copy = createElement("div")
		copy.innerText = "📋" + " Copy link"
		copy.classList.add("menu_options")
		copy.onclick = async function(ev) {
			popup_msg.close()

			let success = await tools.copy_2(ev, tools.full_path(file))
			if(success){
				toaster.toast("Link Copied!")
			}else{
				toaster.toast("Failed to copy!")
			}
		}
		menu.appendChild(copy)

		var rename = createElement("div")
		rename.innerText = "✏️" + " Rename"
		rename.classList.add("menu_options")
		rename.onclick = function() {
			that.rename(file, name)
		}
		menu.appendChild(rename)
		var del = createElement("div")
		del.innerText = "🗑️" + " Delete"
		del.classList.add("menu_options")
		var xxx = 'F'
		if (type == "folder") {
			xxx = 'D'
		}
		del.onclick = function() {
			that.menu_click('del-f', file);
		};
		log(file, type)
		menu.appendChild(del)
		var del_P = createElement("div")
		del_P.innerText = "🔥" + " Delete permanently"
		del_P.classList.add("menu_options")


		del_P.onclick = () => {
			r_u_sure({y:()=>{
				that.menu_click('del-p', file);
			}, head:"Are you sure?", body:"This can't be undone!!!", y_msg:"Continue", n_msg:"Cancel"})
		}
		menu.appendChild(del_P)
		var property = createElement("div")
		property.innerText = "📅" + " Properties"
		property.classList.add("menu_options")
		property.onclick = function() {
			that.menu_click('info', file);
		};
		menu.appendChild(property)
		popup_msg.createPopup("Menu", menu)
		popup_msg.open_popup()
	}
	create_folder() {
		let folder_name = byId('folder-name').value;
		this.menu_click('new_folder', folder_name)
	}
}
var context_menu = new ContextMenu()
//context_menu.show_menus("next", "video")
function Show_folder_maker() {
	popup_msg.createPopup("Create Folder",
		"Enter folder name: <input id='folder-name' type='text'><br><br><div class='pagination center' onclick='context_menu.create_folder()'>Create</div>"
		);
	popup_msg.togglePopup();
}

function show_response(url, add_reload_btn = true) {
	var xhr = new XMLHttpRequest();
	xhr.onreadystatechange = function() {
		if (xhr.readyState == XMLHttpRequest.DONE) {
			let msg = xhr.responseText;
			if (add_reload_btn) {
				msg = msg + "<br><br><div class='pagination' onclick='window.location.reload()'>Refresh🔄️</div>";
			}
			popup_msg.close()
			popup_msg.createPopup("Result", msg);
			popup_msg.open_popup();
		}
	}
	xhr.open('GET', url, true);
	xhr.send(null);
}

function reload() {
	show_response("/?reload");
}

function run_recyle(url) {
	return function() {
		show_response(url);
	}
}

function insertAfter(newNode, existingNode) {
	existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
}





tools.del_child("linkss");
const folder_li = createElement('div');
const file_li = createElement("div")
for (let i = 0; i < r_li.length; i++) {
	// time to customize the links according to their formats
	var folder = false
	let type = null;
	let r = r_li[i];
	let r_ = r.slice(1);
	let name = f_li[i];

	let item = createElement('div');
	item.classList.add("dir_item")


	let link = createElement('a');// both icon and title, display:flex
	link.href = r_;
	link.title = name;

	link.classList.add('all_link');
	link.classList.add("disable_selection")
	let l_icon = createElement("span")
	// this will go inside "link" 1st
	l_icon.classList.add("link_icon")

	let l_box = createElement("span")
	// this will go inside "link" 2nd
	l_box.classList.add("link_name")


	if (r.startsWith('d')) {
		// add DOWNLOAD FOLDER OPTION in it
		// TODO: add download folder option by zipping it
		// currently only shows folder size and its contents
		type = "folder"
		folder = true
		l_icon.innerHTML = "📂".toHtmlEntities();
		l_box.classList.add('link');
	}
	if (r.startsWith('v')) {
		// if its a video, add play button at the end
		// that will redirect to the video player
		// clicking main link will download the video instead
		type = 'video';
		l_icon.innerHTML = '🎥'.toHtmlEntities();
		link.href = go_link("vid", r_)
		l_box.classList.add('vid');
	}
	if (r.startsWith('i')) {
		type = 'image'
		l_icon.innerHTML = '🌉'.toHtmlEntities();
		l_box.classList.add('file');
	}
	if (r.startsWith('f')) {
		type = 'file'
		l_icon.innerHTML = '📄'.toHtmlEntities();
		l_box.classList.add('file');
	}
	if (r.startsWith('h')) {
		type = 'html'
		l_icon.innerHTML = '🔗'.toHtmlEntities();
		l_box.classList.add('html');
	}

	link.appendChild(l_icon)

	l_box.innerText = " " + name;

	if(s_li[i]){
		l_box.appendChild(createElement("br"))

		let s = createElement("span")
		s.className= "link_size"
		s.innerText = s_li[i]
		l_box.appendChild(s)
	}
	link.appendChild(l_box)


	link.oncontextmenu = function(ev) {
		ev.preventDefault()
		log(r_, 1);
		context_menu.show_menus(r_, name, type);
		return false;
	}

	item.appendChild(link);
	//item.appendChild(context);
	// recycling option for the files and folder
	// files and folders are handled differently
	var xxx = "F"
	if (r.startsWith('d')) {
		xxx = "D";
	}


	var hrr = createElement("hr")
	item.appendChild(hrr);
	if (folder) {
		folder_li.appendChild(item);
	} else {
		file_li.appendChild(item)
	}
}
var dir_container = byId("js-content_list")
dir_container.appendChild(folder_li)
dir_container.appendChild(file_li)



</script>





<a href="./?admin" class='pagination'>Admin center</a>


<p>pyroBox UI v4 - I ❤️ emoji!</p>

</body>

</html>
"""




#######################################################

#######################################################


config.file_list['html_vid.html'] = r"""
<!-- using from http://plyr.io  -->
<link rel="stylesheet" href="https://raw.githack.com/RaSan147/py_httpserver_Ult/main/assets/video.css" />

<p><b>Watching:</b> ${PY_FILE_NAME}</p>

<h2>${PY_UNSUPPORT_WARNING}</h2>

<div id="container">
	<video controls crossorigin playsinline data-poster="https://i.ibb.co/dLq2FDv/jQZ5DoV.jpg" id="player">

		<source src="${PY_VID_SOURCE}" type="${PY_CTYPE}" />
	</video>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plyr/3.7.0/plyr.min.js" crossorigin="anonymous" onerror="document.getElementById('player').style.maxWidth = '98vw'"></script>





<!--
<link rel="stylesheet" href="/@assets/video.css" />
<script src="/@assets/plyr.min.js"></script>
<script src="/@assets/player.js"></script>


-->

<script>





//const player = new Plyr('#player');
var controls = [
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
var player = new Plyr('#player', {
	controls
});
player.eventListeners.forEach(function(eventListener) {
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
poster.onclick = function(e) {
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
	var change=10;
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
		if(change==10){
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
		if (player.currentTime > (player.duration-10)) {
			change = player.duration - player.currentTime;
		}
		skip_ol.style.opacity = "0.9";
		last_click = "R"
		player.forward(change)
		if(change==10){
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


</script>

<br>
<br>
<a href="${PY_VID_SOURCE}"  download class='pagination'>Download</a>

<hr>
<p>pyroBox UI v4 - I ❤️ emoji!</p>


</body>
</html>
"""




#######################################################

#######################################################

config.file_list["html_zip_page.html"] = r"""
<h2>ZIPPING FOLDER</h2>
<h3 id="zip-prog">Progress</h3>
<h3 id="zip-perc"></h3>

<script>


const id = "${PY_ZIP_ID}";
const filename = "${PY_ZIP_NAME}";
var dl_now = false
var check_prog = true
var message = document.getElementById("zip-prog")
var percentage = document.getElementById("zip-perc")

function ping(url) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (dl_now) {
			return
		}
		if (this.readyState == 4 && this.status == 200) {
			// Typical action to be performed when the document is ready:
			//document.getElementById("demo").innerHTML = xhttp.responseText;
			// json of the response
			var resp = JSON.parse(xhttp.response);

			if (resp.status=="SUCCESS"){
				check_prog = true;
			} else if (resp.status=="DONE"){
				message.innerHTML = "Downloading";
				percentage.innerText = "";
				dl_now = true;
				clearTimeout(prog_timer)
				run_dl()
			} else if (resp.status=="ERROR"){
				message.innerHTML = "Error";
				percentage.innerText = resp.message;
				clearTimeout(prog_timer)
			} else if (resp.status=="PROGRESS"){
				percentage.innerText = resp.message + "%";
			} else {
				percentage.innerText = resp.status + ": " + resp.message;
				clearTimeout(prog_timer)
			}
		}
	};
	xhttp.open("GET", url, true);
	xhttp.send();
}

function run_dl() {
	tools.download(window.location.pathname + "?zip&zid=" + id + "&download", filename, new_tab = true)
}
var prog_timer = setInterval(function() {
	ping(window.location.pathname + "?zip&zid=" + id + "&progress")}, 500)


</script>


<p>pyroBox UI v4 - I ❤️ emoji!</p>
"""



#####################################################

#####################################################

config.file_list["html_admin.html"] = r"""


<h1 style="text-align: center;">Admin Page</h1>
<hr>




<!-- check if update available -->

<div>
	<p class="update_text" id="update_text">Checking for Update...</p>
	<div class="pagination jsonly" onclick="run_update()" id="run_update" style="display: none;">Run Update</div>
	<br><br>
</div>



<div class='pagination jsonly' onclick="request_reload()">RELOAD SERVER 🧹</div>
<noscript><a href="/?reload" class='pagination'>RELOAD SERVER 🧹</a><br></noscript>
<hr>

<div class='pagination jsonly' onclick="request_shutdown()">Shut down 🔻</div>

<script>


function request_reload() {
	fetch('/?reload');
}



async function check_update() {
	fetch('/?update')
	.then(response => {
		console.log(response);
		return response.json()
	}).then(data => {
		if (data.update_available) {
			byId("update_text").innerText = "Update Available! 🎉 Latest Version: " + data.latest_version ;
			byId("update_text").style.backgroundColor = "#00cc0033";

			byId("run_update").style.display = "block";
		} else {
			byId("update_text").innerText = "No Update Available";
			byId("update_text").style.backgroundColor = "#bbb";
		}
	})
	.catch(async err => {
		await tools.sleep(0);
		byId("update_text").innerText = "Update Error: " + "Invalid Response";
		byId("update_text").style.backgroundColor = "#CC000033";
	});
}

function run_update() {
	byId("update_text").innerText = "Updating...";
	fetch('/?update_now')
	.then(response => response.json())
	.then(data => {
		if (data.status) {
			byId("update_text").innerHTML = data.message;
			byId("update_text").style.backgroundColor = "green";

		} else {
			byId("update_text").innerHTML = data.message;
			byId("update_text").style.backgroundColor = "#bbb";
		}
	})
	.catch(err => {
		byId("update_text").innerText = "Update Error: " + "Invalid Response";
		byId("update_text").style.backgroundColor = "#CC000033";
	})


	byId("run_update").style.display = "none";
}

check_update();
</script>


<p>pyroBox UI v4 - I ❤️ emoji!</p>
"""


#####################################################

#####################################################

config.file_list["html_upload.html"] = r"""
<noscript>

	<form ENCTYPE="multipart/form-data" method="post" action="?upload">
		<!-- using "?upload" action so that user can go back to the page -->
		<center>
			<h1><u>Upload file</u></h1>


			<input type="hidden" name="post-type" value="upload">
			<input type="hidden" name="post-uid" value="12345">

			<span class="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="text"
				label="Password" class="upload-pass-box">
			<br><br>
			<!-- <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" multiple /><br><br> -->
			<div class="upload-box">
				<div class="drag-area">
					<div class="drag-icon">⬆️</div>
					<header>Select Files To Upload</header>
					<input type="file" name="file" multiple class="drag-browse" value="Browse File">
				</div>
			</div>

		</center>
		<center><input id="submit-btn" type="submit" value="&#10174; upload"></center>
	</form>
</noscript>


<form ENCTYPE="multipart/form-data" method="post" id="uploader" class="jsonly" action="?upload">


	<center>
		<h1><u>Upload file</u></h1>


		<input type="hidden" name="post-type" value="upload">
		<input type="hidden" name="post-uid" value="12345">

		<span class="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="text" label="Password"
			class="upload-pass-box">
		<br><br>
		<!-- <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" multiple /><br><br> -->
		<div class="upload-box">
			<div id="drag-area" class="drag-area">
				<div class="drag-icon">⬆️</div>
				<header>Drag & Drop to Upload File</header>
				<span>OR</span>
				<button class="drag-browse">Browse File</button>
				<input type="file" name="file" multiple hidden>
			</div>
		</div>


		<h2 id="has-selected-up" style="display:none">Selected Files</h2>
	</center>
	<div id="drag-file-list">
		<!--// List of file-->
	</div>

	<center><input id="submit-btn" type="submit" value="&#10174; upload"></center>
</form>



<br>
<center>
	<div id="upload-task" style="display:none;font-size:20px;font-weight:700">
		<p id="upload-status"></p>
		<progress id="upload-progress" value="0" max="100" style="width:300px"> </progress>
	</div>
</center>
<hr>


<script>
	//selecting all required elements
	const uploader = byId("uploader"),
	uploader_dropArea = document.querySelector("#drag-area"),
	uploader_dragText = uploader_dropArea.querySelector("header"),
	uploader_button = uploader_dropArea.querySelector("button"),
	uploader_input = uploader_dropArea.querySelector("input");
	let uploader_files; //this is a global variable and we'll use it inside multiple functions
	let selected_files = new DataTransfer(); //this is a global variable and we'll use it inside multiple functions
	uploader_file_display = byId("drag-file-list");
	
	function uploader_exist(file) {
		//check if file is already selected or not
		for (let i = 0; i < selected_files.files.length; i++) {
			if (selected_files.files[i].name == file.name) {
				return i+1; // 0 is false, so we add 1 to make it true
			}
		}
		return false;
	}
	
	function addFiles(files) {
		var exist = false;
		for (let i = 0; i < files.length; i++) {
			exist = uploader_exist(files[i])
	
			if (exist) { //if file already selected, remove that and replace with new one, because, when uploading last file will remain in host server, so we need to replace it with new one
				selected_files.items.remove(exist-1);
			}
			selected_files.items.add(files[i]);
		}
		log("selected "+ selected_files.items.length+ " files");
		uploader_showFiles();
	}
	
	
	uploader_button.onclick = (e)=>{
		e.preventDefault();
		uploader_input.click(); //if user click on the button then the input also clicked
	}
	
	uploader_input.onchange = (e)=>{
		// USING THE BROWSE BUTTON
		let f = e.target.files; // this.files = [file1, file2,...];
		addFiles(f);
		// uploader_dropArea.classList.add("active");
		// uploader_showFiles(); //calling function
		// uploader_dragText.textContent = "Release to Upload File";
	};
	
	
	//If user Drag File Over DropArea
	uploader_dropArea.ondragover = (event)=>{
		event.preventDefault(); //preventing from default behaviour
		uploader_dropArea.classList.add("active");
		uploader_dragText.textContent = "Release to Upload File";
	};
	
	//If user leave dragged File from DropArea
	uploader_dropArea.ondragleave = ()=>{
		uploader_dropArea.classList.remove("active");
		uploader_dragText.textContent = "Drag & Drop to Upload File";
	};
	
	//If user drop File on DropArea
	uploader_dropArea.ondrop = (event)=>{
		event.preventDefault(); //preventing from default behaviour
		//getting user select file and [0] this means if user select multiple files then we'll select only the first one
		addFiles(event.dataTransfer.files);
		// uploader_showFiles(); //calling function
	};
	
	function uploader_removeFileFromFileList(index) {
		let dt = new DataTransfer()
		// const input = byId('files')
		// const { files } = input
	
		for (let i = 0; i < selected_files.files.length; i++) {
			let file = selected_files.files[i]
			if (index !== i)
				dt.items.add(file) // here you exclude the file. thus removing it.
		}
	
		selected_files = dt
		// uploader_input.files = dt // Assign the updates list
		uploader_showFiles()
	}
	
	function uploader_showFiles() {
		tools.del_child(uploader_file_display)
		let uploader_heading = byId("has-selected-up")
		if(selected_files.files.length){
			uploader_heading.style.display = "block"
		} else {
			uploader_heading.style.display = "none"
		}
		for (let i = 0; i <selected_files.files.length; i++) {
			uploader_showFile(selected_files.files[i], i);
		}
	}
	
	function fmbytes(B) {
		'Return the given bytes as a file manager friendly KB, MB, GB, or TB string'
		const KB = 1024,
		MB = (KB ** 2),
		GB = (KB ** 3),
		TB = (KB ** 4)
	
		var unit="byte", val=B;
	
		if (B>1){
			unit="bytes"
			val = B}
		if (B/KB>1){
			val = (B/KB)
			unit="KB"}
		if (B/MB>1){
			val = (B/MB)
			unit="MB"}
		if (B/GB>1){
			val = (B/GB)
			unit="GB"}
		if (B/TB>1){
			val = (B/TB)
			unit="TB"}
	
		val = val.toFixed(2)
	
		return `${val} ${unit}`
	}
	
	function uploader_showFile(file, index){
		let filename = file.name;
		let size = fmbytes(file.size);
	
		let item = createElement("div");
		item.className = "upload-file-item";
	
		item.innerHTML = `
				<span class="file-name">${filename}</span>
				<span class="file-size">${size}</span>
			<span class="file-remove" onclick="uploader_removeFileFromFileList(${index})">&times;</span>
		`;
	
		uploader_file_display.appendChild(item);
	
	}
	
	
	byId("uploader").onsubmit = (e) => {
		e.preventDefault()
	
		uploader_input.files = selected_files.files // Assign the updates list
	
	
		const formData = new FormData(e.target)
	
	
		const status = byId("upload-status")
		const progress = byId("upload-progress")
	
		var prog = 0;
		var msg = "";
	
		// const filenames = formData.getAll('files').map(v => v.name).join(', ')
		const request = new XMLHttpRequest()
		request.open(e.target.method, e.target.action)
		request.timeout = 3600000;
		request.onreadystatechange = () => {
			if (request.readyState === XMLHttpRequest.DONE) {
				msg = `${request.status}: ${request.statusText}`
				if (request.status === 401) msg = 'Incorrect password'
				else if (request.status == 503) msg = 'Upload is disabled'
				else if (request.status === 0) msg = 'Connection failed (Possible cause: Incorrect password or Upload disabled)'
				else if (request.status === 204 || request.status === 200) msg = 'Success'
				status.innerText = msg
			}
		}
		request.upload.onprogress = e => {
			prog = Math.floor(100*e.loaded/e.total)
			if(e.loaded === e.total){
				msg ='Saving...'
			}else{
				msg = `Uploading : ${prog}%`
			}
			status.innerText = msg
			progress.value = prog
	
		}
		status.innerText = `Uploading : 0%`
		byId('upload-task').style.display = 'block'
		request.send(formData)
	}


	

</script>
"""



#####################################################

#####################################################

config.file_list["html_file_list.html"] = r"""

<hr>


<div class='pagination' onclick="Show_folder_maker()">Create Folder</div><br>

<br>
<hr><br>
"""



#####################################################

#####################################################

config.file_list["html_error.html"] = r"""

<h1><u>Error response</u></h1>
<p><u>Error code:</u> ${code}</p>
<p><u>Message:</u> ${message}</p>
<p><u>Error code explanation:</u> ${code} - ${explain}</p>
<hr>
<h3><u>PyroBox Version:</u> ${version}</h3>
<br>
<center><img src = "https://http.cat/${code}"></img></center>
"""
