from string import Template as _Template # using this because js also use {$var} and {var} syntax and py .format is often unsafe

__all__ = [
	"directory_explorer_header",
	"global_script",
	"file_list",
	"upload_form",
	"file_list_script",
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

def file_list_script():
	return get_template("html_script.html")

def upload_form():
	return get_template("html_upload.html")

def video_script():
	return global_script() + get_template("html_vid.html")

def zip_script():
	return global_script() + get_template("html_zip_page.html")

def admin_page():
	return global_script() + get_template("html_admin.html")

def error_page():
	return directory_explorer_header() + get_template("html_error.html")

