from .data_types import Template
__all__ = [
	"directory_explorer_header",
	"global_script",
	"upload_form",
	"file_list_script",
	"video_page",
	"zip_script",
	"error_page",
	"theme_script",
	"video_page_script",
	"page_handler_script",
	"admin_page_script",
	"login_page",
	"style_css"

]


# ---------------------------x--------------------------------

# PAGE TEMPLATES
##############################################################


enc = "utf-8"


class config:
	dev_mode = False
	file_list = {}

pt_config = config()



def _get_template(path):
	if pt_config.dev_mode:
		with open(path, encoding=enc) as f:
			return f.read()

	return pt_config.file_list[path]

def get_template(path):
	return Template(_get_template(path))


def directory_explorer_header():
	return get_template("html_page.html")



def style_css():
	return _get_template("style_main.css")






def global_script():
	return get_template("script_global.js")

def assets_script():
	return get_template("script_main.js")

def file_list_script():
	return get_template("script_file_list.js")

def video_page_script():
	return get_template("script_video_player.js")

def page_handler_script():
	return get_template("script_page_handler.js")

def admin_page_script():
	return get_template("script_admin_page.js")

def error_page_script():
	return get_template("script_error_page.js")

def zip_page_script():
	return get_template("script_zip_page.js")




def upload_form():
	return _get_template("html_upload.html")

def zip_script():
	return get_template("html_zip_page.html")  # TODO: Move to Dynamic island

def error_page():
	return directory_explorer_header()  # TODO: add to PWA

def theme_script():
	return get_template("script_theme.js")

def login_page():
	return get_template("html_login.html")

def signup_page():
	return get_template("html_signup.html")

#directory_explorer_header()







pt_config.file_list["html_page.html"] = r"""
<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet'>
<title>${PY_PAGE_TITLE}</title>

<link rel="stylesheet" href="?style">
</head>

<body>
<script>
const public_url = "${PY_PUBLIC_URL}";
</script>


<style>
	#content_container {
		display: none; /* hide content until page is loaded */
	}
</style>


<noscript>
	<style>
		.jsonly {
			display: none !important
		}

		#content_container {
			display: block; /* making sure its visible */
		}

		#fm_page {
			display: block;
		}

		#content_list {
			/* making sure its visible */
			display: block;
		}
	</style>
</noscript>

<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.png" type="image/png">



<div id="popup-container"></div>

<div id='TopBar' class='top_bar'>

	<span id="dir-tree">${PY_DIR_TREE_NO_JS}</span>


	<button class="open-sidebar-btn" onclick="sidebar_control.toggleNavR()" style='float: right;'><span>
		<span class='nav-btn-text'>Menu</span> <span class="fa fa-thin fa-ellipsis-stroke-vertical">&vellip;</span></span>
	</button>

</div>

<div id="sidebar_bg"></div> <!-- trigger to close Sidebar-->



<div id="mySidebarR" class="sidebar sidebarR theme-tools">

	<span style='right:0; text-align:right;margin-right: 20px;' class="close-sidebar disable_selection"

		id="close-sidebarR" onclick = "sidebar_control.closeNavR()">&times;</span> <!-- × -->

	<div>
		<div id="preference_button" class="accordion accordion-button debug_only" onclick="appConfig.show_help_note()">Preference</div>
		<div class="member_only">
			<div id="user_panel_button" class="accordion accordion-button debug_only" onclick="appConfig.show_author_note()">User Panel</div>
			<div id="admin_button" class="accordion accordion-button admin_only" onclick="goto('./?admin')">Admin Panel</div>
			<div id="logout_button" class="accordion accordion-button" onclick="goto('./?logout')">Logout</div>
		</div>
		<div class="guest_only named_server">
			<div id="login_button" class="accordion accordion-button" onclick="goto('./?login')">Login</div>
			<div id="signup_button" class="accordion accordion-button" onclick="goto('./?signup')">Signup</div>
		</div>
	</div>


	<div class='sidebar-end'></div>



</div>


<div id="actions-btn" class="disable_selection jsonly" onclick="page.on_action_button()">
	<div id="actions-btn-text">More&nbsp;</div>
	<span class="fa fa-solid fa-plus" id="actions-btn-icon"><b>+</b></span>
	<span class="fa fa-duotone fa-spinner fa-spin" id="actions-loading-icon"><span class='spin'>⚉</span></span>
</div>
<div id="progress-island" class="disable_selection jsonly" onclick="progress_bars.show_list()">
	<span id="progress-uploads">Running Uploads
	<span id="progress-uploads-count">(0/0)</span></span>

	<br>

	<span id="progress-zips">Running Zips
	<span id="progress-zips-count">(0/0)</span></span>
</div>

<hr>

<div id="content_container">

	<!-- Contains all the files -->

	<div id="fm_page" class="page">
		<div id="content_list">

			<ul id="linkss">
				<!-- CONTENT LIST (NO JS) -->

				<!-- ${PY_NO_JS_FILE_LIST} -->


			</ul>
			<!-- ${PY_UPLOAD_FORM} -->
		</div>

		<div id="js-content_list" class="jsonly">
			<!-- CONTENT LIST (JS) -->
		</div>
	</div>

	<div id="error-page" class="page ${PY_ERROR_PAGE}">
		<script>var ERROR_PAGE = "${PY_ERROR_PAGE}"</script>
		<h1><u>Error response</u></h1>
		<p><u>Error code:</u> <span id="error_code">${code}</span></p>
		<p><u>Message:</u> <span id="error_message">${message}</span></p>
		<p><u>Error code explanation:</u> <span id="error_code2">${code}</span> - <span id="error_explain">${explain}</span></p>
		<hr>
		<center><img src = "https://http.cat/${code}" style="max-width: 95vw;" alt="Error Image"/></center>
	</div>


	<div id="video-page" class="page">
		<p><b>Watching:</b> <span id="player_title"></span></p>

		<h2 id="player-warning"></h2>

		<div id="container">
			<video controls crossorigin playsinline id="player">

				<source id="player_source" />
			</video>
		</div>

		<a id="video_dl_url"  download class='pagination'>Download</a>

	</div>

	<div id="zip-page" class="page">
		<h2>ZIPPING FOLDER</h2>
		<h3 id="zip-prog">Progress</h3>
		<h3 id="zip-perc"></h3>
	</div>

	<div id="admin_page" class="page">

		<h1 style="text-align: center;">Admin Page</h1>
		<hr>


		<div class="jsonly">

			<!-- check if update available -->

			<div>
				<p class="update_text" id="update_text">Checking for Update...</p>
				<!-- <div class="pagination jsonly" onclick="run_update()" id="run_update" style="display: none;">Run Update</div> -->
				<br><br>
			</div>

			<div>
				<table class="users_list">
					<tr>
						<th>Username</th>
						<th>Manager</th>
					</tr>
				</table>
			</div>



			<div class='pagination jsonly' onclick="admin_tools.request_reload()">RELOAD SERVER 🧹</div>
			<noscript><a href="/?reload" class='pagination'>RELOAD SERVER 🧹</a><br></noscript>
			<hr>

			<div class='pagination jsonly' onclick="admin_tools.request_shutdown()">Shut down 🔻</div>
		</div>

		<noscript>
			<h2>This page requires JS enabled</h2>
		</noscript>
	</div>
</div>



<script src="https://cdnjs.cloudflare.com/ajax/libs/plyr/3.7.0/plyr.min.js" crossorigin="anonymous" onerror="document.getElementById('player').style.maxWidth = '98vw'"></script>

<script src="/?global_script"></script>
<script src="/?asset_script"></script>

<script src="/?file_list_script"></script>
<script src="/?theme_script"></script>
<script src="/?video_page_script"></script>
<script src="/?admin_page_script"></script>
<script src="/?error_page_script"></script>
<script src="/?zip_page_script"></script>


<script src="/?page_handler_script"></script>


<!-- ASSET_SCRIPT will load at the end with all the classes defined -->



<link rel="stylesheet" href="https://raw.githack.com/RaSan147/pyrobox/main/assets/video.css" />

"""


