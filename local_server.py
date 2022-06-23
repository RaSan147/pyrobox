#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from platform import system as platform_system
import os
import shutil
class Config:
	def __init__(self):
		# DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ftp_dir = "." # DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ANDROID_ftp_dir= "/storage/emulated/0/"
		self.LINUX_ftp_dir = "~/"
		self.WIN_ftp_dir= 'G:\\'
		# DEFAULT PORT TO LAUNCH SERVER
		self.IP = None # will be assigned by checking
		self.port= 6969
		# UPLOAD PASSWORD SO THAT ANYONE RANDOM CAN'T UPLOAD
		self.PASSWORD= "SECret".encode('utf-8')
		self.log_location = "G:/py-server/"  # fallback log_location = "./"
		self.allow_web_log = True # if you want to see some important LOG in browser, may contain your important information
		self.default_zip = "7z" # or "zipfile" to use python built in zip module

		self.MAIN_FILE = os.path.realpath(__file__)
		self.MAIN_FILE_dir = os.path.dirname(self.MAIN_FILE)
		print(self.MAIN_FILE)


		self._7z_parent_dir = self.MAIN_FILE_dir # this is where the 7z/7z.exe is located. if you don't want to keep 7z in the same directory, you can change it here
		self._7z_location = '/7z/7za.exe'  # location of 7za.exe # https://www.7-zip.org/a/7z2107-extra.7z

		self.ftp_dir = self.get_default_dir()

	def _7z_command(self, commands = []):
		if self.get_os()=='Windows':
			return [self._7z_parent_dir + self._7z_location,] + commands
		elif self.get_os()=='Linux':
			return ['7z',] + commands
		else:
			print(tools.text_box("7z NOT IMPLANTED YET"))
			raise NotImplementedError

	def get_os(self):
		out = platform_system()
		if out=="Linux":
			if 'ANDROID_STORAGE' in os.environ:
				#self.IP = "192.168.43.1"
				return 'Android'

		return out

	def get_default_dir(self):
		OS = self.get_os()
		if OS=='Windows':
			return self.WIN_ftp_dir
		elif OS=='Linux':
			return self.LINUX_ftp_dir
		elif OS=='Android':
			return self.ANDROID_ftp_dir
		else:
			return './'

	def linux_installer(self):
		# detect if apt or yum is installed
		if shutil.which('pkg'):
			return 'pkg'
		elif shutil.which('apt'):
			return 'apt'
		elif shutil.which('apt-get'):
			return 'apt-get'
		elif shutil.which('yum'):
			return 'yum'
		else:
			return None
			
	def address(self):
		return "%s:%i"%(self.IP, self.port)




class Tools:
	def __init__(self):
		self.styles = {
			"equal" : "=",
			"star"    : "*",
			"hash"  : "#",
			"dash"  : "-",
			"udash": "_"
		}

	def text_box(self, text, style = "equal"):
		term_col = shutil.get_terminal_size()[0]

		s = self.styles[style] if style in self.styles else style
		return (f"\n\n{s*term_col}\n{str(text).center(term_col)}\n{'='*term_col}\n\n")

tools = Tools()
config = Config()

# FEATURES
# ----------------------------------------------------------------
# * PAUSE AND RESUME
# * UPLOAD WITH PASSWORD
# * FOLDER DOWNLOAD (uses temp folder)
# * VIDEO PLAYER
# * DELETE FILE FROM REMOTEp (RECYCLE BIN) # PERMANENTLY DELETE IS VULNERABLE
# * File manager like NAVIGATION BAR
# * RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]
# * MULTIPLE FILE UPLOAD
# * FOLDER CREATION
# * Pop-up messages (from my Web leach repo)


#TODO:
# RIGHT CLICK CONTEXT MENU


# INSTALL REQUIRED PACKAGES
REQUEIREMENTS= ['send2trash',]


import subprocess
import sys
import tempfile, random, string, json


import traceback
import platform

import pkg_resources as pkg_r, importlib


def get_installed():
	importlib.reload(pkg_r)
	return [pkg.key for pkg in pkg_r.working_set]




def init_requirements():
	missing = []

	missing_dict = {
		'pip': 'python3-pip',
		"7z": "p7zip-full"
	}
	if 'pip' not in get_installed():
		missing.append('pip')

	def has_7z():
		try:
			subprocess.check_output(config._7z_command(['-h']))
			return True
		except:
			return False

	if config.get_os()!="Android" and not has_7z():
		missing.append('7z')

	if missing:
		print(tools.text_box("Missing required packages: " + ', '.join(missing)))
		if config.get_os()=='Linux':
			print("***SUDO MAY REQUIRE***")

		promt = config.linux_installer() if config.get_os()=='Linux' else True
			 
		if promt:
			promt = input("Do you want to install them? (y/n) ")

		if promt=='y':
			if config.get_os()=='Linux':
				MISSING = [missing_dict[i] for i in missing]
				subprocess.call(['sudo', config.linux_installer(), 'install', '-y'] + MISSING)

			if config.get_os()=='Windows':
				if 'pip' in missing:
					subprocess.call(sys.executable, '-m', 'ensurepip')
					if "pip" in get_installed():
						missing.remove("pip")

				if '7z' in missing:

					import urllib.request
					import zipfile
					print("Downloading 7za.zip")

					# Download the 7za.zip file and put it in the :
					with urllib.request.urlopen("https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/7z.zip") as response, open(config._7z_parent_dir+ "/7z.zip", 'wb') as out_file:
						shutil.copyfileobj(response, out_file)

					if not os.path.isdir(config._7z_parent_dir):
						os.makedirs(config._7z_parent_dir)

					with zipfile.ZipFile(config._7z_parent_dir + '/7z.zip', 'r') as zip_ref:
						zip_ref.extractall(config._7z_parent_dir)
					try: os.remove(config._7z_parent_dir + '/7z.zip')
					except: pass

					if has_7z():
						missing.remove("7z")
						print("7za.zip downloaded")
					else:
						print("7za.zip failed to download")


		else:
			print("Please install missing packages to use FULL FUNCTIONALITY")

	return missing


missing_sys_req = init_requirements()
disabled_func = {
	"trash": False,
	"7z":     False
}
if "pip" in missing_sys_req:
	print("'Trash/Recycle bin' disabled")
	disabled_func["trash"] = True

if "7z" in missing_sys_req:
	print("'Download folder as Zip' disabled")
	disabled_func["7z"] = True


reload = False


if "pip" not in missing_sys_req:
	for i in REQUEIREMENTS:
		if i not in get_installed():

			# print(i)

			subprocess.call([sys.executable, "-m", "pip", "install", '--disable-pip-version-check', '--quiet', i])
			REQUEIREMENTS.remove(i)

	if not REQUEIREMENTS:
		print("Reloading...")
		reload = True


if config.get_os() == "Android":
	disabled_func["7z"] = True #7z is not supported. will add termux support later


zip_temp_dir = tempfile.gettempdir() + '/zip_temp/'
zip_ids = dict()
zip_in_progress = []

shutil.rmtree(zip_temp_dir, ignore_errors=True)
try:
	os.mkdir(path=zip_temp_dir)
except FileExistsError:
	pass
if not os.path.isdir(config.log_location):
	try:
		os.mkdir(path=config.log_location)
	except:
		config.log_location ="./"




if not disabled_func["trash"]:
	from send2trash import send2trash, TrashPermissionError


directory_explorer_header = '''

<!DOCTYPE HTML>
<!-- test1 -->
<html>
<meta http-equiv="Content-Type" content="text/html; charset=%s">
<meta name="viewport" content="width=device-width, initial-scale=1">


<title>%s</title>

<script>
function request_reload()
{
    fetch('/?reload?');
}

const public_url = "%s";

</script>




<style type="text/css">
body{
  position: relative;
  min-height: 100vh;
}

html, body, input, textarea, select, button {
    border-color: #736b5e;
    color: #e8e6e3;
    background-color: #181a1b;
}
* {
    scrollbar-color: #0f0f0f #454a4d;
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



a{
  line-height: 200%%;
  font-size: 20px;
  font-weight: 600;
  font-family: 'Gill Sans, Gill Sans MT, Calibri, Trebuchet MS, sans-serif';
  text-decoration: none;
  color: #00BFFF;
}

.all_link{
word-wrap: break-word;
}

.link{
  color: #1589FF;
  /* background-color: #1589FF; */
}

.vid{
  color: #8A2BE2;
  font-weight: 300;
}

.file{
  font-weight: 300;
  color: #c07cf7;
  font-weight: 400;
}


#footer {
  position: absolute;
  bottom: 0;
  width: 100%%;
  height: 2.5rem;			/* Footer height */
}


.overflowHidden {
	overflow: hidden !important
}


/* POPUP CSS */

.modal_bg{
  display: inherit;
  position: fixed;
  z-index: 1;
  padding-top: inherit;
  left: 0;
  top: 0;
  width: 100%%;
  height: 100%%;
  overflow: auto;
}


.popup {
	position: fixed;
	z-index: 22;
	left: 50%%;
	top: 50%%;
	width: 100%%;
	height: 100%%;
	overflow: none;
	transition: all .5s ease-in-out;
	transform: translate(-50%%, -50%%) scale(1)
}

.popup-box {
	display: block;
	/*display: inline;*/
	/*text-align: center;*/
	position: fixed;
	top: 50%%;
	left: 50%%;
	color: #BBB;
	transition: all 400ms ease-in-out;
	background: #222;
	width: 95%%;
	max-width: 500px;
	z-index: 23;
	padding: 20px;
	box-sizing: border-box;
	font-family: "Open Sans", sans-serif;
	max-height: min(600px, 80%%);
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
	border-radius: 50%%
}

.popup:not(.active) {
	transform: translate(-50%%, -50%%) scale(0);
	opacity: 0;
}


.popup.active .popup-box {
	transform: translate(-50%%, -50%%) scale(1);
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
    background-color:  #4e4f506b;
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
	width: 95%%;
	padding: 5px;
	margin: 5px;
	text-align: left;
	cursor: pointer;
}

.menu_options:hover, .menu_options:focus {
	background: #337;
}


</style>

<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.png?raw=true" type="image/png">


</head>
<body>




<div id="popup-container">



<h1 style="word-wrap: break-word;">%s</h1>
<hr>


<hr>
<ul id= "linkss">
<a href="../" style="background-color: #000;padding: 3px 20px 8px 20px;border-radius: 4px;">&#128281; {Prev folder}</a>

</ul>
<hr>


'''

