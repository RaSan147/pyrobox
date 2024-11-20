


# TODO
# ----------------------------------------------------------------
# * ADD MORE FILE TYPES
# * ADD SEARCH

import hashlib
import os
#import sys
import posixpath
import shutil

import datetime


import threading
import urllib.parse
import urllib.request

#import subprocess
import json
from http import HTTPStatus
from http.cookies import SimpleCookie


import traceback
import uuid

from .pyroboxCore import config as CoreConfig, logger, DealPostData as DPD, runner as pyroboxRunner, tools, reload_server, __version__ as pyroboxCore_version

from .tools import xpath, EXT, make_dir, os_scan_walk, is_file, Text_Box

from .pyrobox_ServerHost import ServerConfig, ServerHost as SH



__version__ = '0.9.7'
true = T = True
false = F = False
enc = "utf-8"

###########################################
# ADD COMMAND LINE ARGUMENTS
###########################################
from ._arg_parser import main as arg_parser
arg_parser(CoreConfig)
cli_args = CoreConfig.parser.parse_known_args()[0]
CoreConfig.PASSWORD = cli_args.password

logger.info(tools.text_box("Server Config", *({i: getattr(cli_args, i)} for i in vars(cli_args) if not (i.startswith("admin") or "password" in i))))


Sconfig = ServerConfig(cli_args=cli_args)





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
REQUIREMENTS= ['send2trash', 'natsort', 'pyqrcode']




if not os.path.isdir(CoreConfig.log_location):
	try:
		os.mkdir(path=CoreConfig.log_location)
	except Exception:
		CoreConfig.log_location ="./"

if not CoreConfig.disabled_func.get("send2trash"):
	try:
		from send2trash import send2trash, TrashPermissionError
	except Exception:
		CoreConfig.disabled_func["send2trash"] = True
		logger.warning("send2trash module not found, send2trash function disabled. Install it using `pip install send2trash`")


if not CoreConfig.disabled_func.get("natsort"):
	try:
		import natsort
	except Exception:
		CoreConfig.disabled_func["natsort"] = True
		logger.warning("natsort not found, falling back to default sorting. Install it using `pip install natsort`")

if not CoreConfig.disabled_func.get("pyqrcode"):
	try:
		import pyqrcode
	except ImportError:
		CoreConfig.disabled_func["pyqrcode"] = True
		logger.warning("pyqrcode module not found, QR code generation disabled. Install it using `pip install pyqrcode`")





   #############################################
  #				 HANDLER UTILS                #
 # Need to be loaded after CoreConfig is set #
#############################################

from ._fs_utils import get_titles, dir_navigator, get_dir_size, get_stat, get_tree_count_n_size, fmbytes, humanbytes, UploadHandler
from . import _page_templates as pt
from ._exceptions import LimitExceed
from ._zipfly_manager import ZIP_Manager
from ._list_maker import list_directory, list_directory_json, list_directory_html
from ._sub_extractor import extract_subtitles_from_file




########## ZIP MANAGER ################################
# max_zip_size = 6*1024*1024*1024
zip_manager = ZIP_Manager(CoreConfig, size_limit=Sconfig.max_zip_size, zip_temp_dir=Sconfig.zip_dir)

#######################################################



########## PAGE TEMPLATES ###############################
pt.pt_config.dev_mode = CoreConfig.dev_mode

#########################################################






# TODO check against user_mgmt
# download file from url using urllib
def fetch_url(url, file = None):
	try:
		with urllib.request.urlopen(url, timeout=5) as response:
			data = response.read() # a `bytes` object

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



def handle_user_cookie(self: SH):
	cookie = self.cookie
	#print(cookie)
	def get(k):
		x = cookie.get(k)
		if x is not None:
			return x.value
		return ""
	username = get("user")
	token = get("token")

	self.log_info("COOKIE", username, token)

	if not (username and token):
		return None

	user = Sconfig.user_handler.get_user(username)
	#self.log_info("TEMP_USER", user)
#	self.log_info("TEMP_TOKEN_CHECK", user.check_token(token))

	if user:
		if user.check_token(token):
			return user
		else:
			return None
	return None