pt_config.file_list["style_main.css"] = r"""
::-webkit-scrollbar-track {
	background: #222;
}

::-webkit-scrollbar {
	width: 7px;
	/*height: 7px;*/
	opacity: 0.3;
}

::-webkit-scrollbar:hover {
	opacity: 0.9;
}

::-webkit-scrollbar-thumb {
	background: #333;
	border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
	background: #666;
}

::-webkit-scrollbar-thumb:hover {
	background: #aaa;
}

.hidden {
	display: none !important;
}

.disabled {
	pointer-events: none;
	filter: grayscale(100%);
	cursor: not-allowed;
}


#content_list {
	/* making sure this don't get visible if js enabled */
	/* otherwise that part makes a weird flash */
	display: none;
}


body {
	position: relative;
	overflow-x: hidden;
	top: 50px; /* Height of navbar */
}

#content_container {
	min-height: 100vh;
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
	font-family: "Open Sans", sans-serif;
}


.center {
	text-align: center;
	margin: auto;
}

.disable_selection, .no_select {
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


.drag-file-list {
	width: 98%;
	max-height: 300px;
	overflow: auto;
	padding: 20px 3px;

	border: #005ab2 2px solid;
	border-radius: 5px;
}

.upload-file-item {
display: block;
border: 1px solid #ddd;
margin-top: -1px; /* Prevent double borders */
background-color: #8c8c8c5b;
padding: 12px;
text-decoration: none;
font-size: 18px;
color: white;
position: relative;
border-radius: 5px;

max-width: 100%;
}


.upload-file-item {
	table-layout: fixed;
	width: 100%;
	max-height: 300px;
	overflow: auto;
	padding: 20px 0;
	/* align-items: center; */
}

.upload-file-item tr {
	padding: 5px 0;
}

.upload-file-item td.ufname {
	width: 70%;
	text-align: left;
}

.upload-file-item td.ufsize {
	width: auto;
	font-size: .6em;
	font-weight: 600;
	color: #fff;
}

.upload-file-item td.ufsize span {
	background-color: #3d8be4;
	border-radius: 5px;
	padding: 3px;
}

.upload-file-item td.ufremove {
	width: 20px;
}

.upload-file-item td.ufremove span {
	background-color: #2a2a2a;
	border-radius: 5px;
	padding: 6px;
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

:root {
	--popup-bg: #292929;
	--popup-color: #e9f4ff;
	--popup-btn-bg: #313131;
	--popup-btn-bg-active: #005ab2;
	--popup-btn-border: 1px solid #006ad2;
}

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
	color: var(--popup-color);
	transition: all 400ms ease-in-out;
	background: var(--popup-bg);
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

.popup-btn {
	cursor: pointer;
	background: var(--popup-btn-bg);
	color: var(--popup-color);
	border: var(--popup-btn-border);
	border-radius: 6px;
}

.popup-btn:hover, .popup-btn:active {
	background: var(--popup-btn-bg-active);

}

.popup-close-btn {
	position: absolute;
	right: 20px;
	top: 20px;
	width: 30px;
	height: 30px;
	font-size: 25px;
	font-weight: 600;
	line-height: 30px;
	text-align: center;
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
	max-width: min(800px , 70%)
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
	background: #8c8c8c5b;
	width: calc(100% - 10px);
	padding: 5px;
	margin: 5px 0;
	text-align: left;
	cursor: pointer;
}

.menu_options:hover,
.menu_options:focus {
	background: #3f3ffa8d;

}

.menu_options.disabled {
	cursor: not-allowed;
	background: #8c8c8c5b;
	border: #222 solid 1px;
	opacity: 0.7;
}

.menu_options.disabled:hover {
	background: #8c8c8c5b;
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
	max-width: 90%;
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
	bottom: 70px;
	right: 0;
	max-width: 100%;
	height: auto;

	pointer-events: none;

}



.toast-body {
	max-height: 100px;
	width: max-content;
	max-width: 90%;

	overflow-y: auto;
	margin: 7px;
	padding: 10px;
	opacity: 0;
	overflow-wrap: anywhere;
	transform: translateY(100%);

	font-size: 1em;
	color: #fff;


	border-radius: 4px;
	transition:
		opacity 500ms,
		transform 500ms;
}

.toast-body.visible {
	transform: translateY(0);
	opacity: 1;
}




.update_text {
	font-size: 1.5em;
	padding: 5px;
	margin: 5px;
	border: solid 2px;
	border-radius: 4px;
}






























.top_bar {
	display: flex;
	background-color: #111;
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: max-content;
	transition: top 0.3s;
	font-size: 20px;
	z-index: 9;
	flex-direction: row;
	justify-content: space-between;
	align-items: center;

	padding: 3px 0;
	border-bottom: #006ad2 2px solid;
	box-shadow: 0 0 10px #006ad2;
}


.top_bar.inactive {
	display: none;
	transition: none;
}

.top_bar #app_name_container {
	padding: 10px 0;
	float: left;
	font-size: 20px;
	font-family: sans-serif;
}


#dir-tree {
	display: flex;
	overflow-x: auto;
	overflow-y: hidden;
	white-space: nowrap;
	word-wrap: break-word;
	width: calc(100% - 110px);
	font-size: large;
	border: #075baf 2px solid;
	border-radius: 5px;
	background-color: #0d29379f;
	padding: 0 5px;
	height: 34px;
	align-items: center;
}

#dir-tree::-webkit-scrollbar {
	display: none;
}


.dir_arrow {
	position: relative;
	padding: 4px;
	color: #e8e6e3;
	font-size: 12px;
}


.dir_turns {
	padding: 4px;
	border-radius: 5px;
}

.dir_turns:hover {
	background-color: #90cdeb82;
	color: #ffffff;
}


















:root {
	--sb-width: 300px;
}
.sidebar {
	display: block;
	opacity: 0.8;
	height: 100%;
	width: var(--sb-width);
	position: fixed;
	z-index: 5;
	top: 0;
	background-color: #111;
	overflow-x: hidden;
	overflow-y: scroll;
	padding-top: 60px;
}

#sidebar_bg {
	display: none;
	position: fixed;
	z-index: 4;
	padding-top: inherit;
	left: 0;
	top: 0;
	width: 100%;
	height: 100%;
	overflow: auto;
}

#mySidebarL {
	direction: rtl;
}

.sidebarR {
	right: calc(var(--sb-width) * -1);;
}


.mySidebar-inactive {
	transition: all 0.3s;
}

.mySidebar-active{
	display: block;
	opacity: 1;
	transition: all 0.3s;
}

.mySidebar-active.sidebarR{
	right: 0;
}



.sidebar-content {
	direction: ltr;
}


.sidebar-end {
	position: relative;
	max-height: 80%;
	min-height: 180px;
	opacity: 0;
}



.sidebar a:hover {
	color: #f1f1f1;
	background-color: #444;
}

.sidebar .close-sidebar {
	position: absolute;
	top: 0;
	right: 20px;
	font-size: 40px;
	width: 80%;
	height: 28px;
	border: none;
	margin-top: -5px;
	color: white;
	cursor: pointer;
}

.sidebar .close-sidebar:hover {
	background-color: inherit;
}




/* change value on media size */
@media screen and (max-width: 450px) {
	:root {
		--sb-width: 80%;
	}
}

@media screen and (max-width: 340px) {
	:root {
		--sb-width: 100vw;
	}

	.sidebar {
		overflow: auto;
	}
}




.open-sidebar-btn {
	background-color: #2e2e2e;
	font-size: 20px;
	cursor: pointer;
	color: #fff;
	padding: 5px 10px;
	border: none;
	margin: 0 3px 0 3px;
	border-radius: 7px;
}

.open-sidebar-btn:hover {
	background-color: #444;
}


@media screen and (max-width: 620px) {
	.nav-btn-text {
		display: none;
	}
	#dir-tree {
		width: calc(100% - 50px);
	}
}

@media screen and (max-height: 450px) {
	.sidebar a {
		font-size: 18px;
	}

	.sidebar button {
		font-size: 18px;
	}
}





  /* ************************************ */
 /* **        Action Btn + Island     ** */
/* ************************************ */

#progress-island {
	display: none;
	position: fixed;
	z-index: 6;
	right: 65px;
	bottom: 20px;
	width: calc(98% - 65px);
	max-width: 300px;
	height: 50px;
	border-radius: 6px;
	background-color: #000000a3;
	color: #fff;



	font-size: small;

	box-shadow: 0px 5px 5px -3px var(--popup-btn-bg-active);
}

#progress-island span {
	margin: 5px;
}


.progress_bar {
	width: 97%;
	text-align: left;

	padding: 5px 10px;

	border-style: solid;
border-width: 2px 1px; /* 5px top and bottom, 20px on the sides */
border-radius: 4px;
box-shadow: 0px 5px 5px -3px var(--popup-btn-bg-active);
}

.progress_bar_heading {
	display: flex;
	flex-direction: row;
	justify-content: space-between;
	align-items: center;

	border: 1px solid white;
	border-radius: 3px;
	padding: 1px;

}

.progress_bar_heading_text {
	font-size: 1em;
}
.progress_bar_status {
	font-size: 1.2em;
}

.progress_bar_status_text {
	font-size: 1em;
}

.progress_bar_progress {
	height: 3px;
	width: 98%;
	border-radius: 2px;
	margin: 5px;
	color: var(--popup-btn-bg-active);
}

.progress_bar_cancel {
	font-size: .9em;
	color: rgb(196, 233, 255);
	cursor: pointer;
	padding: 2px 3px;
	border-radius: 3px;
	border: #00b7ff 1px solid;
}





#actions-btn {
	/* display: flex; */
	display: none;
	position: fixed;
	color: var(--popup-color);
	background-color: var(--popup-btn-bg);
	min-width: 50px;
	min-height: 50px;
	line-height: 1.8;
	font-size: 25px;
	font-weight: 700;
	right: 10px;
	bottom: 20px;
	cursor: pointer;
	z-index: 6;
	border-radius: 50%;

	transition: all 0.3s ease-in-out;
	box-shadow: 0 2px 3px 1px #3d8be4;


	flex-direction: row;
	flex-wrap: nowrap;
	justify-content: center;
	align-items: center;
}

#actions-btn:hover, #actions-btn:active {
	background-color: var(--popup-btn-bg-active);
	color: var(--theme-color-text2);
	box-shadow: 0 2px 3px 1px #0c2de6;
}

#actions-btn:active {
	transition: all .5s ease-in-out;
	transform: scale(0.3);
}

#actions-btn-text {
	display: none;
}

@media screen and (min-width: 700px) {
	#actions-btn-text {
		display: block;
	}
	#actions-btn {
		border-radius: 20px;
		padding: 0 10px;
	}
}

#actions-loading-icon {
	display: block;
}


.spin {
	-webkit-animation-name: spin;
	-webkit-animation-duration: 4000ms;
	-webkit-animation-iteration-count: infinite;
	-webkit-animation-timing-function: linear;
	-moz-animation-name: spin;
	-moz-animation-duration: 4000ms;
	-moz-animation-iteration-count: infinite;
	-moz-animation-timing-function: linear;
	-ms-animation-name: spin;
	-ms-animation-duration: 4000ms;
	-ms-animation-iteration-count: infinite;
	-ms-animation-timing-function: linear;

	animation-name: spin;
	animation-duration: 4000ms;
	animation-iteration-count: infinite;
	animation-timing-function: linear;
}

@-moz-keyframes spin {
    from { -moz-transform: rotate(0deg); }
    to { -moz-transform: rotate(360deg); }
}
@-webkit-keyframes spin {
    from { -webkit-transform: rotate(0deg); }
    to { -webkit-transform: rotate(360deg); }
}
@keyframes spin {
    from {transform:rotate(0deg);}
    to {transform:rotate(360deg);}
}






  /* ********************** */
 /* Make Dir input element */
/* ********************** */

input#folder-name {
	font-size: large;
	border-radius: 7px;
	padding: 3px;
}



.dir_item {
	display: inline;
}



.all_link, #linkss a {
	display: block;
	white-space: wrap;
	overflow-wrap: anywhere;
	position: relative;
	border-radius: 5px;
	padding: 3px 0;
}

.dir_item:active .link_name {
	color: red;
}

.dir_item:active .all_link, .dir_item:hover .all_link , #linkss a:hover {
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






.accordion {
	background-color: var(--button-background-color);
	color: var(--theme-color-text);
	cursor: pointer;
	padding: 13px;
	width: 85%;
	border: none;
	text-align: left;
	outline: none;
	font-size: 15px;
	transition: all 0.4s;
	border-radius: 3px;
	margin: 0 auto 10px auto;
	box-shadow: 0 2px 3px 1px #3d8be4;
}

.accordion-button {
	text-align: center;
	font-size: larger;
	font-weight: bold;
	padding: 13px 6px;
}

.accordion>.tron-switch {
	margin-right: 5px;
}

.accordion-active,
.accordion:hover {
	background-color: var(--button-background-color-focused);
	color: var(--theme-color-text2);
	box-shadow: 0 2px 3px 1px #d8d8d8;
}

.accordion-panel {
	padding: 0 10px 10px;
	display: none;
	background-color: inherit;
	color: #fff;
	overflow: hidden;
	transition: all 0.8s;
}

.accordion-panel-heading {
	line-height: 40px;
}


















  /* ************************************ */
 /* **          Page segments         ** */
/* ************************************ */

.page {
	display: none;
}

.page.active {
	display: block;
}



  /* ************************************ */
 /* **           All Page             ** */
/* ************************************ */


.admin_only {
	display: none;
}

.member_only {
	display: none;
}

.guest_only {
	display: none;
}

.named_server {
	display: none;
}

.debug_only {
	display: none;
}



  /* ************************************ */
 /* **           Admin Page           ** */
/* ************************************ */

.users_list {
	/* TABLE */
	width: 100%;
	border-collapse: collapse;
	border: 1px solid #ddd;
	font-size: 18px;
}

.users_list tr:nth-child(even) {
	background-color: #464646;
}

.users_list tr:hover {
	background-color: #202020;
}

.users_list th {
	padding-top: 12px;
	padding-bottom: 12px;
	text-align: left;
	color: white;
}

.users_list td {
	padding: 12px;
}

"""