_js_script = """

<div class='pagination' onclick = "request_reload()">reload</div><br>

<div class='pagination' onclick = "Show_folder_maker()">Create Folder</div><br>

<br><hr><br><h2>Upload file</h2>
        <form ENCTYPE="multipart/form-data" method="post">
        <input type="hidden" name="post-type" value="upload">
        <input type="hidden" name="post-uid" value="12345">

  <p>PassWord:&nbsp;&nbsp;</p><input name="password" type="text" label="Password"><br>
  <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" multiple/><br><br>

  <input type="submit" value="&#10174; upload" style="background-color: #555; height: 30px; width: 100px"></form>

<hr>

<script>


const r_li = %s;
const f_li = %s;




const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);

String.prototype.toHtmlEntities = function() {
  return this.replace(/./ugm, s => s.match(/[a-z0-9\s]+/i) ? s : "&#" + s.codePointAt(0) + ";");
};

function null_func(){
	return true
}
function toggle_scroll() {
    document.body.classList.toggle('overflowHidden');
}

function go_link(typee, locate){
  // function to generate link for different types of actions
  return typee+"%%3F"+locate;}

// getting all the links in the directory


class Tools {
	// various tools for the page
	sleep(ms) {
		// sleeps for a given time in milliseconds
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	set_brightness(n = 0) {
		// sets the brightness of the screen

		var val;
		var input_ = byId('brightness-input');
		var brightness = byId('brightness');
		if (n == 0) {
			val = sessionStorage.getItem('bright');
			if (val) {
				val = parseInt(val);
				input_.value = val;
			} else {
				n = 1;
			}
		}
		if (n == 1) {
			val = input_.value;
			//   int to string
			sessionStorage.setItem('bright', val);
		}

		// to make sure opacity is not -1.11022e-16
		if (val == 10) {brightness.style.opacity = 0;return;}


		brightness.style.opacity = 0.7 - (val * 0.07);
	}


	onlyInt(str){
	if(this.is_defined(str.replace)){
	return parseInt(str.replace(/\D+/g, ""))}
	return 0;
	}

	del_child(elm){
		if(typeof(elm)=="string"){
			elm = byId(elm)
		}

		while (elm.firstChild) {
			elm.removeChild(elm.lastChild);
		}
	}
	toggle_bool(bool){
		return bool !== true;
	}

	exists(name){
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

	enable_debug(){
		if(!config.allow_Debugging){
			alert("Debugging is not allowed");
			return;
		}
		if(config.Debugging){
			return
		}
		config.Debugging = true;
		var script = createElement('script'); script.src="//cdn.jsdelivr.net/npm/eruda"; document.body.appendChild(script); script.onload = function () { eruda.init() };
	}


	is_in(item, array) {
		return array.indexOf(item) > -1;
	}

	is_defined(obj){
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
	
	download(dataurl, filename=null) {
  const link = document.createElement("a");
  link.href = dataurl;
  link.download = filename;
  link.click();
}

}

let tools = new Tools();




class Config {
	constructor(){
		this.total_popup =0;
		this.popup_msg_open = false
	}
}

var config = new Config()


class Popup_Msg {
	constructor() {
		this.create()
		this.made_popup = false;

		this.init()

	}

	init(){
		this.onclose = null_func;
		this.scroll_disabled = false;
	}


	create() {
		var that = this;
		this.popup_id = config.total_popup;
		this.popup_obj = createElement("div")
		this.popup_obj.id = "popup-" + this.popup_id;
		this.popup_obj.classList.add("popup")

		this.popup_bg = createElement("div")
		this.popup_bg.classList.add("modal_bg")
		this.popup_bg.id = "popup-bg-" + this.popup_id;
		this.popup_bg.style.backgroundColor = "#000000EE";
		this.popup_bg.onclick = function(){
			that.close()
		}
		this.popup_obj.appendChild(this.popup_bg);

		var popup_box = createElement("div");
		popup_box.classList.add("popup-box")
		var close_btn = createElement("div");
		close_btn.classList.add("popup-close-btn")
		close_btn.onclick = function(){
			that.close()
		}
		close_btn.innerHTML = "&times;";
		popup_box.appendChild(close_btn)

		this.header = createElement("h1")
		this.header.id = "popup-header-" + this.popup_id;
		popup_box.appendChild(this.header)

		this.hr = createElement("popup-hr-" + this.popup_id);
		this.hr.style.width = "95%%"
		popup_box.appendChild(this.hr)

		this.content = createElement("div")
		this.content.id = "popup-content-" + this.popup_id;
		popup_box.appendChild(this.content)

		this.popup_obj.appendChild(popup_box)

		byId("popup-container").appendChild(this.popup_obj)
		config.total_popup +=1;
	}

	close(){
		this.onclose()
		this.dismiss()
		config.popup_msg_open = false;
	}

	hide(){
		this.popup_obj.classList.remove("active");
		tools.toggle_scroll(1)

	}

	dismiss(){
		this.hide()
		tools.del_child(this.header);
		tools.del_child(this.content);
		this.made_popup = false;
	}

	async togglePopup(toggle_scroll = true) {
		if(!this.made_popup){return}
		this.popup_obj.classList.toggle("active");
		if(toggle_scroll){
			tools.toggle_scroll();}
		log(tools.hasClass(this.popup_obj, "active"))
		if(!tools.hasClass(this.popup_obj, "active")) {
		this.close()
		}
	}

	async open_popup(allow_scroll=false){
		if(!this.made_popup){return}
		this.popup_obj.classList.add("active");
		if(!allow_scroll){
			tools.toggle_scroll(0);
			this.scroll_disabled = true;
		}
	}

	async createPopup(header="", content="", hr = true) {
		this.init()
		this.made_popup = true;
		if (typeof header === 'string' || header instanceof String){
		this.header.innerHTML = header;}
		else if(header instanceof Element){
			this.header.appendChild(header)
		}

		if (typeof content === 'string' || content instanceof String){
		this.content.innerHTML = content;}
		else if(content instanceof Element){
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


class ContextMenu {
	constructor(){
		this.old_name = null;
	}
	async on_result(self){
		var data = false;
		if(self.status == 200){
			data =  JSON.parse(self.responseText);}

		popup_msg.close()
		await tools.sleep(300)

		if(data){
			popup_msg.createPopup(data[0], data[1]);
		}else{
			popup_msg.createPopup("Failed", "Server didn't respond<br>response: "+self.status);
		}
	popup_msg.open_popup()

	}
	menu_click(action, link, more_data=null){
		var that = this
		var url = ".";
		var xhr = new XMLHttpRequest();
		xhr.open("POST", url);

		xhr.onreadystatechange = function () {

	   if (this.readyState === 4) {
	   	that.on_result(this)
	   }};

		var formData = new FormData();
		formData.append("post-type", action);
		formData.append("post-uid", 123456);
		formData.append("name", link);
		formData.append("data", more_data)
		xhr.send(formData);

}

	rename_data(){
		var new_name= byId("rename").value;
		popup_msg.close()
		this.menu_click("rename", this.old_name, new_name)
		// popup_msg.createPopup("Done!", "New name: "+new_name)
		// popup_msg.open_popup()
	}

	rename(file){

		popup_msg.close()
		popup_msg.createPopup("Rename", "Enter new name: <input id='rename' type='text'><br><br><div class='pagination center' onclick='context_menu.rename_data()'>Change!</div>");
		popup_msg.open_popup()
		this.old_name = file;
		byId("rename").value = file;
		byId("rename").focus()
	}

	show_menus(file, name,type){

		var that = this;
		var menu = createElement("div")

		if(type =="video"){
			var download = createElement("div")
			download.innerHTML = "⬇️".toHtmlEntities() + " Download"
			download.classList.add("menu_options")
			download.onclick = function(){
				tools.download(file, name);
				popup_msg.close()
			}
			menu.appendChild(download)
			
			var copy_url = ""
		}

		if(type=="folder"){
			var dl_zip = createElement("div")
			dl_zip.innerHTML = "🗃️".toHtmlEntities() + " Download as Zip"
			dl_zip.classList.add("menu_options")
			dl_zip.onclick = function(){
				popup_msg.close()
				window.open(go_link('dl', file), '_blank');
			}
			menu.appendChild(dl_zip)
		}

		var rename = createElement("div")
		rename.innerHTML = "✏️".toHtmlEntities() + " Rename"
		rename.classList.add("menu_options")
		rename.onclick = function(){
			that.rename(file)
		}
		menu.appendChild(rename)

		var del = createElement("div")
		del.innerHTML = "🗑️".toHtmlEntities() + " Delete"
		del.classList.add("menu_options")
		var xxx = 'F'
		if(type=="folder"){
			xxx = 'D'
		}
		del.onclick = function(){
		that.menu_click('del-f', file);};
		log(file, type)
		menu.appendChild(del)

		var del_P = createElement("div")
		del_P.innerHTML = "🔥".toHtmlEntities() + " Delete permanently"
		del_P.classList.add("menu_options")
		function r_u_sure(){
			popup_msg.close()
			var box = createElement("div")
			var msggg = createElement("p")
			msggg.innerHTML = "This can't be undone!!!"
			box.appendChild(msggg)
			var y_btn = createElement("div")
			y_btn.innerHTML ="Continue"
			y_btn.className = "pagination center"
			y_btn.onclick = function(){
				that.menu_click('del-p', file);};

			var n_btn = createElement("div")
			n_btn.innerHTML= "Cancel"
			n_btn.className ="pagination center"
			n_btn.onclick = popup_msg.close;

			box.appendChild(y_btn)
			box.appendChild(n_btn)
			popup_msg.createPopup("Are you sure?", box)
			popup_msg.open_popup()
			}
		del_P.onclick= r_u_sure
		menu.appendChild(del_P)



		var property = createElement("div")
		property.innerHTML = "ℹ️".toHtmlEntities() + " Properties"
		property.classList.add("menu_options")
		property.onclick = function(){
		that.menu_click('info', file);};
		menu.appendChild(property)


		popup_msg.createPopup("Menu", menu)
		popup_msg.open_popup()
	}

	create_folder(){

    let folder_name = document.getElementById('folder-name').value;
    this.menu_click('new folder', folder_name)
	}
}

var context_menu = new ContextMenu()
//context_menu.show_menus("next", "video")


function Show_folder_maker(){
    popup_msg.createPopup("Create Folder", "Enter folder name: <input id='folder-name' type='text'><br><br><div class='pagination center' onclick='context_menu.create_folder()'>Create</div>");
    popup_msg.togglePopup();
}

function show_response(url, add_reload_btn=true){
  var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            let msg = xhr.responseText;
			if(add_reload_btn){
				msg = msg + "<br><br><div class='pagination' onclick='window.location.reload()'>Refresh🔄️</div>";
			}
			popup_msg.close()
            popup_msg.createPopup("Result", msg);
            popup_msg.open_popup();
        }
    }
    xhr.open('GET', url , true);
    xhr.send(null);
}


function reload(){
    show_response("?reload?");
}

function run_recyle(url){
    return function(){
        show_response(url);
    }
}


const linkd_li = document.getElementsByTagName('ul')[0];

for (let i = 0; i < r_li.length; i++) {
  // time to customize the links according to their formats

	let type = null;

	let ele = document.createElement('li');
	let r= r_li[i];
	let r_ = r.slice(1);
	let name = f_li[i];
	let link = document.createElement('a');
	link.href = r_;
	link.classList.add('all_link');

	if(r.startsWith('d')){
	// add DOWNLOAD FOLDER OPTION in it
	// TODO: add download folder option by zipping it
	// currently only shows folder size and its contents

	type = "folder"
	link.innerHTML = "📂".toHtmlEntities() + name;
	link.classList.add('link');

	ele.appendChild(link);

	}

	if(r.startsWith('v')){
	// if its a video, add play button at the end
	// that will redirect to the video player
	// clicking main link will download the video instead

	type = 'video';

	link.innerHTML = '🎥'.toHtmlEntities() + name;
	link.href = go_link("vid", r_)
	link.classList.add('vid');
	ele.appendChild(link);

	}


	if(r.startsWith('i')){

	type = 'image'
	link.innerHTML = '🌉'.toHtmlEntities() + name;
	link.classList.add('file');
	ele.appendChild(link);

	}

	if(r.startsWith('f')){

	type = 'file'
	link.innerHTML = '📄'.toHtmlEntities() + name;
	link.classList.add('file');
	ele.appendChild(link);

	}
	if(r.startsWith('h')){
	type = 'html'
	link.innerHTML = '🔗'.toHtmlEntities() + name;
	link.classList.add('html');
	ele.appendChild(link);

	}

	// recycling option for the files and folder
	// files and folders are handled differently
	var xxx = "F"
	if(r.startsWith('d')){
		xxx = "D";
	}

	var context = createElement('span');
	context.className = "pagination"
	context.innerHTML= '<b>&nbsp;&hellip;&nbsp;</b>';
	context.style.marginLeft= '50px';
	context.onclick = function(){log(r_, 1); context_menu.show_menus(r_, name,type);}

	ele.insertAdjacentElement("beforeend",context);

	var hrr = createElement("hr")
	ele.insertAdjacentElement("beforeend",hrr);




  linkd_li.appendChild(ele);
}


</script>

</body>
</html>
"""

