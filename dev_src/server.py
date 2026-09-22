

# TODO
# ----------------------------------------------------------------
# * ADD MORE FILE TYPES
# * ADD SEARCH

import datetime
import hashlib
# import subprocess
import importlib.util
import json
import os
# import sys
import posixpath
import shutil
import threading
import traceback
import urllib.parse
import urllib.request
import uuid
from http import HTTPStatus

import _page_templates as pt
from _arg_parser import add_args
from _exceptions import LimitExceed
from _fs_utils import (UploadHandler, dir_navigator, fmbytes, get_dir_size,
					   get_stat, get_titles, get_tree_count_n_size, humanbytes)
from _list_maker import (list_directory, list_directory_html,
						 list_directory_json)
from _sub_extractor import extract_subtitles_from_file
from _zipfly_manager import ZIP_Manager
from pyrobox_ServerHost import ServerConfig
from pyrobox_ServerHost import ServerHost as SH
from pyroboxCore import DealPostData as DPD
from pyroboxCore import __version__ as pyroboxCore_version
from pyroboxCore import config as CoreConfig
from pyroboxCore import (
	directory_url_has_trailing_slash,
	logger,
	reload_server,
	validate_client_relpath,
)
from pyroboxCore import runner as pyroboxRunner
from pyroboxCore import tools
import user_mgmt as u_mgmt
from UX_Tools import is_file, xpath

__version__ = '0.9.7'
true = T = True
false = F = False
enc = "utf-8"

###########################################
# ADD COMMAND LINE ARGUMENTS
###########################################

add_args(CoreConfig)
cli_args = CoreConfig.parser.parse_known_args()[0]

logger.info(tools.text_box("Server Config", *({i: getattr(cli_args, i)}
			for i in vars(cli_args) if not (i.startswith("admin") or "password" in i))))


Sconfig = ServerConfig(cli_args=cli_args)
SH.server_config = Sconfig


###########################################
# CoreConfig.dev_mode = False

CoreConfig.MAIN_FILE = os.path.abspath(__file__)

CoreConfig.disabled_func.update({
	"send2trash": False,
	"natsort": False,
	"pyqrcode": False,
	"zip": False,
	"update": False,
	"delete": False,
	"download": False,
	"upload": False,
	"new_folder": False,
	"rename": False,
})


# INSTALL REQUIRED PACKAGES
REQUIREMENTS = ['send2trash', 'natsort', 'pyqrcode']


if not os.path.isdir(CoreConfig.log_location):
	try:
		os.mkdir(path=CoreConfig.log_location)
	except Exception:
		CoreConfig.log_location = "./"

if not CoreConfig.disabled_func.get("send2trash"):
	try:
		from send2trash import TrashPermissionError, send2trash
	except Exception:
		CoreConfig.disabled_func["send2trash"] = True
		logger.warning(
			"send2trash module not found, send2trash function disabled. Install it using `pip install send2trash`")


if not CoreConfig.disabled_func.get("natsort"):
	if importlib.util.find_spec("natsort") is None:
		CoreConfig.disabled_func["natsort"] = True
		logger.warning(
			"natsort not found, falling back to default sorting. Install it using `pip install natsort`")

if not CoreConfig.disabled_func.get("pyqrcode"):
	try:
		import pyqrcode
	except ImportError:
		CoreConfig.disabled_func["pyqrcode"] = True
		logger.warning(
			"pyqrcode module not found, QR code generation disabled. Install it using `pip install pyqrcode`")

   #############################################
  # HANDLER UTILS                #
 # Need to be loaded after CoreConfig is set #
#############################################


########## ZIP MANAGER ################################
# max_zip_size = 6*1024*1024*1024
zip_manager = ZIP_Manager(
	CoreConfig, size_limit=Sconfig.max_zip_size, zip_temp_dir=Sconfig.zip_dir)

#######################################################


########## PAGE TEMPLATES ###############################
pt.pt_config.dev_mode = CoreConfig.dev_mode

#########################################################


# TODO check against user_mgmt
# download file from url using urllib
def fetch_url(url, file=None):
	try:
		with urllib.request.urlopen(url, timeout=5) as response:
			data = response.read()  # a `bytes` object

		if not file:
			return data

		with open(file, 'wb', buffering=Sconfig.max_buffer_size) as f:
			f.write(data)
		return data
	except Exception:
		traceback.print_exc()
		return None


class PostError(Exception):
	pass





@SH.on_req('GET', hasQ="type")
def get_page_type(self: SH, *args, **kwargs):
	"""Return type of the page"""
	user, cookie = Sconfig.authorize_user(self)

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	result = "unknown"

	if self.query("admin"):
		result = "admin"

	elif self.query("login"):
		result = "login"

	elif self.query("signup"):
		result = "signup"

	elif self.query("edit"):
		result = "code"

	elif self.query("vid"):
		result = "vid"

	elif self.query("logout"):
		result = "logout"

	elif self.query("czip"):
		result = "zip"

	elif url_path == "/favicon.ico":
		result = "favicon"

	elif os.path.isdir(os_path):
		for index in "index.html", "index.htm":
			index = xpath(os_path, index)
			if os.path.exists(index):
				result = "html"
				break

		else:
			if self.query("json"):
				result = "dir_json"
			else:
				result = "dir"

	elif os.path.isfile(os_path):
		result = "file"

	return self.return_txt(result, cookie=cookie)


@SH.on_req('HEAD', '/favicon.ico')
def send_favicon(self: SH, *args, **kwargs):
	self.redirect(
		'https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.ico')


@SH.on_req('HEAD', hasQ="about")
def get_about(self: SH, *args, **kwargs):
	"""Return version of the server"""
	return self.send_text(f"Pyrobox Server v{__version__} (pyroboxCore v{pyroboxCore_version}) by RaSan147 (https://github.com/RaSan147/pyrobox)")


@SH.on_req('HEAD', hasQ="version")
def get_version(self: SH, *args, **kwargs):
	"""Return version of the server"""
	return self.send_text(f"{__version__}")