pt_config.file_list["script_global.js"] = r"""
const DEBUGGING = false;



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

"""



pt_config.file_list["script_main.js"] = r"""



class ContextMenu {
	constructor() {
		this.old_name = null;
	}
	async on_result(self) {
		var data = false;
		if (self.status == 200) {
			data = safeJSONParse(self.responseText, ["head", "body", "script"], 5000);
		}
		popup_msg.close()
		await tools.sleep(300)
		if (data) {
			popup_msg.createPopup(data["head"], data["body"]);
			if (data["script"]) {
				let script = document.createElement("script");
				script.innerHTML = data["script"];
				document.body.appendChild(script);
			}
		} else {
			popup_msg.createPopup("Failed", "Server didn't respond<br>response: " + self.status);
		}
		popup_msg.open_popup()
	}
	menu_click(action, link, more_data = null, callback = null) {
		let that = this
		popup_msg.close()

		let url = ".?"+action;
		let xhr = new XMLHttpRequest();
		xhr.open("POST", url);
		xhr.onreadystatechange = function() {
			if (this.readyState === 4) {
				that.on_result(this)
				if (callback) {
					callback()
				}
			}
		};
		const formData = new FormData();
		formData.append("post-type", action);
		formData.append("name", link);
		formData.append("data", more_data)
		xhr.send(formData);
	}
	rename_data() {
		let new_name = byId("input_rename").value;

		this.menu_click("rename", this.old_name, new_name, null, () => {page.refresh_dir()});
		// popup_msg.createPopup("Done!", "New name: "+new_name)
		// popup_msg.open_popup()
	}
	async rename(link, name) {
		await popup_msg.close()
		popup_msg.createPopup("Rename",
			"Enter new name: <input id='input_rename' type='text'><br><br><div class='pagination center' onclick='context_menu.rename_data()'>Change!</div>"
			);
		console.log(popup_msg.content)
		popup_msg.open_popup()
		this.old_name = link;
		byId("input_rename").value = name;
		byId("input_rename").focus()
	}
	show_menus(file, name, type) {
		let that = this;
		let menu = createElement("div")


		const refresh = () => {
			page.refresh_dir()
		}

		let new_tab = createElement("div")
			new_tab.innerText = "↗️" + " New tab"
			new_tab.className = "disable_selection popup-btn menu_options"
			new_tab.onclick = function() {
				window.open(file, '_blank');
				popup_msg.close()
			}
			menu.appendChild(new_tab)
		if (type != "folder") {
			let download = createElement("div")
			download.innerText = "📥" + " Download"
			download.className = "disable_selection popup-btn menu_options"
			download.onclick = function() {
				tools.download(file, name);
				popup_msg.close()
			}
			if(user.permissions.DOWNLOAD){
				menu.appendChild(download)
			}
		}
		if (type == "folder") {
			let dl_zip = createElement("div")
			dl_zip.innerText = "📦" + " Download as Zip"
			dl_zip.className = "disable_selection popup-btn menu_options"
			dl_zip.onclick = function() {
				popup_msg.close()
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			}
			if(user.permissions.ZIP){
				menu.appendChild(dl_zip)
			}
		}

		let copy = createElement("div")
		copy.innerText = "📋" + " Copy link"
		copy.className = "disable_selection popup-btn menu_options"
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

		let rename = createElement("div")
		rename.innerText = "✏️" + " Rename"
		rename.className = "disable_selection popup-btn menu_options"
		rename.onclick = function() {
			that.rename(file, name)
		}

		if (user.permissions.MODIFY) {
			menu.appendChild(rename)
		}

		let del = createElement("div")
		del.innerText = "🗑️" + " Delete"
		del.className = "disable_selection popup-btn menu_options"
		var xxx = 'F'
		if (type == "folder") {
			xxx = 'D'
		}
		del.onclick = function() {
			that.menu_click('del-f', file, null, refresh);
		};

		if (user.permissions.DELETE) {
			menu.appendChild(del)
		}

		let del_P = createElement("div")
		del_P.innerText = "🔥" + " Delete permanently"
		del_P.className = "disable_selection popup-btn menu_options"


		del_P.onclick = () => {
			r_u_sure({y:()=>{
				that.menu_click('del-p', file, null, refresh);
			}, head:"Are you sure?", body:"This can't be undone!!!", y_msg:"Continue", n_msg:"Cancel"})
		}

		if (user.permissions.DELETE) {
			menu.appendChild(del_P)
		}

		let property = createElement("div")
		property.innerText = "📅" + " Properties"
		property.className = "disable_selection popup-btn menu_options"
		property.onclick = function() {
			that.menu_click('info', file);
		};

		if (user.permissions.VIEW) {
			menu.appendChild(property)
		}

		popup_msg.createPopup("Menu", menu)
		popup_msg.open_popup()
	}
	create_folder() {
		let folder_name = byId('folder-name').value;
		this.menu_click('new_folder', folder_name, null, () => {page.refresh_dir()});
	}
}
var context_menu = new ContextMenu()
//context_menu.show_menus("next", "video")

function show_response(url, add_reload_btn = true) {
	let xhr = new XMLHttpRequest();
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


function insertAfter(newNode, existingNode) {
	existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
}

function fmbytes(B) {
	'Return the given bytes as a file manager friendly KB, MB, GB, or TB string'
	let KB = 1024,
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




class ProgressBars {
	constructor() {
		this.last_index = 1
		this.bars = {}
		/* Data Structure
		{index: {
			type: "upload", or "zip"
			status: "waiting" | "running" | "done" | "error"
			form_id: 0, // UploadManager.uploaders[form_id]
			persent: 0,
			source_dir: "", // location from where the file is being uploaded
			status_text: "", // status text
			status_color: "", // status color for the text
		}, ...} */
		this.bar_elements = {}

		this.island_bar = byId("progress-island")
		this.island_up_text = byId("progress-uploads")
		this.island_up_count = byId("progress-uploads-count")

		this.island_zip_text = byId("progress-zips")
		this.island_zip_count = byId("progress-zips-count")
	}

	new(type, id, source_dir) {
		let that = this;
		let index = this.last_index;
		this.last_index += 1;

		let bar = {
			type: type,
			form_id: id,
			percent: 0,
			source_dir: source_dir,
			status_text: "",
			status_color: "",
		}
		this.bars[index] = bar
		this.bar_elements[index] = null // will be set later


		let bar_element = createElement("div")
		bar_element.className = "progress_bar"
		bar_element.id = "progress_bar_" + index

		let bar_head = createElement("div")
		bar_head.className = "progress_bar_heading"

		let bar_head_text = createElement("div")
		bar_head_text.className ="progress_bar_heading_text"
		if(type=="upload"){
			bar_head_text.innerText = "Uploading"
		} else if(type=="zip"){
			bar_head_text.innerText = "Zipping"
		}
		bar_head_text.style.float ="left"
		bar_head.appendChild(bar_head_text)

		let bar_status = createElement("div")
		bar_status.className = "progress_bar_status"
		bar_status.innerText = "0%"
		bar_status.style.float = "right"
		bar_head.appendChild(bar_status)
		bar_element.appendChild(bar_head)


		let status_label = createElement("span")
		status_label.style.font_size = ".6em"
		status_label.innerText = "Status: "
		bar_element.appendChild(status_label)

		let bar_status_text = createElement("span")
		bar_status_text.className = "progress_bar_status_text"
		bar_status_text.innerText = "Waiting"
		bar_element.appendChild(bar_status_text)

		let bar_progress = createElement("progress")
		bar_progress.className = "progress_bar_progress"
		bar_progress.value = 0
		bar_progress.max = 100
		bar_element.appendChild(bar_progress)

		bar_element.appendChild(createElement("br"))

		let bar_cancel = createElement("span")
		bar_cancel.className = "progress_bar_cancel"
		bar_cancel.innerHTML = "&#9888; Delete Task"
		bar_cancel.onclick = function(e){
			e.stopPropagation() // stop the click event from propagating to the bar element
			if (type == "upload") {
				upload_man.remove(id)
			} else if (type == "zip") {
				zip_man.cancel(id)
			}

			that.remove(index)
		}
		bar_element.appendChild(bar_cancel)

		bar_element.onclick = ()=>{
			if(type=="upload") {
				upload_man.show(id)
			} else if(type=="zip") {
				zip_man.show(id)
			}
		}


		this.bar_elements[index] = bar_element

		return index

	}


	update_island() {
		let up_count = 0
		let up_done_count = 0
		let zip_count = 0
		let zip_done_count = 0
		for (let index in this.bars) {
			let bar = this.bars[index]
			if (bar.type == "upload") {
				up_count += 1;
				if (bar.status == "done") {
					up_done_count += 1;
				}
			} else if (bar.type == "zip") {
				zip_count += 1;
				if (bar.status == "done") {
					zip_done_count += 1;
				}
			}
		}

		this.island_bar.style.display = "block"
		if (!(up_count||zip_count)){
			this.island_bar.style.display = "None"
			return
		}


		if (up_count){
			this.island_up_text.style.display = "block"
			this.island_up_count.innerText = "(" + up_done_count + '/' + up_count + ')'
		} else {
			this.island_up_text.style.display = "none"
		}

		if (zip_count){
			this.island_zip_text.style.display = "block"
			this.island_zip_count.innerText = "(" + zip_done_count + '/' + zip_count + ')'
		} else {
			this.island_zip_text.style.display = "none"
		}
	}


	update(index, datas={}) {
		let bar = this.bars[index]
		for (let key in datas) {
			bar[key] = datas[key]
		}
		this.update_bar(index)
	}

	update_bar(index){
		let bar = this.bars[index]
		let bar_element = this.bar_elements[index]
		let type = bar.type



		let bar_head_text = bar_element.getElementsByClassName("progress_bar_heading_text")[0]
		if(type=="upload"){
			bar_head_text.innerText = "Uploading"
		} else if(type=="zip"){
			bar_head_text.innerText = "Zipping"
		}

		let bar_status = bar_element.getElementsByClassName("progress_bar_status")[0]
		bar_status.className = "progress_bar_status"
		bar_status.innerText = bar.percent + "%"

		let bar_status_text = bar_element.getElementsByClassName("progress_bar_status_text")[0]
		bar_status_text.innerText = bar.status_text || "Waiting"
		bar_status_text.style.color = bar.status_color || "white"



		let bar_progress = bar_element.getElementsByClassName("progress_bar_progress")[0]
		bar_progress.value = bar.percent

		this.update_island()
	}

	show_list() {
		let list = createElement("div")
		list.className = "progress_bar_list"

		let heading = createElement("h3")
		heading.innerText = "Do not close this tab while tasks are running"
		list.appendChild(heading)
		list.appendChild(createElement("hr"))


		for (let index in this.bars) {
			let bar = this.bars[index]
			let bar_element = this.bar_elements[index]
			list.appendChild(bar_element)
		}

		popup_msg.createPopup("Running Tasks", list)

		popup_msg.open_popup()
	}

	remove(index) {
		// check if the index exists
		if (!(index in this.bars)) {
			return // to avoid recursion
		}

		delete this.bars[index] // remove the id 1st
		let bar_element = this.bar_elements[index]
		bar_element.remove() // remove the element from the DOM
		delete this.bar_elements[index] // remove the element from the list

		toaster.toast("Task removed")
		this.update_island()
	}
}

const progress_bars = new ProgressBars()
progress_bars.update_island()














class User {
	constructor(){
		this.user = null;
		this.token = null;
		this.permissions_code = null;
		this.permissions = null;

		this.all_permissions = [
			'VIEW',
			'DOWNLOAD',
			'MODIFY',
			'DELETE',
			'UPLOAD',
			'ZIP',
			'ADMIN',
			'MEMBER',
		];
	}

	get_user(){
		this.user = tools.getCookie("user");
		this.token = tools.getCookie("token");
		this.permissions_code = tools.getCookie("permissions") || 0;

		this.permissions = {
			// NOPERMISSIONS: false is not needed since its handled by the server
			'VIEW': false,
			'DOWNLOAD': false,
			'MODIFY': false,
			'DELETE': false,
			'UPLOAD': false,
			'ZIP': false,
			'ADMIN': false,
			'MEMBER': false,
		};
		this.extract_permissions();
	}

	extract_permissions(){
		// this function extracts the permissions from the permissions_code
		let permissions = this.all_permissions;
		this.permissions = {}
		permissions.forEach((permission, i) => {
			this.permissions[permission] = this.permissions_code >> i & 1;
		}, this);
		// if none of permission is true, add nopermission to the permissions
		if(!Object.values(this.permissions).some(x => !!x)){
			this.permissions['NOPERMISSION'] = true;
		} else {
			this.permissions['NOPERMISSION'] = false;
		}

		return this.permissions;


	}

	pack_permissions(){
		// this function packs the permissions into permissions_code
		let permissions = this.all_permissions;

		this.permissions_code = 0;
		permissions.forEach((permission, i) => {
			this.permissions_code |= this.permissions[permission] << i;
		}, this);

		return this.permissions_code;
	}

}

const user = new User();
user.get_user();




// /////////////////////////////
//    Show Admin Only Stuffs  //
// /////////////////////////////

{
	if(user.permissions.ADMIN){
		let css = document.createElement("style");
		css.innerHTML = `
		.admin_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	}

	if(user.permissions.MEMBER){
		let css = document.createElement("style");
		css.innerHTML = `
		.member_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	} else {
		let css = document.createElement("style");
		css.innerHTML = `
		.guest_only {
			display: none;
		}
		`;
		document.body.appendChild(css);
	}

	if (config.allow_Debugging) {
		let css = document.createElement("style");
		css.innerHTML = `
		.debug_only {
			display: block;
		}
		`;
		document.body.appendChild(css);
	}
}
"""