# directory_explorer_body_1=



"""HTTP server classes.

Note: BaseHTTPRequestHandler doesn't implement any HTTP request; see
SimpleHTTPRequestHandler for simple implementations of GET, HEAD and POST,
and CGIHTTPRequestHandler for CGI scripts.

It does, however, optionally implement HTTP/1.1 persistent connections,
as of version 0.3.

Notes on CGIHTTPRequestHandler
------------------------------

This class implements GET and POST requests to cgi-bin scripts.

If the os.fork() function is not present (e.g. on Windows),
subprocess.Popen() is used as a fallback, with slightly altered semantics.

In all cases, the implementation is intentionally naive -- all
requests are executed synchronously.

SECURITY WARNING: DON'T USE THIS CODE UNLESS YOU ARE INSIDE A FIREWALL
-- it may execute arbitrary Python code or external programs.

Note that status code 200 is sent prior to execution of a CGI script, so
scripts cannot send other status codes such as 302 (redirect).

XXX To do:

- log requests even later (to capture byte count)
- log user-agent header and other interesting goodies
- send error log to separate file
"""


# See also:
#
# HTTP Working Group										T. Berners-Lee
# INTERNET-DRAFT											R. T. Fielding
# <draft-ietf-http-v10-spec-00.txt>					 H. Frystyk Nielsen
# Expires September 8, 1995								  March 8, 1995
#
# URL: http://www.ics.uci.edu/pub/ietf/http/draft-ietf-http-v10-spec-00.txt
#
# and
#
# Network Working Group									  R. Fielding
# Request for Comments: 2616									   et al
# Obsoletes: 2068											  June 1999
# Category: Standards Track
#
# URL: http://www.faqs.org/rfcs/rfc2616.html

# Log files
# ---------
#
# Here's a quote from the NCSA httpd docs about log file format.
#
# | The logfile format is as follows. Each line consists of:
# |
# | host rfc931 authuser [DD/Mon/YYYY:hh:mm:ss] "request" ddd bbbb
# |
# |		host: Either the DNS name or the IP number of the remote client
# |		rfc931: Any information returned by identd for this person,
# |				- otherwise.
# |		authuser: If user sent a userid for authentication, the user name,
# |				  - otherwise.
# |		DD: Day
# |		Mon: Month (calendar name)
# |		YYYY: Year
# |		hh: hour (24-hour format, the machine's timezone)
# |		mm: minutes
# |		ss: seconds
# |		request: The first line of the HTTP request as sent by the client.
# |		ddd: the status code returned by the server, - if not available.
# |		bbbb: the total number of bytes sent,
# |			  *not including the HTTP/1.0 header*, - if not available
# |
# | You can determine the name of the file accessed through request.
#
# (Actually, the latter is only true if you know the server configuration
# at the time the request was made!)

__version__ = "0.6"

__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler", "CGIHTTPRequestHandler",
]

import copy
import datetime
import email.utils
import html
import http.client
import io
import mimetypes
import posixpath
import select
import shutil
import socket # For gethostbyaddr()
import socketserver
import sys
import time
import urllib.parse
import contextlib
from functools import partial
from http import HTTPStatus

import re


def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns "2big"
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	"""
	if return_list: r=[]
	total_size = 0
	start_path = os.path.normpath(start_path)

	for dirpath, dirnames, filenames in os.walk(start_path, onerror= print):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if return_list: 
				r.append(fp if full_dir else fp.replace(start_path, "", 1))

			if not os.path.islink(fp):
				total_size += os.path.getsize(fp)
			if limit!=None and total_size>limit:
				print('counted upto', total_size)
				if return_list: return '2big', False
				return '2big'
	if return_list: return total_size, r
	return total_size

def humanbytes(B):
	'Return the given bytes as a human friendly KB, MB, GB, or TB string'
	B = B
	KB = 1024
	MB = (KB ** 2) # 1,048,576
	GB = (KB ** 3) # 1,073,741,824
	TB = (KB ** 4) # 1,099,511,627,776
	ret=''

	if B>=TB:
		ret+= '%i TB  '%(B//TB)
		B%=TB
	if B>=GB:
		ret+= '%i GB  '%(B//GB)
		B%=GB
	if B>=MB:
		ret+= '%i MB  '%(B//MB)
		B%=MB
	if B>=KB:
		ret+= '%i KB  '%(B//KB)
		B%=KB
	if B>0:
		ret+= '%i bytes'%B

	return ret




# PAUSE AND RESUME FEATURE ----------------------------------------

def copy_byte_range(infile, outfile, start=None, stop=None, bufsize=16*1024):
	'''
	TO SUPPORT PAUSE AND RESUME FEATURE
	Like shutil.copyfileobj, but only copy a range of the streams.
	Both start and stop are inclusive.
	'''
	if start is not None: infile.seek(start)
	while 1:
		to_read = min(bufsize, stop + 1 - infile.tell() if stop else bufsize)
		buf = infile.read(to_read)
		if not buf:
			break
		outfile.write(buf)


BYTE_RANGE_RE = re.compile(r'bytes=(\d+)-(\d+)?$')
def parse_byte_range(byte_range):
	'''Returns the two numbers in 'bytes=123-456' or throws ValueError.
	The last number or both numbers may be None.
	'''
	if byte_range.strip() == '':
		return None, None

	m = BYTE_RANGE_RE.match(byte_range)
	if not m:
		raise ValueError('Invalid byte range %s' % byte_range)

	first, last = [x and int(x) for x in m.groups()]
	if last and last < first:
		raise ValueError('Invalid byte range %s' % byte_range)
	return first, last

#---------------------------x--------------------------------




# Default error message template
DEFAULT_ERROR_MESSAGE = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
		"http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
		<title>Error response</title>
	</head>
	<body>
		<h1>Error response</h1>
		<p>Error code: %(code)d</p>
		<p>Message: %(message)s.</p>
		<p>Error code explanation: %(code)s - %(explain)s.</p>
	</body>
</html>
"""

DEFAULT_ERROR_CONTENT_TYPE = "text/html;charset=utf-8"

class HTTPServer(socketserver.TCPServer):

	allow_reuse_address = 1	# Seems to make sense in testing environment

	def server_bind(self):
		"""Override server_bind to store the server name."""
		socketserver.TCPServer.server_bind(self)
		host, port = self.server_address[:2]
		self.server_name = socket.getfqdn(host)
		self.server_port = port


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
	daemon_threads = True