def add_user_cookie(user):
	# add cookie with 1 year expire
	cookie = SimpleCookie()
	def x(k, v):
		nonlocal cookie
		cookie[k] = v
		cookie[k]["expires"] = 365*86400
		cookie[k]["path"] = "/"

	x("user", user.username)
	x("token", user.token_hex)
	x("permissions", user.permission_pack)
	return cookie

def clear_user_cookie():
	cookie = SimpleCookie()
	keys = ("user", "token", "permissions")
	for k in keys:
		cookie[k] = ""
		cookie[k]["expires"] = -1
		cookie[k]["path"] = "/"

	return cookie

def Authorize_user(self:SH):
	# do cookie stuffs and get user
	user = handle_user_cookie(self)

	# self.log_info("USER", user)


	if not user and Sconfig.GUESTS:
		user = Sconfig.guest_id # default guest user

	if not user:
		return None, clear_user_cookie()

	cookie = add_user_cookie(user)


	return user, cookie







@SH.on_req('HEAD', hasQ="type")
def get_page_type(self: SH, *args, **kwargs):
	"""Return type of the page"""
	user, cookie = Authorize_user(self)



	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')


	result= "unknown"

	if self.query("admin"):
		result = "admin"

	elif self.query("login"):
		result = "login"

	elif self.query("signup"):
		result = "signup"

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
	self.redirect('https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.ico')


@SH.on_req('HEAD', hasQ="about")
def get_version(self: SH, *args, **kwargs):
	"""Return version of the server"""
	return self.send_text(f"Pyrobox Server v{__version__} (pyroboxCore v{pyroboxCore_version}) by RaSan147 (https://github.com/RaSan147/pyrobox)")

@SH.on_req('HEAD', hasQ="version")
def get_version(self: SH, *args, **kwargs):
	"""Return version of the server"""
	return self.send_text(f"{__version__}")

@SH.on_req('HEAD', hasQ="qr")
def get_qr(self: SH, *args, **kwargs):
	"""Return QR code for easy access"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if CoreConfig.disabled_func["pyqrcode"]:
		return self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "QR code generation is disabled", cookie=cookie)

	query = self.query.get("qr", [None])[0]
	url = query or CoreConfig.address()

	if len(url) > 2048:
		return self.send_error(HTTPStatus.BAD_REQUEST, "URL too long", cookie=cookie)

	md5_url = hashlib.md5(url.encode()).hexdigest() + hashlib.sha256(url.encode()).hexdigest()
	qr_path = xpath(CoreConfig.temp_dir, f"QR-{md5_url}.svg")

	if not os.path.exists(qr_path):
		pyqrcode.create(url).svg(file=qr_path, scale=5)

	return self.send_file(qr_path, cookie=cookie)


@SH.on_req('HEAD', hasQ="reload")
def reload(self: SH, *args, **kwargs):
	# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)


	CoreConfig.reload = True
	self.send_text("Reload initiated")

	reload_server()

@SH.on_req('HEAD', hasQ="shutdown")
def shutdown(self: SH, *args, **kwargs):
	# SHUTS DOWN THE SERVER. VULNERABLE
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	self.send_text("Shut down initiated", cookie=cookie)
	self.server.shutdown()

@SH.on_req('HEAD', hasQ="admin")
def admin_page(self: SH, *args, **kwargs):
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	return self.html_main_page(user, cookie=cookie)




@SH.on_req('HEAD', hasQ="get_users")
def get_users(self: SH, *args, **kwargs):
	"""Send list of users"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)



	return self.send_json(Sconfig.get_users(), cookie=cookie)


@SH.on_req('HEAD', hasQ="update_user_perm")
def update_user_perm(self: SH, *args, **kwargs):
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	query = self.query
	username = query.get("username", [None])[0]
	permission = query.get("perms", [None])[0]

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

	self.log_warning(f'Updating permission of "{username}" to "{permission}" by {[USER.uid]}')

	return self.send_json({"status": "Success", "message": "Permission updated"}, cookie=cookie)