pt_config.file_list["script_file_list.js"] = r"""
var r_li = [] // ${PY_LINK_LIST};
var f_li = [] // ${PY_FILE_LIST};
var s_li = [] // ${PY_FILE_SIZE};


function clear_file_list() {
	// clear previous data
	tools.del_child("linkss");
	tools.del_child("js-content_list")
}


class FM_Page{
	constructor(){
		this.type = "dir"

		this.my_part = document.getElementById("fm_page")

	}

	on_action_button(){
		// show add folder, sort, etc
		fm.show_more_menu()
	}

	async initialize(lazyload=false){
		if (!lazyload){
			page.clear();
		}

		page.set_title("File Manager")
		page.set_actions_button_text("New&nbsp;")
		page.show_actions_button()

		if (user.permissions.NOPERMISSION || !user.permissions.VIEW){
			page.set_title("No Permission")

			const container = byId("js-content_list")
			const warning = createElement("h2")
			warning.innerText = "You don't have permission to view this page"
			container.appendChild(warning)

			return
		}

		var folder_data = await fetch(tools.add_query_here("folder_data"))
								.then(response => response.json())
								.catch(error => {
									console.error('There has been a problem with your fetch operation:', error); // TODO: Show error in page
								});

		if (!folder_data || !folder_data["status"] || folder_data.status == "error"){
			console.error("Error getting folder data") // TODO: Show error in page
			return
		}

		r_li = folder_data.type_list
		f_li = folder_data.file_list
		s_li = folder_data.size_list

		var title = folder_data.title

		page.set_title(title)


		show_file_list();
	}

	hide(){
		this.my_part.classList.remove("active");
	}

	show(){
		this.my_part.classList.add("active");
	}

	clear(){
		tools.del_child("linkss");
	}

}

const fm_page = new FM_Page();


class UploadManager {
	constructor() {
		let that = this;
		this.last_index = 1
		this.uploaders = {}
		this.requests = {}
		this.status = {}
		/* Data Structure
		{index: form_element, ...}
		*/

		var form = null;
		let file_list = byId("content_container")
		this.drag_pop_open = false;

		file_list.ondragover = (event)=>{
			event.preventDefault(); //preventing from default behaviour
			if(that.drag_pop_open){
				return;
			}
			that.drag_pop_open = true;

			form = upload_man.new()
			popup_msg.createPopup("Upload Files", form, true, onclose=()=>{
				that.drag_pop_open = false;
			})
			popup_msg.open_popup();

		};

			//If user leave dragged File from DropArea
		file_list.ondragleave = (event)=>{
			event.preventDefault(); //preventing from default behavior
			// form.remove();
		};

			//If user drop File on DropArea
		file_list.ondrop = (event)=>{
			event.preventDefault(); //preventing from default behavior
		};
	}

	new() {
		//selecting all required elements
		let that = this;
		let index = this.last_index;
		this.last_index += 1;

		let Form = createElement("form")
		Form.id = "uploader-" + index
		Form.className = "jsonly"
		Form.method = "post"
		Form.action = tools.full_path("?upload") // the upload url, to use later from different pages
		Form.enctype = "multipart/form-data"

		let center = createElement("center")
		// centering the form


		let post_type = createElement("input")
		post_type.type = "hidden";
		post_type.name = "post-type";
		post_type.value = "upload";
		center.appendChild(post_type)


		let pass_header = createElement("span")
		pass_header.className = "upload-pass";
		pass_header.innerText = "Password:  ";
		center.appendChild(pass_header)

		let pass_input = createElement("input")
		pass_input.type = "password";
		pass_input.name = "password";
		pass_input.placeholder = "Password";
		pass_input.label = "Password";
		pass_input.className = "upload-pass-box";
		center.appendChild(pass_input)


		let up_files = createElement("input")
		up_files.type = "file";
		up_files.name = "file";
		up_files.multiple = true
		up_files.hidden = true;
		up_files.onchange = (e)=>{
			// USING THE BROWSE BUTTON
			let f = e.target.files; // this.files = [file1, file2,...];
			addFiles(f);
		};
		center.appendChild(up_files)


		center.appendChild(createElement("br"))
		center.appendChild(createElement("br"))

		let uploader_box = createElement("div")
		uploader_box.className = "upload-box";

			let uploader_dragArea = createElement("div")
			uploader_dragArea.className = "drag-area";
			uploader_dragArea.id = "drag-area";

			let up_icon = createElement("div")
			up_icon.className = "drag-icon";
			up_icon.innerText = "⬆️";
			uploader_dragArea.appendChild(up_icon)

			let up_text = createElement("header")
			up_text.innerText = "Drag & Drop to Upload File";
			uploader_dragArea.appendChild(up_text)

			let or_text = createElement("span")
			or_text.innerText = "OR"
			uploader_dragArea.appendChild(or_text)

			let up_button = createElement("button")
			up_button.type = "button";
			up_button.innerText = "Browse File";
			up_button.className = "drag-browse";
			up_button.onclick = (e)=>{
				e.preventDefault();
				up_files.click(); //if user click on the button then the input also clicked
			}
			uploader_dragArea.appendChild(up_button)

			uploader_dragArea.ondragover = (event)=>{
				event.preventDefault(); //preventing from default behavior
				uploader_dragArea.classList.add("active");
				up_text.innerText = "Release to Upload File";
			};

			//If user leave dragged File from DropArea
			uploader_dragArea.ondragleave = ()=>{
				uploader_dragArea.classList.remove("active");
				up_text.innerText = "Drag & Drop to Upload File";
			};

			//If user drop File on DropArea
			uploader_dragArea.ondrop = (event)=>{
				event.preventDefault(); //preventing from default behavior
				//getting user select file and [0] this means if user select multiple files then we'll select only the first one
				uploader_dragArea.classList.remove("active");
				up_text.innerText = "Drag & Drop to Upload File";

				addFiles(event.dataTransfer.files);
				// uploader_showFiles(); //calling function
			};

		uploader_box.appendChild(uploader_dragArea)
		center.appendChild(uploader_box)


		Form.appendChild(center)

		let uploader_file_container = createElement("div")
		// uploader_file_container.style.display = "contents";
		uploader_file_container.style.display = "none";

		let uploader_file_display = createElement("div")
		uploader_file_display.className = "drag-file-list";

		let uploader_file_display_title = createElement("h2")
		uploader_file_display_title.innerText = "Selected Files"
		uploader_file_display_title.className = "has-selected-files";
		uploader_file_display_title.style.textAlign = "center";
		uploader_file_container.appendChild(uploader_file_display_title)
		uploader_file_container.appendChild(uploader_file_display)



		Form.appendChild(uploader_file_container)

		Form.appendChild(createElement("br"))
		let center2 = createElement("center")
		let submit_button = createElement("button")
		submit_button.type = "submit";
		submit_button.innerText = "➾ Upload";
		submit_button.className = "drag-browse upload-button";

		center2.appendChild(submit_button)

		center2.appendChild(createElement("br"))
		center2.appendChild(createElement("br"))

		let upload_pop_status_label = createElement("span")
		upload_pop_status_label.innerText = "Status: ";
		let upload_pop_status = createElement("span")
		upload_pop_status.className = "upload-pop-status";
		upload_pop_status.innerText = "Waiting";
		upload_pop_status_label.appendChild(upload_pop_status)
		upload_pop_status_label.style.display = "none";
		center2.appendChild(upload_pop_status_label)

		Form.appendChild(center2)

		let prog_id = null;
		let request = null;
		Form["prog_id"] = null; // This is used to update the progress bar

		Form.onsubmit = (e) => {
			e.preventDefault();

			if(that.status[index]){
				that.cancel(index);
				show_status("Upload cancelled");
				return;
			}

			if(selected_files.files.length == 0){
				toaster.toast("No files selected");
				return;
			}

			that.status[index] = true; // The user is uploading

			request = request || new XMLHttpRequest();
			that.requests[index] = request;
			that.uploaders[index] = Form; // Save the form for later use
			// Unless the user is uploading, this won't be saved


			submit_button.innerText = "⏹️ Cancel";

			popup_msg.close();

			up_files.files = selected_files.files; // Assign the updates list


			const formData = new FormData(e.target);

			prog_id = prog_id || progress_bars.new('upload', index, window.location.href); // Create a new progress bar if not already created
			Form.prog_id = prog_id; // Save the progress bar id for later use



			var prog = 0,
			msg = "",
			color = "green",
			upload_status = "waiting";


			progress_bars.update(prog_id, {
						"status_text": "Waiting",
						"status_color": color,
						"status": "waiting",
						"percent": 0});


			// const filenames = formData.getAll('files').map(v => v.name).join(', ')

			request.open(e.target.method, e.target.action);
			request.timeout = 60 * 1000;
			request.onreadystatechange = () => {
				if (request.readyState === XMLHttpRequest.DONE) {
					msg = `${request.status}: ${request.statusText}`;
					upload_status = "error";
					color = "red";
					prog = 0;
					if (request.status === 401){
						msg = 'Incorrect password';
					} else if (request.status == 503) {
						msg = 'Upload is disabled';
					} else if (request.status === 0) {
						msg = 'Connection failed (Possible cause: Incorrect password or Upload disabled)';
					} else if (request.status === 204 || request.status === 200) {
						msg = 'Success';
						color = "green";
						prog = 100;
						upload_status = "done";

						page.refresh_dir(); // refresh the page if it is a dir page
					}


					progress_bars.update(prog_id, {
						"status_text": msg,
						"status_color": color,
						"status": upload_status,
						"percent": prog});

					submit_button.innerText = "➾ Re-upload";
					if (!that.status[index]){
						return; // needs to check this.status[index] because the user might have cancelled the upload but its still called. On cancel already a toast is shown
					}
					show_status(msg);

					if (upload_status === "error") {
						msg = "Upload Failed";
					} else {
						msg = "Upload Complete";
					}
					toaster.toast(msg, 3000, color);

					that.status[index] = false;

				}
			}
			request.upload.onprogress = e => {
				prog = Math.floor(100*e.loaded/e.total);
				if(e.loaded === e.total){
					msg ='Saving...';
					show_status(msg);
				}else{
					msg = `Progress`;
					show_status(msg + " " + prog + "%");
				}


				progress_bars.update(prog_id, {
						"status_text": msg,
						"status_color": "green",
						"status": "running",
						"percent": prog});
			}
			request.send(formData);
		}


		let selected_files = new DataTransfer(); //this is a global variable and we'll use it inside multiple functions



		/**
		 * Displays a status message and optionally hides it.
		 * @param {string} msg - The message to display.
		 * @param {boolean} [hide=false] - Whether to hide the status message or not.
		 */
		function show_status(msg, hide=false){
			if(hide){
				upload_pop_status_label.style.display = "none";
				return;
			}
			upload_pop_status_label.style.display = "block";
			upload_pop_status.innerText = msg;
		}

		/**
		 * Checks if a file is already selected or not.
		 * @param {File} file - The file to check.
		 * @returns {number} - Returns the index+1 of the file if it exists, otherwise returns 0.
		 */
		function uploader_exist(file) {
			for (let i = 0; i < selected_files.files.length; i++) {
				const f = selected_files.files[i];
				if (f.name == file.name) {
					return i+1; // 0 is false, so we add 1 to make it true
				}
			};
			return 0; // false;
		}


		/**
		 * Adds files to the selected files list and replaces any existing file with the same name.
		 * @param {FileList} files - The list of files to add.
		 */
		function addFiles(files) {
			var exist = false;

			for (let i = 0; i < files.length; i++) {
				const file = files[i];
				exist = uploader_exist(file);

				if (exist) {
					// if file already selected,
					// remove that and replace with
					// new one, because, when uploading
					// last file will remain in host server,
					// so we need to replace it with new one
					toaster.toast("File already selected", 1500);
					selected_files.items.remove(exist-1);
				}
				selected_files.items.add(file);
			};
			log("selected "+ selected_files.items.length+ " files");
			uploader_showFiles();
		}

		function uploader_removeFileFromFileList(index) {
			let dt = new DataTransfer();
			// const input = byId('files')
			// const { files } = input

			for (let i = 0; i < selected_files.files.length; i++) {
				let file = selected_files.files[i]
				if (index !== i) {
					dt.items.add(file) // here you exclude the file. thus removing it.
				}
			}

			selected_files = dt
			// uploader_input.files = dt // Assign the updates list
			uploader_showFiles()
		}

		function uploader_showFiles() {
			tools.del_child(uploader_file_display)

			if(selected_files.files.length){
				uploader_file_container.style.display = "contents"
			} else {
				uploader_file_container.style.display = "none"
			}

			for (let i = 0; i <selected_files.files.length; i++) {
				uploader_showFile(selected_files.files[i], i);
			};
		}


		function uploader_showFile(file, index){
			let filename = file.name;
			let size = fmbytes(file.size);

			let item = createElement("table");
			item.className = "upload-file-item";

			let fname = createElement("td");
			fname.className = "ufname";
			fname.innerText = filename;
			item.appendChild(fname);

			let fsize = createElement("td");
			fsize.className = "ufsize";
			let fsize_text = createElement("span");
			fsize_text.innerText = size;
			fsize.appendChild(fsize_text);
			item.appendChild(fsize);

			let fremove = createElement("td");
			fremove.className = "ufremove";
			let fremove_icon = createElement("span");
			fremove_icon.innerHTML = "&times;";
			fremove_icon.onclick = function(){
				uploader_removeFileFromFileList(index)
			}
			fremove.appendChild(fremove_icon);
			item.appendChild(fremove);

			uploader_file_display.appendChild(item);

		}



		return Form;


	}

	up_stat(form, stat=null) {
		if(stat===null){
			return form.getAttribute("uploading");
		}
		form.setAttribute("uploading", stat);
	}

	show(index){
		let form = this.uploaders[index];
		popup_msg.createPopup("Upload Files", form);
		popup_msg.show();
	}

	cancel(index, remove=false){
		let request = this.requests[index];
		let form = this.uploaders[index];
		let prog_id = form.prog_id;

		if(form){
			form.querySelector(".upload-button").innerText = "➾ Upload";
		}
		progress_bars.update(prog_id, {
			"status_text": "Upload Canceled",
			"status_color": "red",
			"status": "error",
			"percent": 0})


		if(this.status[index]){
			this.status[index] = false;
			if(request){
				request.abort();
			}
			if(!remove) toaster.toast("Upload Canceled");

			return true;
		}

		return false;
	}

	remove(index){
		this.cancel(index, true); //cancel the upload (true to make sure it doesn't show toast)
		let form = this.uploaders[index];
		let prog_id = form.prog_id;
		if (prog_id){
			progress_bars.remove(prog_id);
		}
		this.uploaders[index].remove(); //remove the form from DOM
		delete this.uploaders[index]; //remove the form from uploaders array
		delete this.requests[index]; //remove the request from requests array
	}

}

const upload_man = new UploadManager();


class FileManager {
	constructor() {
	}

	show_more_menu(){
		let that = this;
		let menu = createElement("div")

		let sort_by = createElement("div")
		sort_by.innerText = "Sort By"
		sort_by.className = "disable_selection popup-btn menu_options debug_only"
		sort_by.onclick = function(){
			that.Show_sort_by()
		}
		menu.appendChild(sort_by)

		let new_folder = createElement("div")
		new_folder.innerText = "New Folder"
		new_folder.onclick = function(){
			that.Show_folder_maker()
		}
		new_folder.className = "disable_selection popup-btn menu_options"
		menu.appendChild(new_folder)

		let upload = createElement("div")
		upload.innerText = "Upload Files"
		upload.className = "disable_selection popup-btn menu_options"
		if (user.permissions.NOPERMISSION || !user.permissions.UPLOAD){
			upload.className += " disabled"
		} else {
			upload.onclick = function(){
				that.Show_upload_files()
			}
		}
		menu.appendChild(upload)

		popup_msg.createPopup("Options", menu)

		popup_msg.open_popup()
	}


	Show_folder_maker() {
		popup_msg.createPopup("Create Folder",
			"Enter folder name: <input id='folder-name' type='text'><br><br><div class='pagination center' onclick='context_menu.create_folder()'>Create</div>"
			);
		popup_msg.open_popup();
	}

	Show_upload_files() {
		let form = upload_man.new()
		popup_msg.createPopup("Upload Files", form);
		popup_msg.open_popup();
	}



}

const fm = new FileManager();





function show_file_list() {
	let folder_li = createElement('div');
	let file_li = createElement("div")
	r_li.forEach((r, i) => {
		// time to customize the links according to their formats
		var folder = false
		let type = null;
		// let r = r_li[i];
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


		let hrr = createElement("hr")
		item.appendChild(hrr);
		if (folder) {
			folder_li.appendChild(item);
		} else {
			file_li.appendChild(item)
		}
	});

	clear_file_list(); // clear the links since they are no js compatible

	let dir_container = byId("js-content_list")
	dir_container.appendChild(folder_li)
	dir_container.appendChild(file_li)
}

"""


