import os
from data_types import Template
__all__ = [
	"directory_explorer_header",
	"script_global",
	"upload_form",
	"file_list_script",
	"zip_script",
	"error_page",
	"theme_script",
	"video_page_script",
	"video_page_assets",
	"video_css",
	"plyr_js",
	"code_editor_assets",
	"no_page_assets",
	"page_handler_script",
	"admin_page_script",
	"login_page",
	"style_css",
	"code_editor_script"

]


# ---------------------------x--------------------------------

# PAGE TEMPLATES
##############################################################


enc = "utf-8"


class config:
	dev_mode = True
	file_list = {}

pt_config = config()



def _get_template(path):
	if pt_config.dev_mode:
		path = os.path.join(os.path.dirname(__file__), path)
		with open(path, encoding=enc) as f:
			return f.read()

	return pt_config.file_list[path]

def get_template(path):
	return Template(_get_template(path))


def directory_explorer_header():
	return get_template("html_page.html")



def style_css():
	return _get_template("style_main.css")






def script_global():
	return get_template("script_global.js")

def assets_script():
	return get_template("script_main.js")

def file_list_script():
	return get_template("script_file_list.js")

def video_page_script():
	return get_template("script_video_player.js")

def video_css():
	"""Return bundled Plyr CSS, served locally for offline support."""
	return _get_template("video.css")

def plyr_js():
	"""Return bundled Plyr JS, served locally for offline support."""
	return _get_template("plyr.polyfilled.min.js")

def page_handler_script():
	return get_template("script_page_handler.js")

def admin_page_script():
	return get_template("script_admin_page.js")

def error_page_script():
	return get_template("script_error_page.js")

def zip_page_script():
	return get_template("script_zip_page.js")

def code_editor_script():
	return get_template("script_code_editor.js")


def no_page_assets() -> str:
	"""Return empty string — no page-specific assets needed."""
	return ""


def video_page_assets() -> str:
	"""Return HTML tags to load Plyr and video.css, served locally for offline support."""
	return (
		'\t<!-- Plyr video player (video pages only) -->\n'
		'\t<link rel="preload" href="/?video_css"'
		' onload="this.onload=null;this.rel=\'stylesheet\'" as="style">\n'
		'\t<noscript><link rel="stylesheet" href="/?video_css"></noscript>\n'
		'\t<script src="/?plyr_js" defer></script>\n'
		'\t<script src="/?video_page_script" defer></script>\n'
	)


_CODEMIRROR_BASE = "https://cdn.jsdelivr.net/npm/codemirror@5.65.21"

def code_editor_assets() -> str:
	"""Return HTML tags to load CodeMirror + all modes/addons, injected only on code-editor pages."""
	base = _CODEMIRROR_BASE
	modes = [
		"python/python", "javascript/javascript", "htmlmixed/htmlmixed",
		"css/css", "xml/xml", "markdown/markdown", "sql/sql", "clike/clike",
		"go/go", "php/php", "ruby/ruby", "yaml/yaml", "shell/shell",
		"toml/toml", "r/r",
	]
	addons = [
		"edit/matchbrackets", "edit/closebrackets", "edit/matchtags",
		"search/search", "search/searchcursor",
		"selection/active-line",
		"fold/foldcode", "fold/foldgutter", "fold/brace-fold",
		"fold/xml-fold", "fold/indent-fold", "fold/markdown-fold", "fold/comment-fold",
		"mode/overlay",
	]
	lines = [
		'\t<!-- CodeMirror 5.65.21 (code-editor pages only) -->',
		f'\t<link rel="stylesheet" href="{base}/lib/codemirror.css">',
		f'\t<link rel="stylesheet" href="{base}/addon/fold/foldgutter.css">',
		# Themes (switchable via script_code_editor.js)
		# f'\t<link rel="stylesheet" href="{base}/theme/material-darker.css">',
		# f'\t<link rel="stylesheet" href="{base}/theme/material-palenight.css">',
		f'\t<link rel="stylesheet" href="{base}/theme/material-ocean.css">',
		# Core must load synchronously (no defer)
		f'\t<script src="{base}/lib/codemirror.js"></script>',
	]
	for mode in modes:
		lines.append(f'\t<script src="{base}/mode/{mode}.min.js" defer></script>')
	for addon in addons:
		lines.append(f'\t<script src="{base}/addon/{addon}.min.js" defer></script>')
	lines.append('\t<script src="/?code_editor_script" defer></script>')
	return "\n".join(lines) + "\n"




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