@SH.on_req('HEAD', hasQ="get_user_perm")
def get_user_perm(self: SH, *args, **kwargs):
	"""Send permission of a user"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	username = self.query.get("username", [None])[0]

	if not username:
		return self.send_json({"status": False, "message": "Username not provided"}, cookie=cookie)

	USER = Sconfig.user_handler.get_user(username, temp=True)
	if not USER:
		return self.send_json({"status": False, "message": "User not found"}, cookie=cookie)

	return self.send_json({"status": True, "permissions_code": USER.permission_pack}, cookie=cookie)


@SH.on_req('HEAD', hasQ="add_user") # added by Admin
def add_user(self: SH, *args, **kwargs):
	"""Add a user"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	username = self.query.get("username", [None])[0]
	password = self.query.get("password", [None])[0]

	if not (username and password):
		return self.send_json({"status": False, "message": "Username or password not provided"}, cookie=cookie)

	if Sconfig.user_handler.get_user(username):
		return self.send_json({"status": False, "message": "Username already exists"}, cookie=cookie)

	new_user = Sconfig.user_handler.create_user(username, password)
	if not new_user:
		return self.send_json({"status": False, "message": "Failed to create user"}, cookie=cookie)

	return self.send_json({"status": True, "message": f"<h2>User created.</h2> UID: {new_user.uid}"}, cookie=cookie)



@SH.on_req('HEAD', hasQ="delete_user")
def delete_user(self: SH, *args, **kwargs):
	"""Delete a user"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

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

	if not Sconfig.user_handler.delete_user(username): # delete user
		return self.send_json({"status": False, "message": "Failed to delete user"}, cookie=cookie)

	return self.send_json({"status": True, "message": "User deleted"}, cookie=cookie)



@SH.on_req('HEAD', hasQ="update")
def update(self: SH, *args, **kwargs):
	"""Check for update and return the latest version"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED)

	if not user.is_admin():
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)



	data = fetch_url("https://raw.githack.com/RaSan147/pyrobox/main/VERSION")
	if data:
		data  = data.decode("utf-8").strip()
		ret = json.dumps({"update_available": data > __version__, "latest_version": data})
		return self.return_txt(ret, HTTPStatus.OK, cookie=cookie)
	else:
		return self.return_txt("Failed to fetch latest version", HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)


@SH.on_req('HEAD', hasQ="size")
def get_size(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)



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
	return self.send_json({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte}, cookie=cookie)

@SH.on_req('HEAD', hasQ="size_n_count")
def get_size_n_count(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)



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
	return self.send_json({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte,
														"count": count}, cookie=cookie)


@SH.on_req('HEAD', hasQ=("zip_id", "czip"))
def get_zip_id(self: SH, *args, **kwargs):
	"""Return ZIP ID status"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)


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
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)

	url_path = kwargs.get('url_path', '')
	os_path = self.translate_path(url_path)

	# if not dir or not exists
	if not os.path.isdir(os_path):
		return self.send_error(HTTPStatus.NOT_FOUND, "Directory not found", cookie=cookie)


	# dir_size = get_dir_size(path, limit=6*1024*1024*1024)

	# if dir_size == -1:
	# 	msg = "Directory size is too large, please contact the host"
	# 	return self.return_txt(HTTPStatus.OK, msg)

	displaypath = self.get_displaypath(url_path)

	title = "Creating ZIP"

	data = pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
											PY_PUBLIC_URL=CoreConfig.address(),
											PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

	return self.return_txt(data, cookie=cookie)



@SH.on_req('HEAD', hasQ="zip")
def get_zip(self: SH, *args, **kwargs):
	"""Return ZIP file if available
	Else return progress of the task"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	if not user.ZIP:
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if not (user.DOWNLOAD and user.VIEW):
		return self.send_error(HTTPStatus.UNAUTHORIZED, "You are not authorized to perform this action", cookie=cookie)

	if CoreConfig.disabled_func["zip"]:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)



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

			return self.return_file(zip_path, filename, True, cookie=cookie)


		if query("progress"):
			return reply("DONE") #if query("progress") or no query

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
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	return list_directory_json(self)


subtitle_location_map = {}