pt_config.file_list["script_video_player.js"] = r"""
class Video_Page {
	constructor() {
		this.type = "vid"

		this.my_part = document.getElementById("video-page")

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

		this.player_source = document.getElementById("player_source")
		this.player_title = byId("player_title")
			this.player_warning = byId("player-warning")
			this.video_dl_url = byId("video_dl_url")


		this.player = null;

		if (typeof(Plyr) !== "undefined"){
			this.player = new Plyr('#player', {
				controls: this.controls
			});
		}
	}

	async initialize() {
		page.hide_actions_button(); // Hide actions button, not needed here


		var url = tools.add_query_here("vid-data")

		var data = await fetch(url)
					.then(data => {return data.json()})
					.catch(err => {console.error(err)})

		var video = data.video
		var title = data.title
		var content_type = data.content_type
		var warning = data.warning


		this.player_title.innerText = title
		this.player_warning.innerHTML = warning
		this.video_dl_url.href = video

		page.set_title(title)

		if (this.player){
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

			this.init_online_player() // Add double click to skip
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
		this.player_source.src = ""
		this.player_source.type = ""
		this.player_title.innerText = ""
		this.player_warning.innerHTML = ""
		this.video_dl_url.href = ""
	}

	init_online_player() {
		var player = this.player;
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
	}
}

var video_page = new Video_Page()
"""