@SH.on_req('HEAD', hasQ="qr")
def get_qr(self: SH, *args, **kwargs):
	"""Return QR code for easy access"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	if CoreConfig.disabled_func["pyqrcode"]:
		return self.send_error(code=HTTPStatus.INTERNAL_SERVER_ERROR, message="QR code generation is disabled", cookie=cookie)

	query = self.query.get("qr", [None])[0]
	url = query or CoreConfig.address()

	if len(url) > 2048:
		return self.send_error(code=HTTPStatus.BAD_REQUEST, message="URL too long", cookie=cookie)

	md5_url = hashlib.md5(url.encode()).hexdigest() + \
		hashlib.sha256(url.encode()).hexdigest()
	qr_path = xpath(CoreConfig.temp_dir, f"QR-{md5_url}.svg")

	if not os.path.exists(qr_path):
		pyqrcode.create(url).svg(file=qr_path, scale=5)

	return self.send_file(qr_path, cookie=cookie)


@SH.on_req('HEAD', hasQ="reload")
def reload(self: SH, *args, **kwargs):
	# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	CoreConfig.reload = True
	self.send_text("Reload initiated", cookie=cookie)

	reload_server()


@SH.on_req('HEAD', hasQ="shutdown")
def shutdown(self: SH, *args, **kwargs):
	# SHUTS DOWN THE SERVER. VULNERABLE
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	self.send_text("Shut down initiated", cookie=cookie)
	self.server.shutdown()


@SH.on_req('HEAD', hasQ="admin")
def admin_page(self: SH, *args, **kwargs):
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	return self.html_main_page(user, cookie=cookie)


@SH.on_req('HEAD', hasQ="get_users")
def get_users(self: SH, *args, **kwargs):
	"""Send list of users"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	return self.send_json(Sconfig.get_users(), cookie=cookie)


@SH.on_req('HEAD', hasQ="update_user_perm")
def update_user_perm(self: SH, *args, **kwargs):
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	query = self.query
	username = query.get("username", [None])[0]
	permission = query.get("perms", [None])[0]
	
	allowed_paths_raw = query.get("allowed_paths", [None])[0]
	if allowed_paths_raw is not None:
		try:
			allowed_paths = json.loads(urllib.parse.unquote(allowed_paths_raw))
		except Exception:
			allowed_paths = None
	else:
		allowed_paths = None

	try:
		permission = int(permission)
	except Exception:
		permission = None

	if not (username is not None and permission is not None):
		return self.send_json({"status": "Failed", "message": "Username or permission not provided"}, cookie=cookie)

	USER = Sconfig.user_handler.get_user(username, temp=True)
	if not USER:
		return self.send_json({"status": "Failed", "message": "User not found"}, cookie=cookie)

	USER.set_permission_pack(permission)
	if allowed_paths is not None:
		USER.set_allowed_paths(allowed_paths)
		
	self_kick = False
	if user.uid == USER.uid and not USER.is_admin():
		self_kick = True
	
	if permission == USER.permission_pack:
		return self.send_json({"status": "Success", "message": "Permissions updated", "self_kick": self_kick}, cookie=cookie)


@SH.on_req('HEAD', hasQ="get_user_perm")
def get_user_perm(self: SH, *args, **kwargs):
	"""Send permission of a user"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	username = self.query.get("username", [None])[0]

	if not username:
		return self.send_json({"status": False, "message": "Username not provided"}, cookie=cookie)

	USER = Sconfig.user_handler.get_user(username, temp=True)
	if not USER:
		return self.send_json({"status": False, "message": "User not found"}, cookie=cookie)

	return self.send_json({
		"status": True, 
		"permissions_code": USER.permission_pack,
		"allowed_paths": json.dumps(USER.allowed_paths) if USER.allowed_paths else "[]"
	}, cookie=cookie)


@SH.on_req('HEAD', hasQ="add_user")  # added by Admin
def add_user(self: SH, *args, **kwargs):
	"""Add a user"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	username = self.query.get("username", [None])[0]
	password = self.query.get("password", [None])[0]
	permission = self.query.get("perms", [None])[0]
	
	allowed_paths_raw = self.query.get("allowed_paths", [None])[0]
	if allowed_paths_raw is not None:
		try:
			allowed_paths = json.loads(urllib.parse.unquote(allowed_paths_raw))
		except Exception:
			allowed_paths = None
	else:
		allowed_paths = None

	if not (username and password):
		return self.send_json({"status": False, "message": "Username or password not provided"}, cookie=cookie)

	if Sconfig.user_handler.get_user(username):
		return self.send_json({"status": False, "message": "Username already exists"}, cookie=cookie)

	new_user = Sconfig.user_handler.create_user(username, password)
	if not new_user:
		return self.send_json({"status": False, "message": "Failed to create user"}, cookie=cookie)

	if permission is not None:
		try:
			new_user.set_permission_pack(int(permission))
		except (TypeError, ValueError):
			pass

	if allowed_paths is not None:
		new_user.set_allowed_paths(allowed_paths)

	return self.send_json({"status": True, "message": f"<h2>User created.</h2> UID: {new_user.uid}"}, cookie=cookie)


@SH.on_req('HEAD', hasQ="delete_user")
def delete_user(self: SH, *args, **kwargs):
	"""Delete a user"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	username = self.query.get("username", [None])[0]

	if not username:
		return self.send_json({"status": False, "message": "Username not provided"}, cookie=cookie)

	USER = Sconfig.user_handler.get_user(username, temp=True)
	if not USER:
		return self.send_json({"status": False, "message": "User not found"}, cookie=cookie)

	if USER.is_admin():
		return self.send_json({"status": False, "message": "Cannot delete admin! Remove from admin 1st."}, cookie=cookie)

	if not Sconfig.user_handler.delete_user(username):  # delete user
		return self.send_json({"status": False, "message": "Failed to delete user"}, cookie=cookie)

	return self.send_json({"status": True, "message": "User deleted"}, cookie=cookie)


@SH.on_req('HEAD', hasQ="update")
def update(self: SH, *args, **kwargs):
	"""Check for update and return the latest version"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED)

	if not user.is_admin():
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	data = fetch_url("https://raw.githack.com/RaSan147/pyrobox/main/VERSION")
	if data:
		data = data.decode("utf-8").strip()
		ret = json.dumps({"update_available": data >
						 __version__, "latest_version": data})
		return self.return_txt(ret, code=HTTPStatus.OK, cookie=cookie)
	else:
		return self.return_txt("Failed to fetch latest version", code=HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)