@SH.on_req('HEAD', hasQ=("vid", "vid-data"))
def send_video_data(self: SH, *args, **kwargs):
	# SEND VIDEO DATA
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')



	vid_source = url_path

	content_type = self.guess_type(os_path)
	if content_type == self.guess_type(".mov"):
		content_type = self.guess_type(".mp4") # add chrome support for .mov

	if not content_type.startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE", cookie=cookie)
		return None


	displaypath = self.get_displaypath(url_path)

	title = get_titles(displaypath, file=True)

	subtitles = []
	if Sconfig.allow_subtitle:
		subtitles = extract_subtitles_from_file(os_path, output_format="vtt", output_dir=Sconfig.subtitles_dir)

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

	if content_type not in ['video/mp4', 'video/ogg', 'video/webm']:
		warning = ('<h2>It seems HTML player may not be able to play this Video format, Try Downloading</h2>')

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
	user, cookie = Authorize_user(self)

	if not user:
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	sub_id = self.query.get('sub', [None])[0]
	if sub_id not in subtitle_location_map:
		return self.send_error(HTTPStatus.NOT_FOUND, "Subtitle not found", cookie=cookie)

	sub_path = subtitle_location_map[sub_id]

	return self.return_file(sub_path, cookie=cookie)




@SH.on_req('HEAD', hasQ="vid")
def send_video_page(self: SH, *args, **kwargs):
	# SEND VIDEO PLAYER
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	# vid_source = url_path
	content_type = self.guess_type(os_path)

	if not content_type.startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE", cookie=cookie)
		return None

	r = []

	displaypath = self.get_displaypath(url_path)



	title = get_titles(displaypath, file=True)

	r.append(pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
													PY_PUBLIC_URL=CoreConfig.address(),
													PY_DIR_TREE_NO_JS= dir_navigator(displaypath)))

	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(encoded, cookie=cookie)



if CoreConfig.dev_mode:
	SH.alt_directory(
		dir = Sconfig.assets_dir,
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
	return self.send_script(pt.script_global(), content_type="text/javascript")

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
	user, cookie = Authorize_user(self)

	if user:
		return self.redirect("/")

	return self.send_text(pt.login_page())

@SH.on_req('HEAD', hasQ="signup")
def signup_page(self: SH, *args, **kwargs):
	"""Send signup page"""
	user, cookie = Authorize_user(self)

	if user:
		return self.redirect("/")

	if Sconfig.cli_args.no_signup:
		return self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Signup is disabled")

	return self.send_text(pt.signup_page())


@SH.on_req('HEAD', hasQ="logout")
def logout(self: SH, *args, **kwargs):
	"""Logout user"""
	user, cookie = Authorize_user(self)

	if not user:
		return self.redirect("/")

	cookie = clear_user_cookie()
	return self.send_text(pt.login_page(), cookie=cookie)









@SH.on_req('HEAD', hasQ="folder_data")
def get_folder_data(self: SH, *args, **kwargs):
	"""Send folder data"""
	user, cookie = Authorize_user(self)

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


@SH.on_req('HEAD')
def default_get(self: SH, filename=None, *args, **kwargs):
	"""Serve a GET request."""
	user, cookie = Authorize_user(self)

	#print("/"*50)
	#print(user.permission)
	#print("/"*50)

	if not user: # guest or not will be handled in Authentication
		return self.redirect("?login")


	os_path = kwargs.get('path', '')

	if os.path.isdir(os_path):
		parts = urllib.parse.urlsplit(self.path)
		if not parts.path.endswith('/'):
			# redirect browser - doing basically what apache does
			self.send_response(HTTPStatus.MOVED_PERMANENTLY)
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
		self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie=cookie)
		return None



	# else:

	if (not user.DOWNLOAD) or user.NOPERMISSION:
		return self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Download is disabled", cookie=cookie)

	if not os.path.exists(os_path):
		return self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie=cookie)
	return self.return_file(os_path, filename, cookie=cookie)












# TODO check against user_mgmt
def AUTHORIZE_POST(req: SH, post:DPD, post_type=''):
	"""Check if the user is authorized to post"""

	# START
	post.start()
	form = post.form

	verify_1 = form.get_multi_field(verify_name='post-type', verify_msg=post_type, decode=T)

	return verify_1[1]


@SH.on_req('POST', hasQ="do_login")
def handle_login_post(self: SH, *args, **kwargs):
	"""Handle login post"""
	user, cookie = Authorize_user(self)

	if user:
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

	cookie = add_user_cookie(user)

	return self.send_json({"status": "success", "message": "Login successful, if not Auto-redirecting, kindly Refresh"}, cookie=cookie)