pt_config.file_list["script_page_handler.js"] = r"""

class Page{
	constructor(){
		this.container = byId('content_container')
		this.type = null;
		this.handler = fm_page; // default handler

		this.actions_button = byId("actions-btn")
		this.actions_button_text = byId("actions-btn-text")


		this.dir_tree = document.getElementById("dir-tree")

		this.dir_tree.scrollLeft = this.dir_tree.scrollWidth;
		// convert scroll to horizontal
		this.dir_tree.onwheel = function(event) {
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

	get actions_loading_icon(){
		return byId("actions-loading-icon")
	}

	get actions_button_icon(){
		return byId("actions-btn-icon")
	}

	get_type(){
		const url = tools.add_query_here('type', '');
		return fetch(url)
					.then(data => {return data.text()})
	}

	hide_all(){
		for (let handler of Object.values(this.handlers)){
			handler.hide();
		}
	}

	clear(){
		this.handler.clear()
	}

	async initialize(){
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

		if (this.handler){
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

	show_loading(){
		this.actions_loading_icon.classList.remove("hidden");
		this.actions_button_icon.classList.add("hidden");
		this.actions_button_text.classList.add("hidden");
	}

	hide_loading(){
		this.actions_loading_icon.classList.add("hidden");
		this.actions_button_icon.classList.remove("hidden");
		this.actions_button_text.classList.remove("hidden");
	}


	show_actions_button(){
		this.actions_button.style.display = "flex";
	}

	hide_actions_button(){
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

	refresh_dir(){
		console.log(this)
		if (this.type == "dir"){
			fm_page.initialize(true); // refresh the page
		}
	}
}

const page = new Page();

"""