@SH.on_req('HEAD', hasQ="size")
def get_size(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	url_path = kwargs.get('url_path', '')
	os_path = self.translate_path(url_path)

	stat = get_stat(os_path)
	if not stat:
		return self.send_json({"status": 0}, cookie=cookie)
	if os.path.isfile(os_path):
		size = stat.st_size
	else:
		size = get_dir_size(os_path)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.send_json({
		"status": 1,
		"byte": size,
		"humanbyte": humanbyte,
		"fmbyte": fmbyte
	},
		cookie=cookie)


@SH.on_req('HEAD', hasQ="size_n_count")
def get_size_n_count(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	url_path = kwargs.get('url_path', '')
	os_path = self.translate_path(url_path)

	stat = get_stat(os_path)
	if not stat:
		return self.send_json({"status": 0}, cookie=cookie)
	if os.path.isfile(os_path):
		count, size = 1, stat.st_size
	else:
		count, size = get_tree_count_n_size(os_path)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.send_json({
		"status": 1,
		"byte": size,
		"humanbyte": humanbyte,
		"fmbyte": fmbyte,
		"count": count
	},
		cookie=cookie)


@SH.on_req('HEAD', hasQ=("zip_id", "czip"))
def get_zip_id(self: SH, *args, **kwargs):
	"""Return ZIP ID status"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", code=HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)

	os_path = kwargs.get('path', '')
	spathsplit = kwargs.get('spathsplit', '')
	filename = spathsplit[-2] + ".zip"

	zid = None
	status = False
	message = ''

	try:
		zid = zip_manager.get_id(os_path)
		status = True

	except LimitExceed:
		message = f"DIRECTORY SIZE LIMIT EXCEED [CURRENT LIMIT: {humanbytes(Sconfig.max_zip_size)}]"

	except Exception:
		self.log_error(traceback.format_exc())
		message = 'Failed to create zip'

	return self.send_json({
		"status": status,
		"message": message,
		"zid": zid,
		"filename": filename
	}, cookie=cookie)


@SH.on_req('HEAD', hasQ="czip")
def create_zip(self: SH, *args, **kwargs):
	"""Create ZIP task and return ID

	# TODO: Move to Dynamic island
	"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", code=HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)

	url_path = kwargs.get('url_path', '')
	os_path = self.translate_path(url_path)

	# if not dir or not exists
	if not os.path.isdir(os_path):
		return self.send_error(code=HTTPStatus.NOT_FOUND, message="Directory not found", cookie=cookie)

	# dir_size = get_dir_size(path, limit=6*1024*1024*1024)

	# if dir_size == -1:
	# 	msg = "Directory size is too large, please contact the host"
	# 	return self.return_txt(HTTPStatus.OK, msg)

	displaypath = self.get_displaypath(url_path)

	title = "Creating ZIP"

	data = pt.directory_explorer_header().safe_substitute(
														  PY_PAGE_TITLE=title,
														  PY_PUBLIC_URL=CoreConfig.address(),
														  PY_DIR_TREE_NO_JS=dir_navigator(displaypath),
														  PY_ERROR_PAGE="",
														  PY_PAGE_SCRIPTS="")

	return self.return_txt(data, cookie=cookie)


@SH.on_req('HEAD', hasQ="zip")
def get_zip(self: SH, *args, **kwargs):
	"""Return ZIP file if available
	Else return progress of the task"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(code=HTTPStatus.UNAUTHORIZED, message="You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", code=HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)

	os_path = kwargs.get('path', '')
	spathsplit = kwargs.get('spathsplit', '')

	query = self.query
	msg = False

	def reply(status, msg=""):
		return self.send_json({
			"status": status,
			"message": msg
		}, cookie=cookie)

	if not os.path.isdir(os_path):
		msg = "Folder not found. Failed to create zip"
		self.log_error(msg)
		return reply("ERROR", msg)

	filename = spathsplit[-2] + ".zip"

	id = query["zid"][0]

	# IF NOT STARTED
	if zip_manager.calculating(id):
		return reply("CALCULATING")

	if not zip_manager.zip_id_status(id):
		t = zip_manager.archive_thread(os_path, id)
		t.start()

		return reply("SUCCESS", "ARCHIVING")

	if zip_manager.zip_id_status[id] == "DONE":
		if query("download"):
			zip_path = zip_manager.zip_ids[id]

			return self.return_file(zip_path, filename, download=True, cookie=cookie)

		if query("progress"):
			return reply("DONE")  # if query("progress") or no query

	# IF IN PROGRESS
	if zip_manager.zip_id_status[id] == "ARCHIVING":
		progress = zip_manager.zip_in_progress[id]
		# return self.return_txt("%.2f" % progress)
		return reply("PROGRESS", "%.2f" % progress)

	if zip_manager.zip_id_status[id].startswith("ERROR"):
		# return self.return_txt(zip_manager.zip_id_status[id])
		return reply("ERROR", zip_manager.zip_id_status[id])


@SH.on_req('HEAD', hasQ="json")
def send_ls_json(self: SH, *args, **kwargs):
	"""Send directory listing in JSON format"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	return list_directory_json(self, user=user)


subtitle_location_map = {}


@SH.on_req('HEAD', hasQ=("vid", "vid-data"))
def send_video_data(self: SH, *args, **kwargs):
	# SEND VIDEO DATA
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	vid_source = url_path

	content_type = self.guess_type(os_path)
	if content_type == self.guess_type(".mov"):
		content_type = self.guess_type(".mp4")  # add chrome support for .mov

	if not (content_type.startswith('video/') or content_type.startswith('audio/')):
		self.send_error(code=HTTPStatus.NOT_FOUND,
						message="THIS IS NOT A MEDIA FILE", cookie=cookie)
		return None

	displaypath = self.get_displaypath(url_path)

	title = get_titles(displaypath, file=True)

	subtitles = []
	if Sconfig.allow_subtitle:
		subtitles = extract_subtitles_from_file(
			os_path, output_format="vtt", output_dir=Sconfig.subtitles_dir)

	updated_subtitles = []
	default_ = True
	for label, sub_path in subtitles:
		random_uuid = uuid.uuid4().hex
		subtitle_location_map[random_uuid] = sub_path

		"""{
			kind: 'captions',
			label: 'English',
			srclang: 'en',
			src: '/path/to/captions.en.vtt',
			default: true,
		}"""
		updated_subtitles.append(
			{
				"kind": "captions",
				"label": label,
						"srclang": label,
						"src": f"/?sub={random_uuid}",
						"default": default_,
			}
		)
		default_ = False

	warning = ""

	supported_browser_media = [
		'video/mp4', 'video/ogg', 'video/webm',
		'audio/mp4', 'audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/webm', 'audio/flac', 'audio/aac', 'audio/opus'
	]
	if content_type not in supported_browser_media:
		warning = 'This media format may not be supported by your browser. Try downloading instead.'

	return self.send_json({
		"status": "success",
		"warning": warning,
		"video": vid_source,
		"title": displaypath.split("/")[-1],
		"content_type": content_type,
		"subtitles": updated_subtitles
	}, cookie=cookie)


@SH.on_req('HEAD', hasQ="sub")
def send_subtitle(self: SH, *args, **kwargs):
	# SEND SUBTITLE
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("?login")

	sub_id = self.query.get('sub', [None])[0]
	if sub_id not in subtitle_location_map:
		return self.send_error(code=HTTPStatus.NOT_FOUND, message="Subtitle not found", cookie=cookie)

	sub_path = subtitle_location_map[sub_id]

	return self.return_file(sub_path, cookie=cookie)


@SH.on_req('HEAD', hasQ="vid")
def send_video_page(self: SH, *args, **kwargs):
	# SEND VIDEO PLAYER
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	# vid_source = url_path
	content_type = self.guess_type(os_path)

	if not (content_type.startswith('video/') or content_type.startswith('audio/')):
		self.send_error(code=HTTPStatus.NOT_FOUND,
						message="THIS IS NOT A MEDIA FILE", cookie=cookie)
		return None

	r = []

	displaypath = self.get_displaypath(url_path)

	title = get_titles(displaypath, file=True)

	r.append(pt.directory_explorer_header().safe_substitute(
															PY_PAGE_TITLE=title,
															PY_PUBLIC_URL=CoreConfig.address(),
															PY_DIR_TREE_NO_JS=dir_navigator(displaypath),
															PY_ERROR_PAGE="",
															PY_PAGE_SCRIPTS=pt.video_page_assets()))

	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(encoded, cookie=cookie)


# ================================================================
# CODE EDITOR ENDPOINTS
# ================================================================

@SH.on_req('GET', hasQ=("edit", "edit-data"))
def send_code_data(self: SH, *args, **kwargs):
	"""Send code file data for editing"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	# Check if it's a supported text file
	supported_extensions = {
		'.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.htm', '.css', '.scss', '.less',
		'.json', '.xml', '.svg', '.txt', '.md', '.sql', '.java', '.cpp', '.c', '.h',
		'.go', '.php', '.rb', '.yaml', '.yml', '.sh', '.bash', '.conf', '.cfg',
		'.ini', '.properties', '.gradle', '.maven', '.toml', '.r'
	}
	
	file_ext = os.path.splitext(os_path)[1].lower()
	if file_ext not in supported_extensions:
		return self.send_error(
			code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
			message=f"File type {file_ext} is not supported for editing",
			cookie=cookie
		)

	# Check file size
	try:
		file_size = os.path.getsize(os_path)
	except OSError:
		return self.send_error(
			code=HTTPStatus.NOT_FOUND,
			message="File not found",
			cookie=cookie
		)

	# Read file content - limit preview for very large files
	try:
		# Detect original file's line ending format
		detected_line_ending = '\n'  # default
		try:
			with open(os_path, 'rb') as f:
				original_bytes = f.read(min(8192, file_size))  # Check first 8KB
				if b'\r\n' in original_bytes:
					detected_line_ending = 'CRLF'
				else:
					detected_line_ending = 'LF'
		except OSError:
			detected_line_ending = 'LF'  # default if detection fails
		
		# For read-only display of large files, limit to 16KB
		max_preview_size = 16 * 1024  # 16KB for read-only preview
		max_edit_size = 4 * 1024 * 1024  # 4MB for editing
		
		content_preview = ""
		is_truncated = False
		
		if file_size > max_edit_size:
			# Very large file - show 16KB preview only
			is_truncated = True
			with open(os_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
				content_preview = f.read(max_preview_size)
		else:
			# Normal file - read full content
			with open(os_path, 'r', encoding='utf-8', errors='replace', newline='') as f:
				content_preview = f.read()
	except Exception as e:
		return self.send_error(
			code=HTTPStatus.INTERNAL_SERVER_ERROR,
			message=f"Error reading file: {str(e)}",
			cookie=cookie
		)

	displaypath = self.get_displaypath(url_path)
	file_name = os.path.basename(os_path)

	# Auto-detect language from extension
	language_map = {
		'.py': 'python',
		'.js': 'javascript',
		'.ts': 'javascript',
		'.tsx': 'javascript',
		'.jsx': 'javascript',
		'.html': 'html',
		'.htm': 'html',
		'.css': 'css',
		'.scss': 'css',
		'.less': 'css',
		'.json': 'json',
		'.xml': 'xml',
		'.svg': 'xml',
		'.md': 'markdown',
		'.txt': 'text',
		'.sql': 'sql',
		'.java': 'java',
		'.cpp': 'cpp',
		'.c': 'c',
		'.h': 'cpp',
		'.go': 'go',
		'.php': 'php',
		'.rb': 'ruby',
		'.yaml': 'yaml',
		'.yml': 'yaml',
		'.sh': 'shell',
		'.bash': 'shell',
		'.conf': 'text',
		'.cfg': 'text',
		'.ini': 'text',
		'.properties': 'text',
		'.gradle': 'groovy',
		'.maven': 'xml',
		'.toml': 'toml',
		'.r': 'r',
	}

	language = language_map.get(file_ext, 'text')

	# Get file modification time for conflict detection
	try:
		mod_time = os.path.getmtime(os_path)
	except OSError:
		mod_time = 0

	return self.send_json({
		"status": "success",
		"file_name": file_name,
		"path": url_path,
		"content": content_preview,
		"language": language,
		"file_size": file_size,
		"is_truncated": is_truncated,
		"truncated_at": max_preview_size if is_truncated else None,
		"mod_time": mod_time,
		"line_ending": detected_line_ending,
		"read_only": not user.MODIFY or file_size > max_edit_size,  # Read-only if no permission or too large
		"can_edit": user.MODIFY and file_size <= max_edit_size  # Can edit only if has permission AND file <= 4MB
	}, cookie=cookie)


@SH.on_req('GET', hasQ="edit")
def send_code_editor_page(self: SH, *args, **kwargs):
	"""Send code editor page"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	# Basic file validation
	if not os.path.isfile(os_path):
		return self.send_error(
			code=HTTPStatus.NOT_FOUND,
			message="File not found",
			cookie=cookie
		)

	r = []

	displaypath = self.get_displaypath(url_path)
	title = get_titles(displaypath, file=True)

	r.append(pt.directory_explorer_header().safe_substitute(
															PY_PAGE_TITLE=title,
															PY_PUBLIC_URL=CoreConfig.address(),
															PY_DIR_TREE_NO_JS=dir_navigator(displaypath),
															PY_ERROR_PAGE="",
															PY_PAGE_SCRIPTS=pt.code_editor_assets()))

	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(encoded, cookie=cookie)


@SH.on_req('POST', hasQ="save-file")
def save_code_file(self: SH, *args, **kwargs):
	"""Save edited code file"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_json({
			"status": "error",
			"message": "Authentication required"
		}, code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	# Check MODIFY permission
	if not user.MODIFY:
		return self.send_json({
			"status": "error",
			"message": "You don't have permission to modify files"
		}, code=HTTPStatus.FORBIDDEN, cookie=cookie)

	os_path = kwargs.get('path', '')
	
	# Validate file exists
	if not os.path.isfile(os_path):
		return self.send_json({
			"status": "error",
			"message": "File not found"
		}, code=HTTPStatus.NOT_FOUND, cookie=cookie)

	post = DPD(self)

	# AUTHORIZE - verify post-type first
	uid = AUTHORIZE_POST(self, post, 'save-code')

	form = post.form

	if not uid:
		return self.send_json({
			"status": "error",
			"message": "Invalid request"
		}, code=HTTPStatus.BAD_REQUEST, cookie=cookie)

	# PASSWORD VALIDATION FIRST (before reading content)
	password = form.get_multi_field(verify_name='password', decode=True)[1]
	self.log_debug(f'code save password attempt by {user.UID}')
	
	if (user.MEMBER and not user.check_password(password)) or (not user.MEMBER and password != Sconfig.PASSWORD):
		self.log_info(f"Incorrect password for code save by {user.UID}")
		return self.send_json({
			"status": "error",
			"message": "Incorrect password"
		}, code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	try:
		# Now read content after password validation
		content_field = form.get_multi_field(verify_name='content', decode=True)
		content = content_field[1] if len(content_field) > 1 else ''
		
		mod_time_field = form.get_multi_field(verify_name='mod_time', decode=True)
		mod_time_str = mod_time_field[1] if len(mod_time_field) > 1 else '0'
		
		line_ending_field = form.get_multi_field(verify_name='line_ending', decode=True)
		line_ending_type = line_ending_field[1] if len(line_ending_field) > 1 else 'LF'
		
		try:
			mod_time = float(mod_time_str) if mod_time_str else 0.0
		except (ValueError, TypeError):
			mod_time = 0.0

		# Conflict detection: check if file was modified since user opened it
		current_mod_time = os.path.getmtime(os_path)
		if mod_time > 0 and current_mod_time > mod_time:
			return self.send_json({
				"status": "conflict",
				"message": "File was modified by another process. Please reload and try again.",
				"current_mod_time": current_mod_time
			}, code=HTTPStatus.CONFLICT, cookie=cookie)

		# Create backup before writing
		backup_path = os_path + '.backup'
		try:
			if os.path.exists(os_path):
				shutil.copy2(os_path, backup_path)
		except Exception as backup_error:
			logger.warning(f"Failed to create backup: {backup_error}")

		# Map user's line ending choice to actual separator
		separator_map = {
			'CRLF': '\r\n',
			'LF': '\n'
		}
		separator = separator_map.get(line_ending_type, '\n')
		
		# Write file atomically using temp file + rename
		temp_path = os_path + '.tmp'
		try:
			# Ensure content is string
			if isinstance(content, bytes):
				content = content.decode('utf-8', errors='replace')
			
			# Apply original file's line ending format to new content
			content = separator.join(content.splitlines())
			
			# Write with newline='' to prevent Python's automatic line ending conversion on Windows
			with open(temp_path, 'w', encoding='utf-8', errors='replace', newline='') as f:
				f.write(content)
			# Atomic rename
			if os.name == 'nt':  # Windows requires removing target first
				if os.path.exists(os_path):
					os.remove(os_path)
			shutil.move(temp_path, os_path)
		except Exception as write_error:
			# Restore from backup on write failure
			if os.path.exists(backup_path):
				try:
					shutil.copy2(backup_path, os_path)
				except OSError:
					pass
			raise write_error

		# Log the edit
		username = user.username if hasattr(user, 'username') else 'unknown'
		logger.info(f"File edited by {username}: {os_path} ({len(content)} bytes)")

		new_mod_time = os.path.getmtime(os_path)

		return self.send_json({
			"status": "success",
			"message": "File saved successfully",
			"mod_time": new_mod_time
		}, cookie=cookie)

	except Exception as e:
		logger.error(f"Error saving file: {e}")
		return self.send_json({
			"status": "error",
			"message": f"Error saving file: {str(e)}"
		}, code=HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)


@SH.on_req('GET', hasQ="code_editor_script")
def send_code_editor_script(self: SH, *args, **kwargs):
	"""Send code editor script"""
	return self.send_script(pt.code_editor_script())


if CoreConfig.dev_mode:
	SH.alt_directory(
		dir=Sconfig.assets_dir,
		method='HEAD',
		url_regex="/@assets/.*"
	)


@SH.on_req('HEAD', hasQ="style")
def send_style(self: SH, *args, **kwargs):
	"""Send style sheet"""
	return self.send_css(pt.style_css())


@SH.on_req('HEAD', hasQ="script_global")
def send_script_global(self: SH, *args, **kwargs):
	"""Send global script"""
	return self.send_script(pt.script_global())


@SH.on_req('HEAD', hasQ="asset_script")
def send_script(self: SH, *args, **kwargs):
	"""Send script"""
	return self.send_script(pt.assets_script())


@SH.on_req('HEAD', hasQ="theme_script")
def send_theme_script(self: SH, *args, **kwargs):
	"""Send theme script"""
	return self.send_script(pt.theme_script())


@SH.on_req('HEAD', hasQ="page_handler_script")
def send_page_handler_script(self: SH, *args, **kwargs):
	"""Send page handler script"""
	return self.send_script(pt.page_handler_script())


@SH.on_req('HEAD', hasQ="video_page_script")
def send_video_script(self: SH, *args, **kwargs):
	"""Send video script"""
	return self.send_script(pt.video_page_script())


@SH.on_req('HEAD', hasQ="video_css")
def send_video_css(self: SH, *args, **kwargs):
	"""Send bundled Plyr CSS (offline-safe, no CDN)"""
	return self.send_css(pt.video_css())


@SH.on_req('HEAD', hasQ="plyr_js")
def send_plyr_js(self: SH, *args, **kwargs):
	"""Send bundled Plyr JS (offline-safe, no CDN)"""
	return self.send_script(pt.plyr_js())


@SH.on_req('HEAD', hasQ="admin_page_script")
def send_admin_script(self: SH, *args, **kwargs):
	"""Send admin script"""
	return self.send_script(pt.admin_page_script())


@SH.on_req('HEAD', hasQ="file_list_script")
def send_file_list_script(self: SH, *args, **kwargs):
	"""Send file list script"""
	return self.send_script(pt.file_list_script())


@SH.on_req('HEAD', hasQ="error_page_script")
def send_error_page_script(self: SH, *args, **kwargs):
	"""Send error page script"""
	return self.send_script(pt.error_page_script())


@SH.on_req('HEAD', hasQ="zip_page_script")
def send_zip_page_script(self: SH, *args, **kwargs):
	"""Send zip page script"""
	return self.send_script(pt.zip_page_script())


@SH.on_req('HEAD', hasQ="login")
def login_page(self: SH, *args, **kwargs):
	"""Send login page"""
	user, cookie = Sconfig.authorize_user(self)

	if user and not user.is_guest():
		return self.redirect("/")

	return self.send_text(pt.login_page())


@SH.on_req('HEAD', hasQ="signup")
def signup_page(self: SH, *args, **kwargs):
	"""Send signup page"""
	user, cookie = Sconfig.authorize_user(self)

	if user and not user.is_guest():
		return self.redirect("/")

	if Sconfig.cli_args.no_signup:
		return self.send_error(code=HTTPStatus.SERVICE_UNAVAILABLE, message="Signup is disabled")

	return self.send_text(pt.signup_page())


@SH.on_req('HEAD', hasQ="logout")
def logout(self: SH, *args, **kwargs):
	"""Logout user"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.redirect("/")

	cookie = u_mgmt.clear_user_cookie()
	return self.send_text(pt.login_page(), cookie=cookie)


@SH.on_req('HEAD', hasQ="folder_data")
def get_folder_data(self: SH, *args, **kwargs):
	"""Send folder data"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:
		return self.send_json({
			"status": 0,
			"error_code": HTTPStatus.UNAUTHORIZED,
			"error_message": "You must be logged in to access this data.",

		}, cookie=cookie)

	os_path = kwargs.get('path', '')

	if not user.VIEW:
		return self.send_json({
			"status": 0,
			"error_code": HTTPStatus.UNAUTHORIZED,
			"error_message": "You don't have permission to view this folder",

		}, cookie=cookie)

	try:
		if not os.path.isdir(os_path):
			return self.send_json({"status": 0,
								   "warning": "Folder not found"}, cookie=cookie)

	except Exception as e:
		err = traceback.format_exc()
		return self.send_json({
			"status": 0,
			"error_code": HTTPStatus.NOT_FOUND,
			"error_message": str(e),

		})

	data = list_directory(self, os_path, user, cookie=cookie)

	if data:
		return self.send_json(data, cookie=cookie)


@SH.on_req('GET')
def default_get(self: SH, filename=None, *args, **kwargs):
	"""Serve a GET request."""
	user, cookie = Sconfig.authorize_user(self)

	# print("/"*50)
	# print(user.permission)
	# print("/"*50)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	os_path = kwargs.get('path', '')

	if os.path.isdir(os_path):
		parts = urllib.parse.urlsplit(self.path)
		# Match CPython http.server: treat %2f / %2F as an existing trailing slash
		if not directory_url_has_trailing_slash(parts.path):
			# redirect browser - doing basically what apache does
			self.send_response(code=HTTPStatus.MOVED_PERMANENTLY)
			new_parts = (parts[0], parts[1], parts[2] + '/',
						 parts[3], parts[4])
			new_url = urllib.parse.urlunsplit(new_parts)
			self.send_header("Location", new_url)
			self.send_header("Content-Length", "0")
			self.end_headers()
			return None
		for index in "index.html", "index.htm":
			index = xpath(os_path, index)
			if is_file(index):
				os_path = index
				break
		else:
			return list_directory_html(self, os_path, user, cookie=cookie)

	# check for trailing "/" which should return 404. See Issue17324
	# The test for this was added in test_httpserver.py
	# However, some OS platforms accept a trailingSlash as a filename
	# See discussion on python-dev and Issue34711 regarding
	# parsing and rejection of filenames with a trailing slash

	if os_path.endswith("/"):
		self.send_error(code=HTTPStatus.NOT_FOUND,
						message="File not found", cookie=cookie)
		return None

	# else:

	if (not user.DOWNLOAD) or user.NOPERMISSION:
		return self.send_error(code=HTTPStatus.SERVICE_UNAVAILABLE, message="Download is disabled", cookie=cookie)

	if not os.path.exists(os_path):
		return self.send_error(code=HTTPStatus.NOT_FOUND, message="File not found", cookie=cookie)
	return self.return_file(os_path, filename, cookie=cookie)


# TODO check against user_mgmt
def AUTHORIZE_POST(req: SH, post: DPD, post_type=''):
	"""Check if the user is authorized to post"""

	# START
	post.start()
	form = post.form

	verify_1 = form.get_multi_field(
		verify_name='post-type', verify_msg=post_type, decode=T)

	return verify_1[1]


@SH.on_req('POST', hasQ="do_login")
def handle_login_post(self: SH, *args, **kwargs):
	"""Handle login post"""
	user, cookie = Sconfig.authorize_user(self)

	if user and not user.is_guest():
		return self.redirect("/")

	post = DPD(self)

	AUTHORIZE_POST(self, post, 'login')

	form = post.form

	username = form.get_multi_field(verify_name='username', decode=T)[1]

	if not username or not username.strip():
		return self.send_json({"status": "failed", "message": "Username not provided"}, cookie=cookie)

	username = username.strip()

	# GET PASSWORD
	password = form.get_multi_field(verify_name='password', decode=T)[1]

	if not password:
		return self.send_json({"status": "failed", "message": "Password not provided"}, cookie=cookie)

	user = Sconfig.user_handler.get_user(username)
	if not user:
		return self.send_json({"status": "failed", "message": "User not found"}, cookie=cookie)

	if not user.check_password(password):
		return self.send_json({"status": "failed", "message": "Incorrect password"}, cookie=cookie)

	cookie = user.create_cookie()

	return self.send_json({"status": "success", "message": "Login successful, if not Auto-redirecting, kindly Refresh"}, cookie=cookie)


@SH.on_req('POST', hasQ="do_signup")
def handle_signup_post(self: SH, *args, **kwargs):
	"""Handle signup post"""
	user, cookie = Sconfig.authorize_user(self)

	if user and not user.is_guest():
		return self.redirect("/")

	if Sconfig.cli_args.no_signup:
		return self.send_error(code=HTTPStatus.SERVICE_UNAVAILABLE, message="Signup is disabled")

	post = DPD(self)

	AUTHORIZE_POST(self, post, 'signup')

	form = post.form

	username = form.get_multi_field(verify_name='username', decode=T)[1]

	if not username or not username.strip():
		return self.send_json({"status": "failed", "message": "Username not provided"}, cookie=cookie)

	username = username.strip()

	# GET PASSWORD
	password = form.get_multi_field(verify_name='password', decode=T)[1]

	if not password:
		return self.send_json({"status": "failed", "message": "Password not provided"}, cookie=cookie)

	user = Sconfig.user_handler.get_user(username)
	if user:
		return self.send_json({"status": "failed", "message": "Username is already in use!"}, cookie=cookie)

	user = Sconfig.user_handler.create_user(username, password)
	if not user:
		return self.send_json({"status": "failed", "message": "Failed to create user"}, cookie=cookie)

	cookie = user.create_cookie()

	return self.send_json({"status": "success", "message": "Signup successful"}, cookie=cookie)


# TODO check against user_mgmt
@SH.on_req('POST', hasQ="upload")
def upload(self: SH, *args, **kwargs):
	"""GET Uploaded files"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.redirect("?login")

	if user.NOPERMISSION or (not user.UPLOAD):
		return self.send_txt("Upload not allowed", code=HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'upload')

	form = post.form

	if not uid:
		return None

	# uploaded_files = [] # Uploaded folder list

	upload_handler = UploadHandler(uid)

	upload_thread = threading.Thread(target=upload_handler.start, args=(self,))
	upload_thread.start()

	def remove_from_temp(temp_fn):
		try:
			upload_handler.kill()
		except OSError:
			pass

		finally:
			if temp_fn in CoreConfig.temp_files:
				CoreConfig.temp_files.remove(temp_fn)

	# PASSWORD SYSTEM
	password = form.get_multi_field(verify_name='password', decode=T)[1]

	self.log_debug(f'post password: {[password]} by client')

	# readline returns password with \r\n at end
	if (user.MEMBER and not user.check_password(password)) or (not user.MEMBER and password != Sconfig.PASSWORD):
		self.log_info(f"Incorrect password by {uid}")

		return self.send_txt("Incorrect password", code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	while post.remainbytes > 0:
		# reads the next line and returns the file name/relative path
		fn = form.get_file_name(ignore_folder=True)
		if fn is None:  # folder
			post.skip(4)  # skip the next 3 lines and the boundary
			continue

		if not fn or not fn.strip():
			return self.send_error(code=HTTPStatus.BAD_REQUEST, message="Can't find out file name...", cookie=cookie)

		# Reject absolute / drive / traversal names; never os.path.join with raw fn
		# (join discards the served root when fn is absolute).
		fn = validate_client_relpath(fn, allow_leading_slash=False)
		if fn is None:
			logger.warning(f"Invalid upload filename by {uid}")
			upload_handler.kill()
			return self.send_txt("Invalid Path", code=HTTPStatus.BAD_REQUEST, cookie=cookie)

		rltv_path = posixpath.join(url_path, fn)
		if not self.path_safety_check(fn, rltv_path):
			logger.warning(f"Invalid Path: {fn} - {rltv_path} by {uid}")
			upload_handler.kill()
			return self.send_txt("Invalid Path:  " + rltv_path, code=HTTPStatus.BAD_REQUEST, cookie=cookie)

		os_f_path = self.resolve_child_path(url_path, fn)
		if not os_f_path:
			logger.warning(f"Upload path escaped root: {fn} by {uid}")
			upload_handler.kill()
			return self.send_txt("Invalid Path:  " + rltv_path, code=HTTPStatus.BAD_REQUEST, cookie=cookie)

		# make directory if not exists
		f_dir = os.path.dirname(os_f_path)
		if not self.path_is_under_directory(f_dir):
			upload_handler.kill()
			return self.send_txt("Invalid Path:  " + rltv_path, code=HTTPStatus.BAD_REQUEST, cookie=cookie)

		try:
			os.makedirs(f_dir, exist_ok=True)
		except OSError:
			return self.send_txt("Can't create directory to write, do you have permission to write?", code=HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)

		real_fn = os.path.basename(fn)
		temp_fn = os.path.join(f_dir, ".LStemp-" + real_fn + '.tmp')
		if not self.path_is_under_directory(temp_fn):
			upload_handler.kill()
			return self.send_txt("Invalid Path:  " + rltv_path, code=HTTPStatus.BAD_REQUEST, cookie=cookie)
		CoreConfig.temp_files.add(temp_fn)

		line = post.get()  # content type
		line = post.get()  # line gap

		# ORIGINAL FILE STARTS FROM HERE
		out = None
		try:
			out = open(temp_fn, 'wb', buffering=Sconfig.max_buffer_size)  # noqa: SIM115 — ownership passed to upload worker
			preline = post.get()
			while post.remainbytes > 0 and not upload_handler.error:
				line = post.get()
				if post.boundary in line:
					preline = preline[0:-1]
					if preline.endswith(b'\r'):
						preline = preline[0:-1]

					upload_handler.upload(out, 'w', preline)
					# out.write(preline)
					# uploaded_files.append(rltv_path,)
					break
				else:
					upload_handler.upload(out, 'w', preline)
					# out.write(preline)
					preline = line

			upload_handler.upload(out, 's', (os_f_path, user.MODIFY))
			out = None  # ownership transferred to upload worker

			if upload_handler.error and not upload_handler.active:
				remove_from_temp(temp_fn)
				return self.send_error(code=HTTPStatus.INTERNAL_SERVER_ERROR, message=upload_handler.error, cookie=cookie)

		except (IOError, OSError):
			traceback.print_exc()
			return self.send_txt("Can't create file to write, do you have permission to write?", code=HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)
		finally:
			if out is not None and not out.closed:
				out.close()

	upload_handler.active = False  # will take no further inputs
	upload_thread.join()

	if upload_handler.error:
		return self.send_error(code=HTTPStatus.INTERNAL_SERVER_ERROR, message=upload_handler.error, cookie=cookie)

	return self.return_txt("File(s) uploaded", cookie=cookie)


@SH.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SH, *args, **kwargs):
	"""Move 2 recycle bin"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"status": False, "head": "Failed", "body": "You have no permission to delete."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-f')
	form = post.form

	if CoreConfig.disabled_func["send2trash"]:
		return self.send_json({"status": False, "head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)

	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.resolve_child_path(url_path, filename)
	if not os_f_path:
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	self.log_warning(f'<-send2trash-> {os_f_path} by {[uid]}')

	try:
		if CoreConfig.OS == 'Android':
			raise InterruptedError
		send2trash(os_f_path)
		return self.send_json({"status": True, "head": "Success", "body": "Successfully Moved To Recycle bin: " + rel_path}, cookie=cookie)
	except TrashPermissionError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except InterruptedError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except Exception as e:
		traceback.print_exc()
		msg = "<b>" + rel_path + "</b> " + e.__class__.__name__

	return self.send_json({"status": False, "head": "Failed", "body": msg}, cookie=cookie)


@SH.on_req('POST', hasQ="del-p")
def del_permanently(self: SH, *args, **kwargs):
	"""DELETE files permanently"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"status": False, "head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-p')
	form = post.form

	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.resolve_child_path(url_path, filename)
	if not os_f_path:
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	self.log_warning(f'Perm. DELETED {os_f_path} by {[uid]}')

	try:
		if os.path.isfile(os_f_path):
			os.remove(os_f_path)
		else:
			shutil.rmtree(os_f_path, ignore_errors=True)

		return self.send_json({"status": True, "head": "Success", "body": "PERMANENTLY DELETED:  " + rel_path}, cookie=cookie)

	except Exception as e:
		traceback.print_exc()
		return self.send_json({"status": False, "head": "Failed", "body": "<b>" + rel_path + "</b> " + e.__class__.__name__}, cookie=cookie)


@SH.on_req('POST', hasQ="rename")
def rename_content(self: SH, *args, **kwargs):
	"""Rename files"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"status": False, "head": "Failed", "body": "Renaming is disabled."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'rename')
	form = post.form

	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	new_name = form.get_multi_field(verify_name='data', decode=T)[1]

	if not new_name or not new_name.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + new_name}, cookie=cookie)

	new_name = new_name.strip()

	rel_path = self.get_rel_path(filename)
	new_rel_path = self.get_rel_path(new_name)

	if not self.path_safety_check(filename, new_name, rel_path, new_rel_path):
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.resolve_child_path(url_path, filename)
	os_new_f_path = self.resolve_child_path(url_path, new_name)
	if not os_f_path or not os_new_f_path:
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	self.log_warning(f'Renamed "{os_f_path}" to "{os_new_f_path}" by {[uid]}')

	try:
		os.rename(os_f_path, os_new_f_path)
		display_old = urllib.parse.unquote(filename, errors='surrogatepass')
		return self.send_json({"status": True, "head": "Success", "body": f"<span style='white-space:pre-wrap'>Renamed: {display_old} → {new_name}</span>"}, cookie=cookie)
	except Exception as e:
		return self.send_json({"status": False, "head": "Failed", "body": "<b>" + rel_path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + self.get_web_path(str(e), -1)}, cookie=cookie)


@SH.on_req('POST', hasQ="info")
def get_info(self: SH, *args, **kwargs):
	"""Get files permanently"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if user.NOPERMISSION:
		return self.send_json({"status": False, "head": "Failed", "body": "You have no permission to view."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	script = None

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'info')
	form = post.form

	# File link to move to check info

	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.resolve_child_path(url_path, filename)
	if not os_f_path:
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	self.log_warning(f'Info Checked "{os_f_path}" by: {[uid]}')

	if not os.path.exists(os_f_path):
		return self.send_json({"status": False, "head": "Failed", "body": "File/Folder Not Found"}, cookie=cookie)

	file_stat = get_stat(os_f_path)
	if not file_stat:
		return self.send_json({"status": False, "head": "Failed", "body": "Permission Denied"}, cookie=cookie)

	data = []
	data.append(["Name", urllib.parse.unquote(
		filename, errors='surrogatepass')])

	if os.path.isfile(os_f_path):
		data.append(["Type", "File"])
		if "." in filename:
			data.append(["Extension", filename.rpartition(".")[2]])

		size = file_stat.st_size
		data.append(["Size", humanbytes(size) + " (%i bytes)" % size])

	else:  # if os.path.isdir(xpath):
		data.append(["Type", "Folder"])
		# size = get_dir_size(xpath)

		data.append(["Total Files", '<span id="f_count">Please Wait</span>'])

		data.append(["Total Size", '<span id="f_size">Please Wait</span>'])
		script = '''
		tools.fetch_json(tools.full_path("''' + rel_path + '''?size_n_count")).then(resp => {
		// console.log(resp);
		if (resp.status) {
			size = resp.humanbyte;
			count = resp.count;
			document.getElementById("f_size").innerHTML = resp.humanbyte + " (" + resp.byte + " bytes)";
			document.getElementById("f_count").innerHTML = count;
		} else {
			throw new Error(resp.msg);
		}}).catch(err => {
		console.log(err);
		document.getElementById("f_size").innerHTML = "Error";
		});
		'''

	data.append(["Path", rel_path])

	def get_dt(time):
		return datetime.datetime.fromtimestamp(time)

	data.append(["Created on", get_dt(file_stat.st_ctime)])
	data.append(["Last Modified", get_dt(file_stat.st_mtime)])
	data.append(["Last Accessed", get_dt(file_stat.st_atime)])

	body = """<table class="properties-table">
<thead>
<tr>
<th>Property</th>
<th>Value</th>
</tr>
</thead>
<tbody>
"""
	for key, val in data:
		body += "<tr><td>{key}</td><td>{val}</td></tr>\n".format(
			key=key, val=val)
	body += "</tbody></table>"

	return self.send_json({"status": True, "head": "Properties", "body": body, "script": script}, cookie=cookie)


@SH.on_req('POST', hasQ="new_folder")
def new_folder(self: SH, *args, **kwargs):
	"""Create new folder"""
	user, cookie = Sconfig.authorize_user(self)

	if not user:  # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), code=HTTPStatus.UNAUTHORIZED)

	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"status": False, "head": "Failed", "body": "Permission denied."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'new_folder')
	form = post.form

	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.resolve_child_path(url_path, filename)
	if not os_f_path:
		return self.send_json({"status": False, "head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	self.log_warning(f'New Folder Created "{os_f_path}" by: {[uid]}')

	try:
		if os.path.exists(os_f_path):
			return self.send_json({"status": False, "head": "Failed", "body": "Folder Already Exists:  " + rel_path}, cookie=cookie)
		if os.path.isfile(os_f_path):
			return self.send_json({"status": False, "head": "Failed", "body": "File Already Exists:  " + rel_path}, cookie=cookie)
		os.makedirs(os_f_path)
		return self.send_json({"status": True, "head": "Success", "body": "New Folder Created:  " + rel_path}, cookie=cookie)

	except Exception as e:
		self.log_error(traceback.format_exc())
		return self.send_json({"status": False, "head": "Failed", "body": f"<b>{rel_path}</b><br><b>{e.__class__.__name__}</b>"}, cookie=cookie)


@SH.on_req('POST')
def default_post(self: SH, *args, **kwargs):
	raise PostError("Bad Request")


# proxy for old versions
def run(*args, **kwargs):
	SH.allow_CORS(method='GET', origin='*')

	runner = pyroboxRunner(handler=SH, *args, **kwargs)

	url = CoreConfig.address()

	if cli_args.qr and not CoreConfig.disabled_func["pyqrcode"]:
		# Create a QR code on terminal
		try:
			url = pyqrcode.create(url, error='L')
			print(url.terminal('black', 'white', quiet_zone=1))
		except Exception as e:
			logger.error(f"Error generating QR code: {e}")

	runner.run()


if __name__ == '__main__':
	run(port=45454)
