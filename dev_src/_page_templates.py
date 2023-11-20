from data_types import Template
__all__ = [
	"directory_explorer_header",
	"global_script",
	"upload_form",
	"file_list_script",
	"video_page",
	"zip_script",
	"admin_page",
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
	dev_mode = True
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




def upload_form():
	return _get_template("html_upload.html")

def video_page():
	return get_template("html_vid.html")

def zip_script():
	return get_template("html_zip_page.html")  # TODO: Move to Dynamic island

def admin_page():
	return get_template("html_admin.html")

def error_page():
	return directory_explorer_header()  # TODO: add to PWA

def theme_script():
	return get_template("script_theme.js")

def login_page():
	return get_template("html_login.html")

def signup_page():
	return get_template("html_signup.html")

#directory_explorer_header()