pt_config.file_list["script_admin_page.js"] = r"""
class Admin_page {
	constructor(){
		this.my_part = byId("admin_page")
	}

	initialize(){
		this.show()
		page.set_actions_button_text("Add User&nbsp;");
		page.show_actions_button();
	}

	show(){
		this.my_part.classList.add("active");
		updater.check_update();
		admin_tools.get_users();
	}

	hide(){
		this.my_part.classList.remove("active");
	}

	on_action_button() {
		admin_tools.add_user();
	}

	clear() {
		var table = byClass("users_list")[0]
		var rows = table.rows.length
		for (var i = 1; i < rows; i++) {
			table.deleteRow(1)
		}
	}
}

var admin_page = new Admin_page()


class Updater{
	async check_update() {
		fetch('/?update')
		.then(response => {
			// console.log(response);
			return response.json()
		}).then(data => {
			if (data.update_available) {
				byId("update_text").innerText = "Update Available! 🎉 Latest Version: " + data.latest_version ;
				byId("update_text").style.backgroundColor = "#00cc0033";

				byId("run_update").style.display = "block";
			} else {
				byId("update_text").innerText = "No Update Available";
				byId("update_text").style.backgroundColor = "#888";
			}
		})
		.catch(async err => {
			byId("update_text").innerText = "Update Error: " + "Invalid Response";
			byId("update_text").style.backgroundColor = "#CC000033";
		});
	}

	// run_update() {
	// 	byId("update_text").innerText = "Updating...";
	// 	fetch('/?update_now')
	// 	.then(response => response.json())
	// 	.then(data => {
	// 		if (data.status) {
	// 			byId("update_text").innerHTML = data.message;
	// 			byId("update_text").style.backgroundColor = "green";

	// 		} else {
	// 			byId("update_text").innerHTML = data.message;
	// 			byId("update_text").style.backgroundColor = "#bbb";
	// 		}
	// 	})
	// 	.catch(err => {
	// 		byId("update_text").innerText = "Update Error: " + "Invalid Response";
	// 		byId("update_text").style.backgroundColor = "#CC000033";
	// 	})


	// 	byId("run_update").style.display = "none";
	// }

}

var updater = new Updater();



class Admin_tools {
	constructor(){
		this.user_list = [];
	}

	async get_users() {
		fetch('/?get_users')
		.then(response => response.json())
		.then(data => {
			this.user_list = data;
			this.display_users();
		})
		.catch(err => {
			console.log(err);
		})
	}

	display_users() {
		var table = byClass("users_list")[0];
		var rows = table.rows.length;
		for (var i = 1; i < rows; i++) {
			table.deleteRow(1);
		}

		for (i = 0; i < this.user_list.length; i++) {
			var row = table.insertRow(-1);
			row.innerHTML = "<td>" + this.user_list[i] + "</td><td><div class='pagination' onclick='admin_tools.manage_user(" + i +
				")'>Manage</div></td></td><td>";
		}
	}

	show_perms(index) {

	}

	manage_user(index) {
		var username = this.user_list[index];


		const client_page_html = `
<form action="" method="post" class="perm_checker_form">
	<h2>Update Permissions</h2>
	<table>
		<tr>
			<td>View</td>
			<td><input type="checkbox" name="VIEW" value="0" id="view"></td>
		</tr>
		<tr>
			<td>Download</td>
			<td><input type="checkbox" name="DOWNLOAD" value="1" id="download"></td>
		</tr>
		<tr>
			<td>Modify</td>
			<td><input type="checkbox" name="MODIFY" value="2" id="modify"></td>
		</tr>
		<tr>
			<td>Delete</td>
			<td><input type="checkbox" name="DELETE" value="3" id="delete"></td>
		</tr>
		<tr>
			<td>Upload</td>
			<td><input type="checkbox" name="UPLOAD" value="4" id="upload"></td>
		</tr>
		<tr>
			<td>Zip</td>
			<td><input type="checkbox" name="ZIP" value="5" id="zip"></td>
		</tr>
		<tr>
			<td>Admin</td>
			<td><input type="checkbox" name="ADMIN" value="6" id="admin"></td>
		</tr>
		<tr>
			<td>Member</td>
			<td><input type="checkbox" name="MEMBER" value="7" id="member" disabled></td>
		</tr>
	</table>

	<div class="submit_parent">
		<input type="submit" name="submit" value="Submit" id="submit">
	</div>

</form>

<br>
<div class='pagination' onclick='admin_tools.delete_user(${index})'
	style="margin: 0 auto;">Delete User</div>

<!--
on submit, get all the values and put them in a dict object
if admin is checked, all other values are checked -->


<!-- make the table and input look modern
keep the submit button in center, modernize the button UI-->
<style>
	.perm_checker_form table {
		border-collapse: collapse;
		width: 100%;
		color: #afafaf;
		font-family: monospace;
		font-size: 25px;
		text-align: left;
	}
	.perm_checker_form tr:nth-child(even) {background-color: #4d4d4d}

	.perm_checker_form td:nth-child(1){
		text-align: left;
		width: calc(100% - 50px);
	}

	.perm_checker_form td:nth-child(2){
		text-align: center;
		width: 50px;
	}


	.perm_checker_form input[type=checkbox] {
		-moz-appearance:none;
		-webkit-appearance:none;
		-o-appearance:none;
		outline: none;
		content: none;
	}

	.perm_checker_form input[type=checkbox]:before {
		content: "✅";
		font-size: 17px;
		color: transparent !important;
		background: #636363;
		display: block;
		width: 17px;
		height: 17px;
		border: 1px solid black;
	}

	.perm_checker_form input[type=checkbox][disabled]:before {
		filter: grayscale(1);
	}

	.perm_checker_form input[type=checkbox]:checked:before {
		color: black !important;
	}

	.perm_checker_form input[type=submit] {
		background-color: #444;
		color: white;
		font-family: monospace;
		font-size: 25px;
		text-align: center;
		border: none;
		width: 60%;
		padding: 15px 32px;
		text-decoration: none;
		display: inline-block;
		margin: 4px 2px;
		cursor: pointer;

		border-radius: 2px;
		box-shadow: 5px 5px 0 0 #1abeff;
	}

	.perm_checker_form input[type=submit]:hover {
		background-color: #333;
		box-shadow: 3px 3px 0 0 #1abeff;
	}

	.perm_checker_form .submit_parent {
		display: flex;
		justify-content: center;
	}

</style>

		`

		var client_page_script = `
{
	var view = document.getElementById("view");
	var download = document.getElementById("download");
	var modify = document.getElementById("modify");
	var delete_ = document.getElementById("delete");
	var upload = document.getElementById("upload");
	var zip = document.getElementById("zip");
	var admin = document.getElementById("admin");
	var member = document.getElementById("member");

	var submit = document.getElementById("submit");

	var username = "${username}";
	var _user = new User();
	fetch('/?get_user_perm&username=' + username)
	.then(response => response.json())
	.then(data => {
		if (data.status) {
			_user.permissions_code = data.permissions_code;
			var perms = _user.extract_permissions();

			view.checked = perms["VIEW"];
			download.checked = perms["DOWNLOAD"];
			modify.checked = perms["MODIFY"];
			delete_.checked = perms["DELETE"];
			upload.checked = perms["UPLOAD"];
			zip.checked = perms["ZIP"];
			admin.checked = perms["ADMIN"];
			member.checked = perms["MEMBER"];
		} else {
			popup_msg.createPopup(data["message"]);
			popup_msg.open_popup();
		}
	})


	submit.onclick = function(e) {
		e.preventDefault();
		var dict = {};
		dict["VIEW"] = view.checked;
		dict["DOWNLOAD"] = download.checked;
		dict["MODIFY"] = modify.checked;
		dict["DELETE"] = delete_.checked;
		dict["UPLOAD"] = upload.checked;
		dict["ZIP"] = zip.checked;
		dict["ADMIN"] = admin.checked;
		dict["MEMBER"] = member.checked;


		_user.permissions = dict;
		var perms = _user.pack_permissions();

		fetch('/?update_user_perm&username=' + username + "&perms=" + perms)
		.then(response => response.json())
		.then(data => {
			popup_msg.createPopup(data["status"], data["message"]);
			popup_msg.open_popup();
		})
		.catch(err => {
			console.log(err);
		})
	}


	admin.onclick = function() {
		if (admin.checked) {
			view.checked = true;
			download.checked = true;
			modify.checked = true;
			delete_.checked = true;
			upload.checked = true;
			zip.checked = true;
		}
	}

}
		`


		popup_msg.createPopup(username + " Options", client_page_html, true, null_func, client_page_script);

		popup_msg.open_popup()


	}

	delete_user(index) {
		var username = this.user_list[index];
		r_u_sure({y:()=>{
			fetch('/?delete_user&username=' + username)
			.then(response => response.json())
			.then(data => {
				if (data.status) {
					popup_msg.createPopup("Success", data["message"]);
				} else {
					popup_msg.createPopup("Error", data["message"]);
				}
				popup_msg.open_popup();
				this.get_users();
			})
			.catch(err => {
				console.log(err);
			})
		}});
	}

	request_reload() {
		r_u_sure({y:()=>{
			fetch('/?reload')
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data)
				popup_msg.open_popup();
			})

		}});
	}

	request_shutdown() {
		r_u_sure({y:()=>{
			fetch('/?shutdown')
			.then(response => response.text())
			.then(data => {
				popup_msg.createPopup(data)
				popup_msg.open_popup();
			})

		}});
	}

	add_user() {
		var client_page_html = `
<form action="" method="post" class="add_user_form">
	<table>
		<tr>
			<td>Username</td>
			<td><input type="text" name="username" id="add_user_username"></td>
		</tr>
		<tr>
			<td>Password</td>
			<td><input type="password" name="password" id="add_user_password"></td>
		</tr>
		<tr>
			<td>Confirm Password</td>
			<td><input type="password" name="confirm_password" id="add_user_confirm_password"></td>
		</tr>
	</table>

	<div class="submit_parent">
		<input type="submit" name="submit" value="Submit" id="add_user_submit">
	</div>

	<div id="add_user_status"></div>

</form>

<style>

	.add_user_form table {
		border-collapse: collapse;
		width: 100%;
		color: #afafaf;
		font-family: monospace;
		font-size: 18px;
		text-align: left;
	}

	.add_user_form input[type=text], input[type=password] {
		background-color: #444;
		color: white;
		font-family: monospace;
		font-size: 20px;
		text-align: center;
		border: none;
		width: 90%;
		padding: 5px 7px;
		text-decoration: none;
		display: inline-block;
		margin: 4px 2px;
		cursor: pointer;

		border-radius: 2px;
		box-shadow: 5px 5px 0 0 #1abeff;
	}

	.add_user_form input[type=text]:hover, input[type=password]:hover {
		background-color: #333;
		box-shadow: 3px 3px 0 0 #1abeff;
	}

	.add_user_form .submit_parent {
		display: flex;
		justify-content: center;
	}

	.add_user_form input[type=submit] {
		background-color: #444;
		color: white;
		font-family: monospace;
		font-size: 25px;
		text-align: center;
		border: none;
		width: 60%;
		padding: 15px 32px;
		text-decoration: none;
		display: inline-block;
		margin: 4px 2px;
		cursor: pointer;

		border-radius: 2px;
		box-shadow: 5px 5px 0 0 #1abeff;
	}

	.add_user_form input[type=submit]:hover {
		background-color: #333;
		box-shadow: 3px 3px 0 0 #1abeff;
	}

</style>
		`

		var client_page_script = `
{
	var username = document.getElementById("add_user_username");
	var password = document.getElementById("add_user_password");
	var confirm_password = document.getElementById("add_user_confirm_password");
	var submit = document.getElementById("add_user_submit");
	var submit_status = document.getElementById("add_user_status");
	const NotUsernameRegex = /[^a-zA-Z0-9_]/g;
	const note = (msg, color='red') => {
		submit_status.innerHTML = msg;
		submit_status.style.color = color;
	}

	submit.onclick = function(e) {
		e.preventDefault();

		var OK = false;
		var _uname = username.value;
		var _pass = password.value;
		var _pass_confirm = confirm_password.value;

		console.log(_uname);
		console.log(_pass);

		if(_uname.length<1){
			note("Username must have at least 1 character!")
		} else if (_uname.length>64){
			note("Username must be less than 64 character long")
		} else if (_pass.length<4){
			note("Password must have at least 4 character!")
		}else if (_pass.length>256){
			note("Password can't be longer than 256 characters")
		} else if (NotUsernameRegex.test(_uname)){
			note("Username can only have A-Z, a-z, 0-9, _")
		} else if (_uname == _pass){
			note("Username and password can't be the same!")
		} else if (_pass != _pass_confirm){
			note("Passwords do not match!")
		} else {
			OK = true;
			note("Adding user...", "green");
		}

		if (!OK) {
			return false;
		}

		fetch('/?add_user&username=' + username.value + "&password=" + password.value)
		.then(response => response.json())
		.then(data => {
			popup_msg.createPopup(data["status"], data["message"]);
			popup_msg.open_popup();

			admin_tools.get_users();
		})
		.catch(err => {
			console.log(err);
		})
	}
}
		`

		popup_msg.createPopup("Add User", client_page_html, true, null_func, client_page_script);

		popup_msg.open_popup()
	}
}

var admin_tools = new Admin_tools();


"""


pt_config.file_list["script_error_page.js"] = r"""
class Error_Page {
	constructor() {
		this.type = "error"

		this.my_part = document.getElementById("error-page")
	}

	initialize() {
		page.hide_actions_button(); // Hide actions button, not needed
		page.set_title("Error")
	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
	}
}

var error_page = new Error_Page()
"""


pt_config.file_list["html_upload.html"] = r"""
<noscript>
	<form ENCTYPE="multipart/form-data" method="post" action="?upload" id="uploader-nojs">
		<!-- using "?upload" action so that user can go back to the page -->
		<center>
			<h1><u>Upload file</u></h1>


			<input type="hidden" name="post-type" value="upload">

			<span class="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="password"
				label="Password" class="upload-pass-box" placeholder="Password" maxlength="512" minlength="1" required><br><br>
			<br><br>
			<!-- <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" multiple /><br><br> -->
			<div class="upload-box">
				<div class="drag-area">
					<div class="drag-icon">⬆️</div>
					<header>Select Files To Upload</header>
					<input type="file" name="file" multiple class="drag-browse" value="Browse File" style="max-width: min(300px, 80%);">
				</div>
			</div>

		</center>
		<center><input class="drag-browse" type="submit" value="&#10174; upload"></center>
	</form>
</noscript>

"""


pt_config.file_list["script_zip_page.js"] = r"""

class Zip_Page {
	constructor() {
		this.type = "zip"

		this.my_part = document.getElementById("zip-page")

		this.message = document.getElementById("zip-prog")
		this.percentage = document.getElementById("zip-perc")
	}

	async initialize() {
		page.hide_actions_button(); // Hide actions button, not needed here

		this.dl_now = false
		this.check_prog = true

		this.prog_timer = null

		var url = tools.add_query_here("zip_id")

		var data = await fetch(url)
					.then(data => {return data.json()})
					.catch(err => {console.error(err)})

		// {
		// 	"status": status,
		// 	"message": message,
		// 	"zid": zid,
		//  "filename": filename
		// }

		var status = data.status
		var message = data.message
		this.zid = data.zid
		this.filename = data.filename

		const that = this

		if (status) {
			this.prog_timer = setInterval(function() {
				that.ping(window.location.pathname + "?zip&zid=" + that.zid + "&progress")}, 500)
		} else {
			this.message.innerHTML = "Error";
			this.percentage.innerText = message;
		}


	}

	hide() {
		this.my_part.classList.remove("active");
	}

	show() {
		this.my_part.classList.add("active");
	}

	clear() {
		this.message.innerHTML = ""
		this.percentage.innerText = ""
		this.dl_now = false
		this.check_prog = true
		this.zid = null
		this.filename = null
		if(this.prog_timer){
			clearTimeout(this.prog_timer)
			this.prog_timer = null
		}
	}

	
	ping(url) {
		const that = this
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (that.dl_now) {
				return
			}
			if (this.readyState == 4 && this.status == 200) {
				// Typical action to be performed when the document is ready:
				//document.getElementById("demo").innerHTML = xhttp.responseText;
				// json of the response
				var resp = safeJSONParse(this.response, ["status", "message"], 5000);
				// console.log(resp)

				if (resp.status=="SUCCESS"){
					that.check_prog = true;
				} else if (resp.status=="DONE"){
					that.message.innerHTML = "Downloading";
					that.percentage.innerText = "";
					that.dl_now = true;
					clearTimeout(that.prog_timer)
					that.run_dl()
				} else if (resp.status=="ERROR"){
					that.message.innerHTML = "Error";
					that.percentage.innerText = resp.message;
					clearTimeout(that.prog_timer)
				} else if (resp.status=="PROGRESS"){
					that.percentage.innerText = resp.message + "%";
				} else {
					that.percentage.innerText = resp.status + ": " + resp.message;
					if(that.prog_timer){
						clearTimeout(that.prog_timer)
						that.prog_timer = null
					}
				}
			}
		};
		xhttp.open("GET", url, true);
		xhttp.send();
	}

	
	run_dl() {
		tools.download(window.location.pathname + "?zip&zid=" + this.zid + "&download", this.filename, true)
	}

}

var zip_page = new Zip_Page();
"""