@SH.on_req('POST', hasQ="do_signup")
def handle_signup_post(self: SH, *args, **kwargs):
	"""Handle signup post"""
	user, cookie = Authorize_user(self)

	if user:
		return self.redirect("/")

	if Sconfig.cli_args.no_signup:
		return self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Signup is disabled")


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

	cookie = add_user_cookie(user)

	return self.send_json({"status": "success", "message": "Signup successful"}, cookie=cookie)




# TODO check against user_mgmt
@SH.on_req('POST', hasQ="upload")
def upload(self: SH, *args, **kwargs):
	"""GET Uploaded files"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.UPLOAD):
		return self.send_txt("Upload not allowed", HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)


	os_path = kwargs.get('path', '')
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

	if (user.MEMBER and not user.check_password(password)) or (not user.MEMBER and password != CoreConfig.PASSWORD): # readline returns password with \r\n at end
		self.log_info(f"Incorrect password by {uid}")

		return self.send_txt("Incorrect password", HTTPStatus.UNAUTHORIZED, cookie=cookie)

	while post.remainbytes > 0:
		fn = form.get_file_name() # reads the next line and returns the file name
		if not fn:
			return self.send_error(HTTPStatus.BAD_REQUEST, "Can't find out file name...", cookie=cookie)


		rltv_path = xpath(url_path, fn) # relative path (must be url path with / separator)

		if not self.path_safety_check(fn, rltv_path):
			return self.send_txt("Invalid Path:  " + rltv_path, HTTPStatus.BAD_REQUEST, cookie=cookie)

		temp_fn = xpath(os_path, ".LStemp-"+ fn +'.tmp')
		CoreConfig.temp_files.add(temp_fn)


		os_f_path = xpath(os_path, fn)



		line = post.get() # content type
		line = post.get() # line gap



		# ORIGINAL FILE STARTS FROM HERE
		try:
			out = open(temp_fn, 'wb', buffering=Sconfig.max_buffer_size)
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

			if upload_handler.error and not upload_handler.active:
				remove_from_temp(temp_fn)
				return self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, upload_handler.error, cookie=cookie)



		except (IOError, OSError):
			traceback.print_exc()
			return self.send_txt("Can't create file to write, do you have permission to write?", HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)


	upload_handler.active = False # will take no further inputs
	upload_thread.join()

	if upload_handler.error:
		return self.send_error(upload_handler.error, HTTPStatus.INTERNAL_SERVER_ERROR, cookie=cookie)



	return self.return_txt("File(s) uploaded", cookie=cookie)





@SH.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SH, *args, **kwargs):
	"""Move 2 recycle bin"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "You have no permission to delete."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-f')
	form = post.form

	if CoreConfig.disabled_func["send2trash"]:
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()


	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.translate_path(xpath(url_path, filename))

	self.log_warning(f'<-send2trash-> {os_f_path} by {[uid]}')

	head = "Failed"
	try:
		if CoreConfig.OS == 'Android':
			raise InterruptedError
		send2trash(os_f_path)
		msg = "Successfully Moved To Recycle bin " + post.refresh
		head = "Success"
	except TrashPermissionError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except InterruptedError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except Exception as e:
		traceback.print_exc()
		msg = "<b>" + rel_path + "</b> " + e.__class__.__name__

	return self.send_json({"head": head, "body": msg}, cookie=cookie)