class BaseHTTPRequestHandler(socketserver.StreamRequestHandler):

	"""HTTP request handler base class.

	The following explanation of HTTP serves to guide you through the
	code as well as to expose any misunderstandings I may have about
	HTTP (so you don't need to read the code to figure out I'm wrong
	:-).

	HTTP (HyperText Transfer Protocol) is an extensible protocol on
	top of a reliable stream transport (e.g. TCP/IP).  The protocol
	recognizes three parts to a request:

	1. One line identifying the request type and path
	2. An optional set of RFC-822-style headers
	3. An optional data part

	The headers and data are separated by a blank line.

	The first line of the request has the form

	<command> <path> <version>

	where <command> is a (case-sensitive) keyword such as GET or POST,
	<path> is a string containing path information for the request,
	and <version> should be the string "HTTP/1.0" or "HTTP/1.1".
	<path> is encoded using the URL encoding scheme (using %xx to signify
	the ASCII character with hex code xx).

	The specification specifies that lines are separated by CRLF but
	for compatibility with the widest range of clients recommends
	servers also handle LF.  Similarly, whitespace in the request line
	is treated sensibly (allowing multiple spaces between components
	and allowing trailing whitespace).

	Similarly, for output, lines ought to be separated by CRLF pairs
	but most clients grok LF characters just fine.

	If the first line of the request has the form

	<command> <path>

	(i.e. <version> is left out) then this is assumed to be an HTTP
	0.9 request; this form has no optional headers and data part and
	the reply consists of just the data.

	The reply form of the HTTP 1.x protocol again has three parts:

	1. One line giving the response code
	2. An optional set of RFC-822-style headers
	3. The data

	Again, the headers and data are separated by a blank line.

	The response code line has the form

	<version> <responsecode> <responsestring>

	where <version> is the protocol version ("HTTP/1.0" or "HTTP/1.1"),
	<responsecode> is a 3-digit response code indicating success or
	failure of the request, and <responsestring> is an optional
	human-readable string explaining what the response code means.

	This server parses the request and the headers, and then calls a
	function specific to the request type (<command>).  Specifically,
	a request SPAM will be handled by a method do_SPAM().  If no
	such method exists the server sends an error response to the
	client.  If it exists, it is called with no arguments:

	do_SPAM()

	Note that the request name is case sensitive (i.e. SPAM and spam
	are different requests).

	The various request details are stored in instance variables:

	- client_address is the client IP address in the form (host,
	port);

	- command, path and version are the broken-down request line;

	- headers is an instance of email.message.Message (or a derived
	class) containing the header information;

	- rfile is a file object open for reading positioned at the
	start of the optional input data part;

	- wfile is a file object open for writing.

	IT IS IMPORTANT TO ADHERE TO THE PROTOCOL FOR WRITING!

	The first thing to be written must be the response line.  Then
	follow 0 or more header lines, then a blank line, and then the
	actual data (if any).  The meaning of the header lines depends on
	the command executed by the server; in most cases, when data is
	returned, there should be at least one header line of the form

	Content-type: <type>/<subtype>

	where <type> and <subtype> should be registered MIME types,
	e.g. "text/html" or "text/plain".

	"""

	# The Python system version, truncated to its first component.
	sys_version = "Python/" + sys.version.split()[0]

	# The server software version.  You may want to override this.
	# The format is multiple whitespace-separated strings,
	# where each string is of the form name[/version].
	server_version = "BaseHTTP/" + __version__

	error_message_format = DEFAULT_ERROR_MESSAGE
	error_content_type = DEFAULT_ERROR_CONTENT_TYPE

	# The default request version.  This only affects responses up until
	# the point where the request line is parsed, so it mainly decides what
	# the client gets back when sending a malformed request line.
	# Most web servers default to HTTP 0.9, i.e. don't send a status line.
	default_request_version = "HTTP/0.9"

	def parse_request(self):
		"""Parse a request (internal).

		The request should be stored in self.raw_requestline; the results
		are in self.command, self.path, self.request_version and
		self.headers.

		Return True for success, False for failure; on failure, any relevant
		error response has already been sent back.

		"""
		self.command = None  # set in case of error on the first line
		self.request_version = version = self.default_request_version
		self.close_connection = True
		requestline = str(self.raw_requestline, 'iso-8859-1')
		requestline = requestline.rstrip('\r\n')
		self.requestline = requestline
		words = requestline.split()
		if len(words) == 0:
			return False

		if len(words) >= 3:  # Enough to determine protocol version
			version = words[-1]
			try:
				if not version.startswith('HTTP/'):
					raise ValueError
				base_version_number = version.split('/', 1)[1]
				version_number = base_version_number.split(".")
				# RFC 2145 section 3.1 says there can be only one "." and
				#   - major and minor numbers MUST be treated as
				#	  separate integers;
				#   - HTTP/2.4 is a lower version than HTTP/2.13, which in
				#	  turn is lower than HTTP/12.3;
				#   - Leading zeros MUST be ignored by recipients.
				if len(version_number) != 2:
					raise ValueError
				version_number = int(version_number[0]), int(version_number[1])
			except (ValueError, IndexError):
				self.send_error(
					HTTPStatus.BAD_REQUEST,
					"Bad request version (%r)" % version)
				return False
			if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
				self.close_connection = False
			if version_number >= (2, 0):
				self.send_error(
					HTTPStatus.HTTP_VERSION_NOT_SUPPORTED,
					"Invalid HTTP version (%s)" % base_version_number)
				return False
			self.request_version = version

		if not 2 <= len(words) <= 3:
			self.send_error(
				HTTPStatus.BAD_REQUEST,
				"Bad request syntax (%r)" % requestline)
			return False
		command, path = words[:2]
		if len(words) == 2:
			self.close_connection = True
			if command != 'GET':
				self.send_error(
					HTTPStatus.BAD_REQUEST,
					"Bad HTTP/0.9 request type (%r)" % command)
				return False
		self.command, self.path = command, path

		# Examine the headers and look for a Connection directive.
		try:
			self.headers = http.client.parse_headers(self.rfile,
													 _class=self.MessageClass)
		except http.client.LineTooLong as err:
			self.send_error(
				HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
				"Line too long",
				str(err))
			return False
		except http.client.HTTPException as err:
			self.send_error(
				HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
				"Too many headers",
				str(err)
			)
			return False

		conntype = self.headers.get('Connection', "")
		if conntype.lower() == 'close':
			self.close_connection = True
		elif (conntype.lower() == 'keep-alive' and
			  self.protocol_version >= "HTTP/1.1"):
			self.close_connection = False
		# Examine the headers and look for an Expect directive
		expect = self.headers.get('Expect', "")
		if (expect.lower() == "100-continue" and
				self.protocol_version >= "HTTP/1.1" and
				self.request_version >= "HTTP/1.1"):
			if not self.handle_expect_100():
				return False
		return True

	def handle_expect_100(self):
		"""Decide what to do with an "Expect: 100-continue" header.

		If the client is expecting a 100 Continue response, we must
		respond with either a 100 Continue or a final response before
		waiting for the request body. The default is to always respond
		with a 100 Continue. You can behave differently (for example,
		reject unauthorized requests) by overriding this method.

		This method should either return True (possibly after sending
		a 100 Continue response) or send an error response and return
		False.

		"""
		self.send_response_only(HTTPStatus.CONTINUE)
		self.end_headers()
		return True

	def handle_one_request(self):
		"""Handle a single HTTP request.

		You normally don't need to override this method; see the class
		__doc__ string for information on how to handle specific HTTP
		commands such as GET and POST.

		"""
		try:
			self.raw_requestline = self.rfile.readline(65537)
			if len(self.raw_requestline) > 65536:
				self.requestline = ''
				self.request_version = ''
				self.command = ''
				self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
				return
			if not self.raw_requestline:
				self.close_connection = True
				return
			if not self.parse_request():
				# An error code has been sent, just exit
				return
			mname = 'do_' + self.command
			if not hasattr(self, mname):
				self.send_error(
					HTTPStatus.NOT_IMPLEMENTED,
					"Unsupported method (%r)" % self.command)
				return
			method = getattr(self, mname)
			method()
			self.wfile.flush() #actually send the response if not already done.
		except socket.timeout as e:
			#a read or a write timed out.  Discard this connection
			self.log_error("Request timed out: %r", e)
			self.close_connection = True
			return

	def handle(self):
		"""Handle multiple requests if necessary."""
		self.close_connection = True

		self.handle_one_request()
		while not self.close_connection:
			self.handle_one_request()

	def send_error(self, code, message=None, explain=None):
		"""Send and log an error reply.

		Arguments are
		* code:	an HTTP error code
				   3 digits
		* message: a simple optional 1 line reason phrase.
				   *( HTAB / SP / VCHAR / %x80-FF )
				   defaults to short entry matching the response code
		* explain: a detailed message defaults to the long entry
				   matching the response code.

		This sends an error response (so it must be called before any
		output has been generated), logs the error, and finally sends
		a piece of HTML explaining the error to the user.

		"""

		try:
			shortmsg, longmsg = self.responses[code]
		except KeyError:
			shortmsg, longmsg = '???', '???'
		if message is None:
			message = shortmsg
		if explain is None:
			explain = longmsg
		self.log_error("code %d, message %s", code, message)
		self.send_response(code, message)
		self.send_header('Connection', 'close')

		# Message body is omitted for cases described in:
		#  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
		#  - RFC7231: 6.3.6. 205(Reset Content)
		body = None
		if (code >= 200 and
			code not in (HTTPStatus.NO_CONTENT,
						 HTTPStatus.RESET_CONTENT,
						 HTTPStatus.NOT_MODIFIED)):
			# HTML encode to prevent Cross Site Scripting attacks
			# (see bug #1100201)
			content = (self.error_message_format % {
				'code': code,
				'message': html.escape(message, quote=False),
				'explain': html.escape(explain, quote=False)
			})
			body = content.encode('UTF-8', 'replace')
			self.send_header("Content-Type", self.error_content_type)
			self.send_header('Content-Length', str(len(body)))
		self.end_headers()

		if self.command != 'HEAD' and body:
			self.wfile.write(body)

	def send_response(self, code, message=None):
		"""Add the response header to the headers buffer and log the
		response code.

		Also send two standard headers with the server software
		version and the current date.

		"""
		self.log_request(code)
		self.send_response_only(code, message)
		self.send_header('Server', self.version_string())
		self.send_header('Date', self.date_time_string())

	def send_response_only(self, code, message=None):
		"""Send the response header only."""
		if self.request_version != 'HTTP/0.9':
			if message is None:
				if code in self.responses:
					message = self.responses[code][0]
				else:
					message = ''
			if not hasattr(self, '_headers_buffer'):
				self._headers_buffer = []
			self._headers_buffer.append(("%s %d %s\r\n" %
					(self.protocol_version, code, message)).encode(
						'utf-8', 'strict'))

	def send_header(self, keyword, value):
		"""Send a MIME header to the headers buffer."""
		if self.request_version != 'HTTP/0.9':
			#print(("%s: %s\r\n" % (keyword, value)))
			if not hasattr(self, '_headers_buffer'):
				self._headers_buffer = []
			self._headers_buffer.append(
				("%s: %s\r\n" % (keyword, value)).encode('utf-8', 'strict'))

		if keyword.lower() == 'connection':
			if value.lower() == 'close':
				self.close_connection = True
			elif value.lower() == 'keep-alive':
				self.close_connection = False

	def end_headers(self):
		"""Send the blank line ending the MIME headers."""
		if self.request_version != 'HTTP/0.9':
			self._headers_buffer.append(b"\r\n")
			self.flush_headers()

	def flush_headers(self):
		if hasattr(self, '_headers_buffer'):
			self.wfile.write(b"".join(self._headers_buffer))
			self._headers_buffer = []

	def log_request(self, code='-', size='-'):
		"""Log an accepted request.

		This is called by send_response().

		"""
		if isinstance(code, HTTPStatus):
			code = code.value
		self.log_message('"%s" %s %s',
						 self.requestline, str(code), str(size))

	def log_error(self, format, *args):
		"""Log an error.

		This is called when a request cannot be fulfilled.  By
		default it passes the message on to log_message().

		Arguments are the same as for log_message().

		XXX This should go to the separate error log.

		"""

		self.log_message(format, *args)

	def log_message(self, format, *args):
		"""Log an arbitrary message.

		This is used by all other logging functions.  Override
		it if you have specific logging wishes.

		The first argument, FORMAT, is a format string for the
		message to be logged.  If the format string contains
		any % escapes requiring parameters, they should be
		specified as subsequent arguments (it's just like
		printf!).

		The client ip and current date/time are prefixed to
		every message.

		"""

		sys.stderr.write("%s - - [%s] %s\n" %
						 (self.address_string(),
						  self.log_date_time_string(),
						  format%args))

		with open(config.log_location + 'log.txt','a+') as f:
			f.write("\n\n" + "%s - - [%s] %s\n" %
						 (self.address_string(),
						  self.log_date_time_string(),
						  format%args))

	def version_string(self):
		"""Return the server software version string."""
		return self.server_version + ' ' + self.sys_version

	def date_time_string(self, timestamp=None):
		"""Return the current date and time formatted for a message header."""
		if timestamp is None:
			timestamp = time.time()
		return email.utils.formatdate(timestamp, usegmt=True)

	def log_date_time_string(self):
		"""Return the current time formatted for logging."""
		now = time.time()
		year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
		s = "%02d/%3s/%04d %02d:%02d:%02d" % (
				day, self.monthname[month], year, hh, mm, ss)
		return s

	weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

	monthname = [None,
				 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
				 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

	def address_string(self):
		"""Return the client address."""

		return self.client_address[0]

	# Essentially static class variables

	# The version of the HTTP protocol we support.
	# Set this to HTTP/1.1 to enable automatic keepalive
	protocol_version = "HTTP/1.0"

	# MessageClass used to parse headers
	MessageClass = http.client.HTTPMessage

	# hack to maintain backwards compatibility
	responses = {
		v: (v.phrase, v.description)
		for v in HTTPStatus.__members__.values()
	}


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	"""Simple HTTP request handler with GET and HEAD commands.

	This serves files from the current directory and any of its
	subdirectories.  The MIME type for files is determined by
	calling the .guess_type() method.

	The GET and HEAD requests are identical except that the HEAD
	request omits the actual contents of the file.

	"""

	server_version = "SimpleHTTP/" + __version__

	def __init__(self, *args, directory=None, **kwargs):
		if directory is None:
			directory = os.getcwd()
		self.directory = directory
		super().__init__(*args, **kwargs)

	def do_GET(self):
		"""Serve a GET request."""
		f = self.send_head()
		if f:
			try:
				self.copyfile(f, self.wfile)
			except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
				print(e.__class__.__name__, e)
			finally:
				f.close()

	def do_HEAD(self):
		"""Serve a HEAD request."""
		f = self.send_head()
		if f:
			f.close()

	def do_POST(self):
		"""Serve a POST request."""
		self.range = None # bug patch

		r, info = self.deal_post_data()
		if r == None:
			if info=='get-json':
				return self.list_directory_json()
		print((r, info, "by: ", self.client_address))
		f = io.BytesIO()


		if r==True:
			head = "Success"
		elif r==False:
			head = "Failed"
		else:
			head = r

		body = info


		f.write(json.dumps([head, body]).encode())

		length = f.tell()
		f.seek(0)
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.send_header("Content-Length", str(length))
		self.end_headers()

		if f:
			print(69*111111)
			self.copyfile(f, self.wfile)
			f.close()

	def deal_post_data(self):
		boundary = None
		uid = None
		num = 0
		post_type = None

		refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh🔄️</div>"


		def get_rel_path(filename):
			return urllib.parse.unquote(posixpath.join(self.path, filename), errors='surrogatepass')


		def get(show=True, strip=False, self=self):
			"""
			show: print line
			strip: strip \r\n at end
			"""
			nonlocal num, remainbytes
			line = self.rfile.readline()
			if show:
				print(num, line)
				num+=1
			remainbytes -= len(line)

			if strip and line.endswith(b"\r\n"):
				line = line.rpartition(b"\r\n")[0]

			return line

		def pass_bound(self=self):
			nonlocal remainbytes
			line = get(0)
			if not boundary in line:
				return (False, "Content NOT begin with boundary")

		def get_type(line=None, self=self):
			nonlocal remainbytes
			if not line:
				line = get()
			try:
				return re.findall(r'Content-Disposition.*name="(.*?)"', line.decode())[0]
			except: return None

		def skip(self=self):
			get(0)

		def handle_files(self=self):
			nonlocal remainbytes
			uploaded_files = [] # Uploaded folder list

			# pass boundary
			pass_bound()


			# PASSWORD SYSTEM
			if get_type()!="password":
				return (False, "Invalid request")


			skip()
			password= get(0)
			print('post password: ',  password)
			if password != config.PASSWORD + b'\r\n': # readline returns password with \r\n at end
				return (False, "Incorrect password") # won't even read what the random guy has to say and slap 'em

			pass_bound()


			while remainbytes > 0:
				line =get()

				fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
				if not fn:
					return (False, "Can't find out file name...")
				path = self.translate_path(self.path)

				fn = os.path.join(path, fn[0])
				line = get(0) # content type
				line = get(0) # line gap

				# ORIGINAL FILE STARTS FROM HERE
				try:
					out = open(fn, 'wb')
				except IOError:
					return (False, "Can't create file to write, do you have permission to write?")
				else:
					with out:
						preline = get(0)
						while remainbytes > 0:
							line = get(0)
							if boundary in line:
								preline = preline[0:-1]
								if preline.endswith(b'\r'):
									preline = preline[0:-1]
								out.write(preline)
								uploaded_files.append(fn)
								break
							else:
								out.write(preline)
								preline = line


			return (True, ("<!DOCTYPE html><html>\n<title>Upload Result Page</title>\n<body>\n<h2>Upload Result Page</h2>\n<hr>\nFile '%s' upload success!" % ",".join(uploaded_files)) +"<br><a href=\"%s\">back</a>" % self.headers['referer'] + refresh)


		def del_data(self=self):

			if disabled_func["trash"]:
				return (False, "Trash not available. Please contact the Host...")

			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()


			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))
			#print(tools.text_box(xpath))

			print('send2trash "%s" by: %s'%(xpath, uid))

			bool = False
			try:
				send2trash(xpath)
				msg = "Successfully Moved To Recycle bin"+refresh
				bool = True
			except TrashPermissionError:
				msg = "Recycling unavailable! Try deleting permanently..."
			except Exception as e:
				traceback.print_exc()
				msg = "<b>" + path + "<b>" + e.__class__.__name__ + " : " + str(e)

			return (bool, msg)



		def del_permanently(self=self):

			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()


			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))
			#print(tools.text_box(xpath))

			print('Perm. DELETED "%s" by: %s'%(xpath, uid))


			try:
				if os.path.isfile(xpath): os.remove(xpath)
				else: shutil.rmtree(xpath)

				return (True, "PERMANENTLY DELETED  " + path +refresh)


			except Exception as e:
				return (False, "<b>" + path + "<b>" + e.__class__.__name__ + " : " + str(e))


		def rename(self=self):
			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()

			pass_bound()

			if get_type()!="data":
				return (False, "Invalid request")


			skip()
			new_name = get(strip=1).decode()


			path = get_rel_path(filename)


			#print(tools.text_box(filename))
			xpath = self.translate_path(posixpath.join(self.path, filename))


			new_path = self.translate_path(posixpath.join(self.path, new_name))

			#print(tools.text_box(xpath))
			print('Renamed "%s" by: %s'%(xpath, uid))


			try:
				os.rename(xpath, new_path)
				return (True, "Rename successful!" + refresh)
			except Exception as e:
				return (False, "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) )


		def info(self=self):


			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()



			path = get_rel_path(filename)

			#print(tools.text_box(filename))
			xpath = self.translate_path(posixpath.join(self.path, filename))

			#print(tools.text_box(xpath))
			print('Info Checked "%s" by: %s'%(xpath, uid))

			data = {}
			data["Name"] = filename
			if os.path.isfile(xpath):
				data["Type"] = "File"
				if "." in filename:
					data["Extension"] = filename.rpartition(".")[2]

				size = int(os.path.getsize(xpath))

			elif os.path.isdir(xpath):
				data["Type"] = "Folder"
				size = get_dir_size(xpath)

			data["Size"] = humanbytes(size) + " (%i bytes)"%size
			data["Path"] = path

			def get_dt(time):
				return datetime.datetime.fromtimestamp(time)

			data["Created on"] = get_dt(os.path.getctime(xpath))
			data["Last Modified"] = get_dt(os.path.getmtime(xpath))
			data["Last Accessed"] = get_dt(os.path.getatime(xpath))

			body = """
<style>
table {
  font-family: arial, sans-serif;
  border-collapse: collapse;
  width: 100%;
}

td, th {
  border: 1px solid #00BFFF;
  text-align: left;
  padding: 8px;
}

tr:nth-child(even) {
  background-color: #111;
}
</style>

<table>
  <tr>
    <th>About</th>
    <th>Info</th>
  </tr>
  """
			for i in data.keys():
				body += "<tr><td>%s</td><td>%s</td></tr>"%(i, data[i])
			body += "</table>"

			return ("Properties", body)


		def new_folder(self=self):


			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()



			path = get_rel_path(filename)

			#print(tools.text_box(filename))
			xpath = self.translate_path(posixpath.join(self.path, filename))

			#print(tools.text_box(xpath))
			print('Info Checked "%s" by: %s'%(xpath, uid))

			try:
				os.makedirs(xpath)
				return (True, "New Folder Created:  " + path +refresh)

			except Exception as e:
				return (False, "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) )

		while 0:
			line = get()


		content_type = self.headers['content-type']
		print(self.headers)

		if not content_type:
			return (False, "Content-Type header doesn't contain boundary")
		boundary = content_type.split("=")[1].encode()

		remainbytes = int(self.headers['content-length'])


		pass_bound()# LINE 1

		# get post type
		if get_type()=="post-type":
			skip() # newline
		else:
			return (False, "Invalid post request")

		line = get()
		handle_type = line.decode().strip() # post type LINE 3

		pass_bound() #boundary for password or guid of user

		if get_type()=="post-uid":
			skip() # newline
		else:
			return (False, "Unknown User request")

		uid = get() # uid LINE 5

		##################################

		# HANDLE USER PERMISSION BY CHECKING UID

		##################################

		if handle_type == "upload":
			return handle_files()


		elif handle_type == "test":
			while remainbytes > 0:
				line =get()

		elif handle_type == "del-f":
			return del_data()

		elif handle_type == "del-p":
			return del_permanently()

		elif handle_type=="rename":
			return rename()

		elif handle_type=="info":
			return info()

		elif handle_type == "new folder":
			return new_folder()

		elif handle_type == "get-json":
			return (None, "get-json")

		return (True, "Something")



	def send_head(self):
		"""Common code for GET and HEAD commands.

		This sends the response code and MIME headers.

		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.

		"""

		global reload, zip_ids, zip_in_progress

		if 'Range' not in self.headers:
			self.range = None
			first, last = 0, 0

		else:
			try:
				self.range = parse_byte_range(self.headers['Range'])
				first, last = self.range
			except ValueError as e:
				self.send_error(400, 'Invalid byte range')
				return None

		path = self.translate_path(self.path)
		spathtemp= os.path.split(self.path)
		pathtemp= os.path.split(path)
		spathsplit = self.path.split('/')

		filename = None

		if self.path == '/favicon.ico':
			self.send_response(301)
			self.send_header('Location','https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.ico')
			self.end_headers()
			return None




		print('path',path, '\nself.path',self.path, '\nspathtemp',spathtemp, '\npathtemp',pathtemp, '\nspathsplit',spathsplit)

		if spathsplit[-1] == "?reload?":
			# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
			reload = True

			httpd.server_close()
			httpd.shutdown()

		elif spathsplit[-1].startswith('dlY%3F'):
			msg = False
			if disabled_func["7z"]:
				msg = "Zip function is not available, please Contact the host"
			else:
				# print("=="*10, "\n\n")
				filename = pathtemp[-1][4:-29]
				# print("filename", filename)
				id = pathtemp[-1][-24:]
				# print("id", id)
				loc = zip_temp_dir
				zip_name = id + '.zip'
				zip_path = os.path.join(str(loc), zip_name)
				zip_source = os.path.join(pathtemp[0], pathtemp[-1][4:-29])

				# print('zip_ids', zip_ids)

				# print(id in zip_ids.keys())
				# print(id in zip_in_progress)

				xpath = pathtemp[0] +'\\' + pathtemp[-1][4:-29]

				try:
					if id in zip_ids.keys():
						path = zip_path
						filename = zip_ids[id] + ".zip"

						if not os.path.isfile(path):
							zip_ids.pop(id)


					if id in zip_in_progress:
						while id in zip_in_progress:
							time.sleep(1)
						path = zip_path
						filename = zip_ids[id] + ".zip"

					if not (id in zip_ids.keys() or id in zip_in_progress):
						zip_in_progress.append(id)

						# print("Downloading", filename, "from", id)
						# print("==================== current path", str(loc))
						# print("==================== to zip path ", str(pathtemp[-1][4:-29]))


						# print(' '.join([_7z_parent_dir+'/7z/7za', 'a', '-mx=0', str(loc)+'\\'+id+'.zip', pathtemp[0] +'\\' + pathtemp[-1][4:-29]]))
						subprocess.call(config._7z_command(['a', '-mx=0', zip_path , zip_source]))
						zip_in_progress.remove(id)
						zip_ids[id] = filename
						path = zip_path
						filename = zip_ids[id] + ".zip"
				except Exception as e:
					traceback.print_exc()

					msg = "<!doctype HTML><h1>Zipping failed  " + xpath + "</h1><br>" + e.__class__.__name__

					if config.allow_web_log:
						msg += " : " + str(e) + "\n\n\n" + traceback.format_exc().replace("\n", "<br>")
						msg += "<br><br><b>7z location:</b> " + config._7z_parent_dir +  config._7z_location
						msg += "<br><br><b>Command</b> " + ' '.join(config._7z_command(['a', '-mx=0', zip_path , zip_source]))
						msg += "<br><br>"
						msg += ' '.join(map(str, ['path',path, '<br>self.path',self.path, '<br>spathtemp',spathtemp, '<br>pathtemp',pathtemp, '<br>spathsplit',spathsplit]))
						msg += "<br><br>"
						msg += ' '.join(map(str, ['loc',loc, '<br>id',id, '<br>zip_name',zip_name, '<br>zip_path',zip_path, '<br>zip_ids',zip_ids, '<br>zip_in_progress',zip_in_progress]))
						msg += "<br><br>"

			if msg:
				encoded = msg.encode('utf-8', 'surrogateescape')

				f = io.BytesIO()
				f.write(encoded)

				f.seek(0)

				self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
				self.send_header("Content-type", "text/html; charset=%s" % 'utf-8')
				self.send_header("Content-Length", str(len(encoded)))
				self.end_headers()
				return f

		elif self.path.endswith('/') and spathsplit[-2].startswith('dl%3F'):
			if disabled_func["7z"]:
				outp = "Zip function is not available, please Contact the host"
			else:
				path= self.translate_path('/'.join(spathsplit[:-2])+'/'+spathsplit[-2][5:]+'/')
				if not os.path.isdir(path):
					outp = "<!DOCTYPE HTML><h1>Directory not found</h1>"
				else:
					# print('init')
					total_size, r = get_dir_size(path, 8*1024*1024*1024, True, False)  # max size limit = 8GB
					id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))+'_'+ str(time.time())
					id += '0'*(25-len(id))
					print(total_size, r)
					too_big= total_size=='2big'
					# print(too_big)
					print("Directory size: " + str(total_size))
					outp='<!DOCTYPE HTML><h1>The folder size is too big</h1>\
						' if too_big else """<!DOCTYPE HTML><h1> Download will start shortly</h1>
						<br><br>
						<iframe src="../dlY%3F"""+spathsplit[-2][5:] +"%3Fid="+id+"""" style="display:none;border: transparent;" height="600px" width="900px"
						onload="this.style.display = 'block'"></iframe>
						<pre style='font-size:20px; font-weight: 600;'><b>Directory size:</b> """ + humanbytes(total_size) + """</pre>
						<br><br>The directory has:\n<hr>"""+ ("\n".join(['<u>'+i+'</u><br>' for i in r]) + """
						<script>//window.open("../dlY%3F"""+spathsplit[-2][5:] +"%3Fid="+id+'", "_blank");</script>')
			encoded = outp.encode('utf-8', 'surrogateescape')

			f = io.BytesIO()
			f.write(encoded)

			f.seek(0)
			self.send_response(HTTPStatus.OK)
			self.send_header("Content-type", "text/html; charset=%s" % 'utf-8')
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			return f


		elif spathtemp[0].startswith('/drive%3E'):
			# SWITCH TO A DIFFERENT DRIVE ON WINDOWS
			# NOT WORKING YET

			if os.path.isdir(spathtemp[0][9:]+':\\'):
				self.path = spathtemp[0][9]+':\\'
				self.directory = self.path
				try: self.path += spathtemp[0][10:]
				except: pass
				self.path = spathtemp[1]
				path = self.translate_path(self.path)

				#print('path',path, '\nself.path',self.path)
				spathtemp= os.path.split(self.path)
				pathtemp= os.path.split(path)

		elif spathsplit[-1].startswith('vid%3F') or os.path.exists(path):
			# SEND VIDEO PLAYER
			if spathsplit[-1].startswith('vid%3F') and self.guess_type(os.path.join(pathtemp[0],  pathtemp[-1][4:])).startswith('video/'):

				self.path= "/".join(spathsplit[:-1]+ [spathtemp[1][6:],])
				#print(tools.text_box(self.path))
				path=os.path.join(pathtemp[0],  pathtemp[1][4:])

				r = []
				try:
					displaypath = urllib.parse.unquote(self.path,
													errors='surrogatepass')
				except UnicodeDecodeError:
					displaypath = urllib.parse.unquote(path)
				displaypath = html.escape(displaypath, quote=False)
				enc = sys.getfilesystemencoding()


				title = self.get_titles(displaypath)

				"""r.append('<!DOCTYPE HTML>')
				r.append('<html>\n<head>')
				r.append('<meta http-equiv="Content-Type" '
						'content="text/html; charset=%s">' % enc)
				r.append('<title>%s</title>\n</head>' % title)"""
				r.append(directory_explorer_header%(enc, title,
				 config.address(), self.dir_navigator(displaypath)))

				if self.guess_type(os.path.join(pathtemp[0],  spathsplit[-1][6:])) not in ['video/mp4', 'video/ogg', 'video/webm']:
					r.append('<h2>It seems HTML player can\'t play this Video format, Try Downloading</h2>')
				else:
					ctype = self.guess_type("/".join([pathtemp[0],  spathsplit[-1][6:]]))
					r.append('''
<!-- stolen from http://plyr.io -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/RaSan147/httpserver_with_many_feat@main/video.css" />

<link rel="preload" as="font" crossorigin type="font/woff2" href="https://cdn.plyr.io/static/fonts/gordita-medium.woff2" />
<link rel="preload" as="font" crossorigin type="font/woff2" href="https://cdn.plyr.io/static/fonts/gordita-bold.woff2" />

<div id="container">
	<video controls crossorigin playsinline data-poster="https://i.imgur.com/jQZ5DoV.jpg" id="player">

	<source src="%s" type="%s"/>
	<a href="%s" download>Download</a>
	</video>


<script src="https://cdn.plyr.io/3.6.9/demo.js" crossorigin="anonymous"></script>
	</div><br>'''%(self.path, ctype, self.path))

				r.append('<br><a href="%s"><div class=\'pagination\'>Download</div></a></li>'
					% self.path)


				r.append('\n<hr>\n</body>\n</html>\n')
				encoded = '\n'.join(r).encode(enc, 'surrogateescape')
				f = io.BytesIO()
				f.write(encoded)
				f.seek(0)
				self.send_response(HTTPStatus.OK)
				self.send_header("Content-type", "text/html; charset=%s" % enc)
				self.send_header("Content-Length", str(len(encoded)))
				self.end_headers()
				return f

		f = None
		if os.path.isdir(path):
			parts = urllib.parse.urlsplit(self.path)
			if not parts.path.endswith('/'):
				# redirect browser - doing basically what apache does
				self.send_response(HTTPStatus.MOVED_PERMANENTLY)
				new_parts = (parts[0], parts[1], parts[2] + '/',
							 parts[3], parts[4])
				new_url = urllib.parse.urlunsplit(new_parts)
				self.send_header("Location", new_url)
				self.end_headers()
				return None
			for index in "index.html", "index.htm":
				index = os.path.join(path, index)
				if os.path.exists(index):
					path = index
					break
			else:
				#print(path)
				return self.list_directory(path)

		# check for trailing "/" which should return 404. See Issue17324
		# The test for this was added in test_httpserver.py
		# However, some OS platforms accept a trailingSlash as a filename
		# See discussion on python-dev and Issue34711 regarding
		# parseing and rejection of filenames with a trailing slash
		if path.endswith("/"):
			self.send_error(HTTPStatus.NOT_FOUND, "File not found")
			return None





		else:
			ctype = self.guess_type(path)
			f = open(path, 'rb')
			try:
				fs = os.fstat(f.fileno())

				file_len = fs[6]
				if self.range and first >= file_len: # PAUSE AND RESUME SUPPORT
					self.send_error(416, 'Requested Range Not Satisfiable')
					return None
				# Use browser cache if possible
				if ("If-Modified-Since" in self.headers
						and "If-None-Match" not in self.headers):
					# compare If-Modified-Since and time of last file modification
					try:
						ims = email.utils.parsedate_to_datetime(
							self.headers["If-Modified-Since"])
					except (TypeError, IndexError, OverflowError, ValueError):
						# ignore ill-formed values
						pass
					else:
						if ims.tzinfo is None:
							# obsolete format with no timezone, cf.
							# https://tools.ietf.org/html/rfc7231#section-7.1.1.1
							ims = ims.replace(tzinfo=datetime.timezone.utc)
						if ims.tzinfo is datetime.timezone.utc:
							# compare to UTC datetime of last modification
							last_modif = datetime.datetime.fromtimestamp(
								fs.st_mtime, datetime.timezone.utc)
							# remove microseconds, like in If-Modified-Since
							last_modif = last_modif.replace(microsecond=0)

							if last_modif <= ims:
								self.send_response(HTTPStatus.NOT_MODIFIED)
								self.end_headers()
								f.close()
								return None
				if self.range:
					self.send_response(206)
					self.send_header('Content-type', ctype)
					self.send_header('Accept-Ranges', 'bytes')


					if last is None or last >= file_len:
						last = file_len - 1
					response_length = last - first + 1

					self.send_header('Content-Range',
									'bytes %s-%s/%s' % (first, last, file_len))
					self.send_header('Content-Length', str(response_length))



				else:
					self.send_response(HTTPStatus.OK)
					self.send_header("Content-type", ctype)
					self.send_header("Content-Length", str(fs[6]))

				self.send_header("Last-Modified",
								self.date_time_string(fs.st_mtime))
				self.send_header("Content-Disposition", 'filename="%s"' % (os.path.basename(path) if filename is None else filename))
				self.end_headers()
				return f
			except:
				f.close()
				raise




	def list_directory_json(self, path):
		"""Helper to produce a directory listing (JSON).
		Return json file of available files and folders"""

		try:
			list = os.listdir(path)
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		list.sort(key=lambda a: a.lower())
		dir_dict = {"paths": [], "names":[]}


		for name in list:
			fullname = os.path.join(path, name)
			print(fullname)
			displayname = linkname = name


			_is_dir_ = True
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			elif os.path.islink(fullname):
				displayname = name + "@"

			dir_dict["paths"].append(urllib.parse.quote(linkname, errors='surrogatepass'))
			dir_dict["names"].append(html.escape(displayname, quote=False))

		encoded = json.dumps(dir_dict).encode("utf-8", 'surrogateescape')
		f = io.BytesIO()
		f.write(encoded)
		f.seek(0)
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-type", "application/json; charset=%s" % "utf-8")
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return f

	def list_directory(self, path):
		"""Helper to produce a directory listing (absent index.html).

		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().

		"""
		print(path)
		try:
			list = os.listdir(path)
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		list.sort(key=lambda a: a.lower())
		r = []
		try:
			displaypath = urllib.parse.unquote(self.path,
											   errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(path)
		displaypath = html.escape(displaypath, quote=False)
		enc = sys.getfilesystemencoding()


		title = self.get_titles(displaypath)

		r.append(directory_explorer_header%(enc, title,
		config.address(), self.dir_navigator(displaypath)))
		'''r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
				 '"http://www.w3.org/TR/html4/strict.dtd">')
		r.append('<meta http-equiv="Content-Type" '
				 'content="text/html; charset=%s">' % enc)
		r.append('<title>%s</title>\n</head>' % title)'''
		#r.append('<body>\n<h1>%s</h1>' % title)
		r.append('<hr>\n<ul id= "linkss">')
		r_li= [] # type + file_link
				 # f  : File
				 # d  : Directory
				 # v  : Video
				 # h  : HTML
		f_li = [] # file_names


		# r.append("""<a href="../" style="background-color: #000;padding: 3px 20px 8px 20px;border-radius: 4px;">&#128281; {Prev folder}</a>""")
		for name in list:
			fullname = os.path.join(path, name)
			displayname = linkname = name
			# Append / for directories or @ for symbolic links
			_is_dir_ = True
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			elif os.path.islink(fullname):
				displayname = name + "@"
			else:
				_is_dir_ =False
				__, ext = posixpath.splitext(fullname)
				if ext=='.html':
					r_li.append('h'+ urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(html.escape(displayname, quote=False))

				elif self.guess_type(linkname).startswith('video/'):
					r_li.append('v'+ urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(html.escape(displayname, quote=False))

				elif self.guess_type(linkname).startswith('image/'):
					r_li.append('i'+ urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(html.escape(displayname, quote=False))

				else:
					r_li.append('f'+ urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(html.escape(displayname, quote=False))
			if _is_dir_:
				r_li.append('d' + urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(html.escape(displayname, quote=False))



				# Note: a link to a directory displays with @ and links with /
		# r.append('')

		# r.append('''''')

		r.append(_js_script%(str(r_li), str(f_li)))
		# r.append('<script>function dl_(typee, locate){window.open(typee+"%3F"+locate,"_self");}</script></body>\n</html>\n')
		encoded = '\n'.join(r).encode(enc, 'surrogateescape')
		f = io.BytesIO()
		f.write(encoded)
		f.seek(0)
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-type", "text/html; charset=%s" % enc)
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return f

	def get_titles(self, path):

		paths = path.split('/')
		if paths[-2]=='':
			return 'Viewing &#127968; HOME'
		else:
			return 'Viewing ' + paths[-2]

	def dir_navigator(self, path):
		"""Makes each part of the header directory accessible like links
		just like file manager, but with less CSS"""

		dirs = path.split('/')
		urls = ['/']
		names = ['&#127968; HOME']
		r = []

		for i in range(1, len(dirs)):
			dir = dirs[i]
			urls.append(urls[i-1] + urllib.parse.quote(dir, errors='surrogatepass' )+ '/')
			names.append(dir)

		for i in range(len(names)):
			tag = "<a href='" + urls[i] + "'>" + names[i] + "</a>"
			r.append(tag)

		return '<span class="dir_arrow">&#10151;</span>'.join(r)


	def translate_path(self, path):
		"""Translate a /-separated PATH to the local filename syntax.

		Components that mean special things to the local file system
		(e.g. drive or directory names) are ignored.  (XXX They should
		probably be diagnosed.)

		"""
		# abandon query parameters
		path = path.split('?',1)[0]
		path = path.split('#',1)[0]
		# Don't forget explicit trailing slash when normalizing. Issue17324
		trailing_slash = path.rstrip().endswith('/')
		try:
			path = urllib.parse.unquote(path, errors='surrogatepass')
		except UnicodeDecodeError:
			path = urllib.parse.unquote(path)
		path = posixpath.normpath(path)
		words = path.split('/')
		words = filter(None, words)
		path = self.directory
		#print(self.directory)
		for word in words:
			if os.path.dirname(word) or word in (os.curdir, os.pardir):
				# Ignore components that are not a simple file/directory name
				continue
			path = os.path.join(path, word)
		if trailing_slash:
			path += '/'
		return os.path.normpath(path) # fix OS based path issue

	def copyfile(self, source, outputfile):
		"""Copy all data between two file objects.

		The SOURCE argument is a file object open for reading
		(or anything with a read() method) and the DESTINATION
		argument is a file object open for writing (or
		anything with a write() method).

		The only reason for overriding this would be to change
		the block size or perhaps to replace newlines by CRLF
		-- note however that this the default server uses this
		to copy binary data as well.

		"""


		if not self.range:
			source.read(1)
			source.seek(0)
			shutil.copyfileobj(source, outputfile)

		else:
			# SimpleHTTPRequestHandler uses shutil.copyfileobj, which doesn't let
			# you stop the copying before the end of the file.
			start, stop = self.range  # set in send_head()
			copy_byte_range(source, outputfile, start, stop)


	def guess_type(self, path):
		"""Guess the type of a file.

		Argument is a PATH (a filename).

		Return value is a string of the form type/subtype,
		usable for a MIME Content-type header.

		The default implementation looks the file's extension
		up in the table self.extensions_map, using application/octet-stream
		as a default; however it would be permissible (if
		slow) to look inside the data to make a better guess.

		"""

		base, ext = posixpath.splitext(path)
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		ext = ext.lower()
		if ext in self.extensions_map:
			return self.extensions_map[ext]
		else:
			return self.extensions_map['']

	if not mimetypes.inited:
		mimetypes.init() # try to read system mime.types
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
		'': 'application/octet-stream', # Default
		'.py': 'text/plain',
		'.c': 'text/plain',
		'.h': 'text/plain',
		})


# Utilities for CGIHTTPRequestHandler

def _url_collapse_path(path):
	"""
	Given a URL path, remove extra '/'s and '.' path elements and collapse
	any '..' references and returns a collapsed path.

	Implements something akin to RFC-2396 5.2 step 6 to parse relative paths.
	The utility of this function is limited to is_cgi method and helps
	preventing some security attacks.

	Returns: The reconstituted URL, which will always start with a '/'.

	Raises: IndexError if too many '..' occur within the path.

	"""
	# Query component should not be involved.
	path, _, query = path.partition('?')
	path = urllib.parse.unquote(path)

	# Similar to os.path.split(os.path.normpath(path)) but specific to URL
	# path semantics rather than local operating system semantics.
	path_parts = path.split('/')
	head_parts = []
	for part in path_parts[:-1]:
		if part == '..':
			head_parts.pop() # IndexError if more '..' than prior parts
		elif part and part != '.':
			head_parts.append( part )
	if path_parts:
		tail_part = path_parts.pop()
		if tail_part:
			if tail_part == '..':
				head_parts.pop()
				tail_part = ''
			elif tail_part == '.':
				tail_part = ''
	else:
		tail_part = ''

	if query:
		tail_part = '?'.join((tail_part, query))

	splitpath = ('/' + '/'.join(head_parts), tail_part)
	collapsed_path = "/".join(splitpath)

	return collapsed_path



nobody = None

def nobody_uid():
	"""Internal routine to get nobody's uid"""
	global nobody
	if nobody:
		return nobody
	try:
		import pwd
	except ImportError:
		return -1
	try:
		nobody = pwd.getpwnam('nobody')[2]
	except KeyError:
		nobody = 1 + max(x[2] for x in pwd.getpwall())
	return nobody


def executable(path):
	"""Test for executable file."""
	return os.access(path, os.X_OK)


class CGIHTTPRequestHandler(SimpleHTTPRequestHandler):

	"""Complete HTTP server with GET, HEAD and POST commands.

	GET and HEAD also support running CGI scripts.

	The POST command is *only* implemented for CGI scripts.

	"""

	# Determine platform specifics
	have_fork = hasattr(os, 'fork')

	# Make rfile unbuffered -- we need to read one line and then pass
	# the rest to a subprocess, so we can't use buffered input.
	rbufsize = 0

	def do_POST(self):
		"""Serve a POST request.

		This is only implemented for CGI scripts.

		"""

		if self.is_cgi():
			self.run_cgi()
		else:
			self.send_error(
				HTTPStatus.NOT_IMPLEMENTED,
				"Can only POST to CGI scripts")

	def send_head(self):
		"""Version of send_head that support CGI scripts"""
		if self.is_cgi():
			return self.run_cgi()
		else:
			return SimpleHTTPRequestHandler.send_head(self)

	def is_cgi(self):
		"""Test whether self.path corresponds to a CGI script.

		Returns True and updates the cgi_info attribute to the tuple
		(dir, rest) if self.path requires running a CGI script.
		Returns False otherwise.

		If any exception is raised, the caller should assume that
		self.path was rejected as invalid and act accordingly.

		The default implementation tests whether the normalized url
		path begins with one of the strings in self.cgi_directories
		(and the next character is a '/' or the end of the string).

		"""
		collapsed_path = _url_collapse_path(self.path)
		dir_sep = collapsed_path.find('/', 1)
		head, tail = collapsed_path[:dir_sep], collapsed_path[dir_sep+1:]
		if head in self.cgi_directories:
			self.cgi_info = head, tail
			return True
		return False


	cgi_directories = ['/cgi-bin', '/htbin']

	def is_executable(self, path):
		"""Test whether argument path is an executable file."""
		return executable(path)

	def is_python(self, path):
		"""Test whether argument path is a Python script."""
		head, tail = os.path.splitext(path)
		return tail.lower() in (".py", ".pyw")

	def run_cgi(self):
		"""Execute a CGI script."""
		dir, rest = self.cgi_info
		path = dir + '/' + rest
		i = path.find('/', len(dir)+1)
		while i >= 0:
			nextdir = path[:i]
			nextrest = path[i+1:]

			scriptdir = self.translate_path(nextdir)
			if os.path.isdir(scriptdir):
				dir, rest = nextdir, nextrest
				i = path.find('/', len(dir)+1)
			else:
				break

		# find an explicit query string, if present.
		rest, _, query = rest.partition('?')

		# dissect the part after the directory name into a script name &
		# a possible additional path, to be stored in PATH_INFO.
		i = rest.find('/')
		if i >= 0:
			script, rest = rest[:i], rest[i:]
		else:
			script, rest = rest, ''

		scriptname = dir + '/' + script
		scriptfile = self.translate_path(scriptname)
		if not os.path.exists(scriptfile):
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No such CGI script (%r)" % scriptname)
			return
		if not os.path.isfile(scriptfile):
			self.send_error(
				HTTPStatus.FORBIDDEN,
				"CGI script is not a plain file (%r)" % scriptname)
			return
		ispy = self.is_python(scriptname)
		if self.have_fork or not ispy:
			if not self.is_executable(scriptfile):
				self.send_error(
					HTTPStatus.FORBIDDEN,
					"CGI script is not executable (%r)" % scriptname)
				return

		# Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
		# XXX Much of the following could be prepared ahead of time!
		env = copy.deepcopy(os.environ)
		env['SERVER_SOFTWARE'] = self.version_string()
		env['SERVER_NAME'] = self.server.server_name
		env['GATEWAY_INTERFACE'] = 'CGI/1.1'
		env['SERVER_PROTOCOL'] = self.protocol_version
		env['SERVER_PORT'] = str(self.server.server_port)
		env['REQUEST_METHOD'] = self.command
		uqrest = urllib.parse.unquote(rest)
		env['PATH_INFO'] = uqrest
		env['PATH_TRANSLATED'] = self.translate_path(uqrest)
		env['SCRIPT_NAME'] = scriptname
		if query:
			env['QUERY_STRING'] = query
		env['REMOTE_ADDR'] = self.client_address[0]
		authorization = self.headers.get("authorization")
		if authorization:
			authorization = authorization.split()
			if len(authorization) == 2:
				import base64, binascii
				env['AUTH_TYPE'] = authorization[0]
				if authorization[0].lower() == "basic":
					try:
						authorization = authorization[1].encode('ascii')
						authorization = base64.decodebytes(authorization).\
										decode('ascii')
					except (binascii.Error, UnicodeError):
						pass
					else:
						authorization = authorization.split(':')
						if len(authorization) == 2:
							env['REMOTE_USER'] = authorization[0]
		# XXX REMOTE_IDENT
		if self.headers.get('content-type') is None:
			env['CONTENT_TYPE'] = self.headers.get_content_type()
		else:
			env['CONTENT_TYPE'] = self.headers['content-type']
		length = self.headers.get('content-length')
		if length:
			env['CONTENT_LENGTH'] = length
		referer = self.headers.get('referer')
		if referer:
			env['HTTP_REFERER'] = referer
		accept = []
		for line in self.headers.getallmatchingheaders('accept'):
			if line[:1] in "\t\n\r ":
				accept.append(line.strip())
			else:
				accept = accept + line[7:].split(',')
		env['HTTP_ACCEPT'] = ','.join(accept)
		ua = self.headers.get('user-agent')
		if ua:
			env['HTTP_USER_AGENT'] = ua
		co = filter(None, self.headers.get_all('cookie', []))
		cookie_str = ', '.join(co)
		if cookie_str:
			env['HTTP_COOKIE'] = cookie_str
		# XXX Other HTTP_* headers
		# Since we're setting the env in the parent, provide empty
		# values to override previously set values
		for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
				  'HTTP_USER_AGENT', 'HTTP_COOKIE', 'HTTP_REFERER'):
			env.setdefault(k, "")

		self.send_response(HTTPStatus.OK, "Script output follows")
		self.flush_headers()

		decoded_query = query.replace('+', ' ')

		if self.have_fork:
			# Unix -- fork as we should
			args = [script]
			if '=' not in decoded_query:
				args.append(decoded_query)
			nobody = nobody_uid()
			self.wfile.flush() # Always flush before forking
			pid = os.fork()
			if pid != 0:
				# Parent
				pid, sts = os.waitpid(pid, 0)
				# throw away additional data [see bug #427345]
				while select.select([self.rfile], [], [], 0)[0]:
					if not self.rfile.read(1):
						break
				if sts:
					self.log_error("CGI script exit status %#x", sts)
				return
			# Child
			try:
				try:
					os.setuid(nobody)
				except OSError:
					pass
				os.dup2(self.rfile.fileno(), 0)
				os.dup2(self.wfile.fileno(), 1)
				os.execve(scriptfile, args, env)
			except:
				self.server.handle_error(self.request, self.client_address)
				os._exit(127)

		else:
			# Non-Unix -- use subprocess
			cmdline = [scriptfile]
			if self.is_python(scriptfile):
				interp = sys.executable
				if interp.lower().endswith("w.exe"):
					# On Windows, use python.exe, not pythonw.exe
					interp = interp[:-5] + interp[-4:]
				cmdline = [interp, '-u'] + cmdline
			if '=' not in query:
				cmdline.append(query)
			self.log_message("command: %s", subprocess.list2cmdline(cmdline))
			try:
				nbytes = int(length)
			except (TypeError, ValueError):
				nbytes = 0
			p = subprocess.Popen(cmdline,
								 stdin=subprocess.PIPE,
								 stdout=subprocess.PIPE,
								 stderr=subprocess.PIPE,
								 env = env
								 )
			if self.command.lower() == "post" and nbytes > 0:
				data = self.rfile.read(nbytes)
			else:
				data = None
			# throw away additional data [see bug #427345]
			while select.select([self.rfile._sock], [], [], 0)[0]:
				if not self.rfile._sock.recv(1):
					break
			stdout, stderr = p.communicate(data)
			self.wfile.write(stdout)
			if stderr:
				self.log_error('%s', stderr)
			p.stderr.close()
			p.stdout.close()
			status = p.returncode
			if status:
				self.log_error("CGI script exit status %#x", status)
			else:
				self.log_message("CGI script exited OK")


def _get_best_family(*address):
	infos = socket.getaddrinfo(
		*address,
		type=socket.SOCK_STREAM,
		flags=socket.AI_PASSIVE,
	)
	family, type, proto, canonname, sockaddr = next(iter(infos))
	return family, sockaddr


import socket
def get_ip():
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.settimeout(0)
			try:
				# doesn't even have to be reachable
				s.connect(('10.255.255.255', 1))
				IP = s.getsockname()[0]
			except:
				try:
					if config.get_os()=="Android":
						IP = s.connect(("192.168.43.1",  1))
						IP = s.getsockname()[0]
						# Assigning this variable because Android does't return actual IP when hosting a hotspot
				except (socket.herror, OSError):
					IP = '127.0.0.1'
			finally:
				s.close()
			return IP


def test(HandlerClass=BaseHTTPRequestHandler,
		 ServerClass=ThreadingHTTPServer,
		 protocol="HTTP/1.0", port=8000, bind=None):
	"""Test the HTTP request handler class.

	This runs an HTTP server on port 8000 (or the port argument).

	"""

	global httpd
	if sys.version_info>(3,7,2): # BACKWARD COMPATIBILITY
		ServerClass.address_family, addr = _get_best_family(bind, port)
	else:
		addr =(bind if bind!=None else '', port)

	HandlerClass.protocol_version = protocol
	httpd = ServerClass(addr, HandlerClass)
	host, port = httpd.socket.getsockname()[:2]
	url_host = f'[{host}]' if ':' in host else host
	hostname = socket.gethostname()
	local_ip = config.IP if config.IP else get_ip()
	config.IP= local_ip

	print(
		f"Serving HTTP on {host} port {port} \n" #TODO: need to check since the output is "Serving HTTP on :: port 6969"
		f"(http://{url_host}:{port}/) ...\n" #TODO: need to check since the output is "(http://[::]:6969/) ..."
		f"Server is probably running on http://{config.address()}"

	)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print("\nKeyboard interrupt received, exiting.")
		if not reload:
			sys.exit(0)

	except OSError:
		print("\nOSError received, exiting.")
		if not reload:
			sys.exit(0)


class DualStackServer(ThreadingHTTPServer): # UNSUPPORTED IN PYTHON 3.7
	def server_bind(self):
		# suppress exception when protocol is IPv4
		with contextlib.suppress(Exception):
			self.socket.setsockopt(
				socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
		return super().server_bind()




if __name__ == '__main__':
	import argparse



	parser = argparse.ArgumentParser()
	parser.add_argument('--cgi', action='store_true',
					   help='Run as CGI Server')
	parser.add_argument('--bind', '-b', metavar='ADDRESS',
						help='Specify alternate bind address '
							 '[default: all interfaces]')
	parser.add_argument('--directory', '-d', default=config.get_default_dir(),
						help='Specify alternative directory '
						'[default:current directory]')
	parser.add_argument('port', action='store',
						default=config.port, type=int,
						nargs='?',
						help='Specify alternate port [default: 8000]')
	args = parser.parse_args()
	if args.directory == config.ftp_dir and not os.path.isdir(config.ftp_dir):
		print(config.ftp_dir, "not found!\nReseting directory to current directory")
		args.directory = "."
	if args.cgi:
		handler_class = CGIHTTPRequestHandler
	else:
		handler_class = partial(SimpleHTTPRequestHandler,
								directory=args.directory)
								
	config.port = args.port

	if not reload:
		if sys.version_info>(3,7,2):
			test(
			HandlerClass=handler_class,
			ServerClass=DualStackServer,
			port=args.port,
			bind=args.bind,
			)
		else: # BACKWARD COMPATIBILITY
			test(
			HandlerClass=handler_class,
			ServerClass=ThreadingHTTPServer,
			port=args.port,
			bind=args.bind,
			)

if reload == True:
	subprocess.call([sys.executable, config.MAIN_FILE, *sys.argv[1:]])
	sys.exit(0)