pt_config.file_list["script_theme.js"] = r"""
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
			document.querySelectorAll(".fa").forEach(e => e.parentNode.replaceChild(Object.assign(document.createElement("i"), { className: e.className, style: e.style , id: e.id}), e));
		}
	}

	async load_fa() {
		var that = this;
		let link = createElement('link');
		link.rel = "stylesheet";

		link.type = "text/css";
		link.media = 'print';
		// link.href = "https://cdn.jsdelivr.net/gh/hung1001/font-awesome-pro-v6@44659d9/css/all.min.css";

		const cache_buster = Math.random() // bcz it needs to fetch webFont files which may not be cached and cause Tofu font issue
		link.href = "//cdn.jsdelivr.net/gh/RaSan147/fabkp@2f5670e/css/all.min.css" + "?no_cache=" + cache_buster;
		link.onload = function () {
			log("fa loaded")
			that.fa_ok = true;
			that.del_fa_alt()
			link.media = "all";



			// var fa = byClass("fa")
			// for (var i=0;i<fa.length;i++){
			// 	fa[i].tagName = "i"
			// }
		}
		document.head.appendChild(link);
	}
}

var theme_controller = new Theme_Controller();

theme_controller.getViewportSize();
theme_controller.load_fa()






const MAIN_JS = true;
const V = "0.0.1";

if (typeof datas === "undefined") {window["datas"] = {}} // if datas is not defined

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
		if (! this.top_bar) return false;

		this.top_bar.style.top = "0";
		document.body.style.top = "50px";
		// this.top_bar.classList.remove("inactive");
	}

	hide() {
		if (! this.top_bar) return false;

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

	_closeNavR(){
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
"""


pt_config.file_list["html_login.html"] = r"""
<!DOCTYPE HTML>
<!-- test1 -->
<html lang="en">
<head>

<meta charset="UTF-8">
<meta name="viewport" content="user-scalable=no, width=device-width, initial-scale=1, maximum-scale=1">

<meta  property="og:title" content="Signup" />

<meta property="og:image" content="https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.png" />




<link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet'>

<title>Login</title>


<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.png" type="image/png">


<link rel="stylesheet" href="?style">
</head>

<body>


<div>
	<div id="login-page">
		<div id="login-header">
			<h1>Login</h1>
		</div>
		<div id="login-form">
			<form action="?do_login" method="post" ENCTYPE="multipart/form-data" id="login">
				<input name="post-type" value="login" hidden>
				<table>
					<tr>
					<th><label for="username">Username</label></th>
					<td><input type="text" name="username" class="txt_box" id="username" placeholder="Username" maxlength="64" minlength="1"></td>
					</tr>
					<tr>
					<th><label for="password">Password</label></th>
					<td><input type="password" name="password" class="txt_box" id="password" placeholder="Password" maxlength="512"></td>
					</tr>
				</table>
				<div id="login-submit">
					<input id="submit_btn" type="submit" value="login">
				</div>
			</form>
		</div>

		<p class="status" id="status"></p>

	</div>
</div>

<br>
<div>Don't Have account? <a href="?signup" style="font-size: medium;">SIGNUP</a></div>


<style>
body {
	padding: 20px;
}

.status {
	color: rgb(48, 48, 48);
	display: none;
	font-size: 1.5em;
	padding: 5px;
	margin: 5px;
	border: solid 2px;
	border-radius: 4px;
}


#login-page {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}


#login-form {
	width: 100%;
	max-width: 400px;
}

.txt_box {
	width: 100%;
	height: 25px;
	font-size: 1em;
}

#submit_btn {
	width: 200px;
	height: 50px;
	font-size: 1.5em;
}

table {
	border-color: #00000000;
	border-spacing: 4px;
	width: 95%;
	text-align: left;
}
</style>

<script src="/?global_script"></script>
<script>

function update_note(note='', color="gray"){

	const status = byId('status')
	status.style.display = 'none';
	if(note != ''){
		status.style.display = 'block';
	}
	status.style.color = color;
	status.innerText = note;
}



function test_fields(){
	const note = (msg) => {update_note(msg, "red")}

	const _uname = byId("username").value
	const _pass = byId("password").value
	const usernameRegex = /^[a-zA-Z0-9_]+$/g;


	if(_uname.length<1){
		note("Username must have at least 1 character!")
		return 0;
	}
	if (_uname.length>64){
		note("Username must be less than 64 character long")
		return 0;
	}
	if (_pass.length<4){
		note("Password must have at least 4 character!")
		return 0;
	}
	if (_pass.length>256){
		note("Password can't be longer than 256 characters")
		return 0;
	}
	if (!usernameRegex.test(_uname)){
		note("Username can only have A-Z, a-z, 0-9, _")
		return 0;
	}
	note()
	return 1;
}


byId("login").onsubmit = (e) => {
	e.preventDefault()

	const formData = new FormData(e.target)

	if (!test_fields()){
		return 0
	}
	var msg = "";
	var color = "red"

	// const filenames = formData.getAll('files').map(v => v.name).join(', ')
	const request = new XMLHttpRequest()
	request.open(e.target.method, e.target.action)
	request.timeout = 60*1000;
	request.onreadystatechange = () => {
		if (request.readyState === XMLHttpRequest.DONE) {
			msg = `${request.status}: ${request.statusText}`
			if (request.status === 0) msg = 'Connection failed'
			if (request.status === 204 || request.status === 200){
				var response = JSON.parse(request.responseText);
				if (response.status == "success"){
					msg = "Signed up. REDIRECTING...";
					color = "green"

					setTimeout(function(){goto("./");}, 1000);
				}
				else {
					msg = response.message;
					if (response.status == "failed"){
						color = "red";
					} else {
						color = "Yellow";
					}
				}

			}
			if (request.status === 401) msg = 'Incorrect password';

			update_note(msg, color)
		}
	}


	request.send(formData)
}
</script>
"""


pt_config.file_list["html_signup.html"] = r"""
<!DOCTYPE HTML>
<!-- test1 -->
<html lang="en">
<head>

<meta charset="UTF-8">
<meta name="viewport" content="user-scalable=no, width=device-width, initial-scale=1, maximum-scale=1">

<meta  property="og:title" content="Signup" />

<meta property="og:image" content="https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.png" />




<link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet'>

<title>Signup</title>


<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.png" type="image/png">


<link rel="stylesheet" href="?style">
</head>

<body>


<div>
	<div id="signup-page">
		<div id="signup-header">
			<h1>Signup</h1>
		</div>
		<div id="signup-form">
			<form action="?do_signup" method="post" ENCTYPE="multipart/form-data" id="signup">
				<input name="post-type" value="signup" hidden>
				<table>
					<tr>
					<th><label for="username">Username</label></th>
					<td><input type="text" name="username" class="txt_box" id="username" placeholder="Username (can be anything)" maxlength="64" minlength="1"></td>
					</tr>
					<tr>
					<th><label for="password">Password</label></th>
					<td><input type="password" name="password" class="txt_box" id="password" placeholder="Password" maxlength="512"></td>
					</tr>
				</table>
				<div id="signup-submit">
					<input id="submit_btn" type="submit" value="Signup">
				</div>
			</form>
		</div>

		<p class="status" id="status"></p>

	</div>
</div>

<br>
<div>Already have an account? <a href="?login" style="font-size: medium;">LOGIN</a></div>


<style>
body {
	padding: 20px;
}

.status {
	color: rgb(48, 48, 48);
	display: none;
	font-size: 1.5em;
	padding: 5px;
	margin: 5px;
	border: solid 2px;
	border-radius: 4px;
}


#signup-page {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}

#signup-form {
	width: 100%;
	max-width: 400px;
}

.txt_box {
	width: 100%;
	height: 25px;
	font-size: 1em;
}

#submit_btn {
	width: 200px;
	height: 50px;
	font-size: 1.5em;
}

table {
	border-color: #00000000;
	border-spacing: 4px;
	width: 95%;
	text-align: left;
}
</style>

<script src="/?global_script"></script>
<script>

function update_note(note='', color="gray"){

	const status = byId('status')
	status.style.display = 'none';
	if(note != ''){
		status.style.display = 'block';
	}
	status.style.color = color;
	status.innerText = note;
}



function test_fields(){
	const note = (msg) => {update_note(msg, "red")}

	const _uname = byId("username").value
	const _pass = byId("password").value
	const usernameRegex = /^[a-zA-Z0-9_]+$/g;


	if(_uname.length<1){
		note("Username must have at least 1 character!")
	} else if (_uname.length>64){
		note("Username must be less than 64 character long")
	} else if (_pass.length<4){
		note("Password must have at least 4 character!")
	}else if (_pass.length>256){
		note("Password can't be longer than 256 characters")
	} else if (!usernameRegex.test(_uname)){
		note("Username can only have A-Z, a-z, 0-9, _")
	} else if (_uname == _pass){
		note("Username and password can't be the same!")
	} else {
		return 1;
	}

	return 0;
}


byId("signup").onsubmit = (e) => {
	e.preventDefault()

	const formData = new FormData(e.target)

	if (!test_fields()){
		return 0
	}
	var msg = "";
	var color = "red"

	// const filenames = formData.getAll('files').map(v => v.name).join(', ')
	const request = new XMLHttpRequest()
	request.open(e.target.method, e.target.action)
	request.timeout = 60*1000;
	request.onreadystatechange = () => {
		if (request.readyState === XMLHttpRequest.DONE) {
			msg = `${request.status}: ${request.statusText}`
			if (request.status === 0) msg = 'Connection failed'
			if (request.status === 204 || request.status === 200){
				var response = JSON.parse(request.responseText);
				if (response.status == "success"){
					msg = "Signed up. REDIRECTING...";
					color = "green"

					setTimeout(function(){goto("./");}, 1000);
				}
				else {
					msg = response.message;
					if (response.status == "failed"){
						color = "red";
					} else {
						color = "Yellow";
					}
				}

			}
			if (request.status === 401) msg = 'Incorrect password';

			update_note(msg, color)
		}
	}


	request.send(formData)
}
</script>
"""