@SH.on_req('POST', hasQ="del-p")
def del_permanently(self: SH, *args, **kwargs):
	"""DELETE files permanently"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)

	url_path = kwargs.get('url_path', '')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-p')
	form = post.form



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.translate_path(xpath(url_path, filename))

	self.log_warning(f'Perm. DELETED {os_f_path} by {[uid]}')


	try:
		if os.path.isfile(os_f_path): os.remove(os_f_path)
		else: shutil.rmtree(os_f_path, ignore_errors=True)

		return self.send_json({"head": "Success", "body": "PERMANENTLY DELETED  " + rel_path + post.refresh}, cookie=cookie)


	except Exception as e:
		traceback.print_exc()
		return self.send_json({"head": "Failed", "body": "<b>" + rel_path + "<b>" + e.__class__.__name__}, cookie=cookie)





@SH.on_req('POST', hasQ="rename")
def rename_content(self: SH, *args, **kwargs):
	"""Rename files"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"head": "Failed", "body": "Renaming is disabled."}, cookie=cookie)


	url_path = kwargs.get('url_path', '')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'rename')
	form = post.form



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()


	new_name = form.get_multi_field(verify_name='data', decode=T)[1]

	if not new_name or not new_name.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + new_name}, cookie=cookie)

	new_name = new_name.strip()

	rel_path = self.get_rel_path(filename)
	new_rel_path = self.get_rel_path(new_name)

	if not self.path_safety_check(filename, new_name, rel_path, new_rel_path):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.translate_path(xpath(url_path, filename))
	os_new_f_path = self.translate_path(xpath(url_path, new_name))

	self.log_warning(f'Renamed "{os_f_path}" to "{os_new_f_path}" by {[uid]}')


	try:
		os.rename(os_f_path, os_new_f_path)
		return self.send_json({"head": "Renamed Successfully", "body":  post.refresh}, cookie=cookie)
	except Exception as e:
		return self.send_json({"head": "Failed", "body": "<b>" + rel_path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + self.get_web_path(str(e), -1) }, cookie=cookie)





@SH.on_req('POST', hasQ="info")
def get_info(self: SH, *args, **kwargs):
	"""Get files permanently"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION:
		return self.send_json({"head": "Failed", "body": "You have no permission to view."}, cookie=cookie)

	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	script = None


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'info')
	form = post.form


	# File link to move to check info

	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.translate_path(posixpath.join(url_path, filename))


	self.log_warning(f'Info Checked "{os_f_path}" by: {[uid]}')

	if not os.path.exists(os_f_path):
		return self.send_json({"head":"Failed", "body":"File/Folder Not Found"}, cookie=cookie)

	file_stat = get_stat(os_f_path)
	if not file_stat:
		return self.send_json({"head":"Failed", "body":"Permission Denied"}, cookie=cookie)

	data = []
	data.append(["Name", urllib.parse.unquote(filename, errors= 'surrogatepass')])

	if os.path.isfile(os_f_path):
		data.append(["Type","File"])
		if "." in filename:
			data.append(["Extension", filename.rpartition(".")[2]])

		size = file_stat.st_size
		data.append(["Size", humanbytes(size) + " (%i bytes)"%size])

	else: #if os.path.isdir(xpath):
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
	for key, val in data:
		body += "<tr><td>{key}</td><td>{val}</td></tr>".format(key=key, val=val)
	body += "</table>"

	return self.send_json({"head":"Properties", "body":body, "script":script}, cookie=cookie)


@SH.on_req('POST', hasQ="new_folder")
def new_folder(self: SH, *args, **kwargs):
	"""Create new folder"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED)

	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"head": "Failed", "body": "Permission denied."}, cookie=cookie)


	os_path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'new_folder')
	form = post.form

	filename = form.get_multi_field(verify_name='name', decode=T)[1]

	if not filename or not filename.strip():
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + filename}, cookie=cookie)

	filename = filename.strip()

	rel_path = self.get_rel_path(filename)

	if not self.path_safety_check(filename, rel_path):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + rel_path}, cookie=cookie)

	os_f_path = self.translate_path(posixpath.join(url_path, filename))


	self.log_warning(f'New Folder Created "{os_f_path}" by: {[uid]}')

	try:
		if os.path.exists(os_f_path):
			return self.send_json({"head": "Failed", "body": "Folder Already Exists:  " + rel_path}, cookie=cookie)
		if os.path.isfile(os_f_path):
			return self.send_json({"head": "Failed", "body": "File Already Exists:  " + rel_path}, cookie=cookie)
		os.makedirs(os_f_path)
		return self.send_json({"head": "Success", "body": "New Folder Created:  " + rel_path +post.refresh}, cookie=cookie)

	except Exception as e:
		self.log_error(traceback.format_exc())
		return self.send_json({"head": "Failed", "body": f"<b>{ rel_path }</b><br><b>{ e.__class__.__name__ }</b>"}, cookie=cookie)





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
	run(port = 45454)
