


# TODO
# ----------------------------------------------------------------
# * ADD MORE FILE TYPES
# * ADD SEARCH

import os
#import sys
import posixpath
import shutil

import datetime


import urllib.parse
import urllib.request

#import subprocess
import json
from http import HTTPStatus
from http.cookies import SimpleCookie


import traceback

from .pyroboxCore import config as CoreConfig, logger, DealPostData as DPD, run as run_server, tools, reload_server, __version__

from ._fs_utils import get_titles, dir_navigator, get_dir_size, get_stat, get_tree_count_n_size, fmbytes, humanbytes
from ._arg_parser import main as arg_parser
from . import _page_templates as pt
from ._exceptions import LimitExceed
from ._zipfly_manager import ZIP_Manager
from ._list_maker import list_directory, list_directory_json, list_directory_html


from .pyrobox_ServerHost import ServerConfig, ServerHost as SH



__version__ = __version__
true = T = True
false = F = False
enc = "utf-8"

###########################################
# ADD COMMAND LINE ARGUMENTS
###########################################
arg_parser(CoreConfig)
cli_args = CoreConfig.parser.parse_known_args()[0]
CoreConfig.PASSWORD = cli_args.password

logger.info(tools.text_box("Server Config", *({i: getattr(cli_args, i)} for i in vars(cli_args) if not (i.startswith("admin") or "password" in i))))


Sconfig = ServerConfig(cli_args=cli_args)





###########################################
# CoreConfig.dev_mode = False
pt.pt_config.dev_mode = CoreConfig.dev_mode

CoreConfig.MAIN_FILE = os.path.abspath(__file__)

CoreConfig.disabled_func.update({
			"send2trash": False,
			"natsort": False,
			"zip": False,
			"update": False,
			"delete": False,
			"download": False,
			"upload": False,
			"new_folder": False,
			"rename": False,
})

########## ZIP MANAGER ################################
# max_zip_size = 6*1024*1024*1024
zip_manager = ZIP_Manager(CoreConfig, size_limit=Sconfig.max_zip_size)

#######################################################



# INSTALL REQUIRED PACKAGES
REQUIREMENTS= ['send2trash', 'natsort']











if not os.path.isdir(CoreConfig.log_location):
	try:
		os.mkdir(path=CoreConfig.log_location)
	except Exception:
		CoreConfig.log_location ="./"




if not CoreConfig.disabled_func["send2trash"]:
	try:
		from send2trash import send2trash, TrashPermissionError
	except Exception:
		CoreConfig.disabled_func["send2trash"] = True
		logger.warning("send2trash module not found, send2trash function disabled")

























# TODO check against user_mgmt
# download file from url using urllib
def fetch_url(url, file = None):
	try:
		with urllib.request.urlopen(url, timeout=5) as response:
			data = response.read() # a `bytes` object
			if not file:
				return data

		with open(file, 'wb') as f:
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



	path = kwargs.get('path', '')

	result= "unknown"

	if self.query("admin"):
		result = "admin"

	elif self.query("login"):
		result = "login"

	elif self.query("signup"):
		result = "signup"

	elif self.query("vid"):
		result = "vid"

	elif self.query("czip"):
		result = "zip"

	elif path == "/favicon.ico":
		result = "favicon"


	elif os.path.isdir(path):
		for index in "index.html", "index.htm":
			index = os.path.join(path, index)
			if os.path.exists(index):
				result = "html"
				break

		else:
			if self.query("json"):
				result = "dir_json"
			else:
				result = "dir"

	elif os.path.isfile(path):
		result = "file"

	return self.return_txt(result, cookie=cookie)




@SH.on_req('HEAD', '/favicon.ico')
def send_favicon(self: SH, *args, **kwargs):
	self.redirect('https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.ico')

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

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.send_json({"status": 0}, cookie=cookie)
	if os.path.isfile(xpath):
		size = stat.st_size
	else:
		size = get_dir_size(xpath)

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

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.send_json({"status": 0}, cookie=cookie)
	if os.path.isfile(xpath):
		count, size = 1, stat.st_size
	else:
		count, size = get_tree_count_n_size(xpath)

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
	
	
	path = kwargs.get('path', '')
	os_path = self.translate_path(path)
	spathsplit = kwargs.get('spathsplit', '')
	filename = spathsplit[-2] + ".zip"

	zid = None
	status = False
	message = ''
	
	try:
		zid = zip_manager.get_id(os_path)
		status = True

	except LimitExceed:
		message = 'Directory size limit exceed'
		
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



	path = kwargs.get('path', '')
	os_path = self.translate_path(path)
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




@SH.on_req('HEAD', hasQ=("vid", "vid-data"))
def send_video_data(self: SH, *args, **kwargs):
	# SEND VIDEO DATA
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)

	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')


	vid_source = url_path

	content_type = self.guess_type(path)

	if not content_type.startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE", cookie=cookie)
		return None


	displaypath = self.get_displaypath(url_path)

	title = get_titles(displaypath, file=True)


	warning = ""

	if content_type not in ['video/mp4', 'video/ogg', 'video/webm']:
		warning = ('<h2>It seems HTML player may not be able to play this Video format, Try Downloading</h2>')

	return self.send_json({
		"status": "success",
		"warning": warning,
		"video": vid_source,
		"title": displaypath.split("/")[-1],
		"content_type": content_type,
	}, cookie=cookie)



@SH.on_req('HEAD', hasQ="vid")
def send_video_page(self: SH, *args, **kwargs):
	# SEND VIDEO PLAYER
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	vid_source = url_path
	content_type = self.guess_type(path)

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






# @SH.on_req('HEAD', url_regex="/@assets/.*")
# def send_assets(self: SH, *args, **kwargs):
# 	"""Send assets"""
# 	user = Authorize_user(self)

# 	if not user: # guest or not will be handled in Authentication
# 		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED)

# 	if not CoreConfig.ASSETS:
# 		self.send_error(HTTPStatus.NOT_FOUND, "Assets not available")
# 		return None


# 	path = kwargs.get('path', '')
# 	spathsplit = kwargs.get('spathsplit', '')

# 	path = CoreConfig.ASSETS_dir + "/".join(spathsplit[2:])
# 	#	print("USING ASSETS", path)

# 	if not os.path.isfile(path):
# 		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
# 		return None

# 	return self.return_file(path)

@SH.on_req('HEAD', hasQ="style")
def send_style(self: SH, *args, **kwargs):
	"""Send style sheet"""
	return self.send_css(pt.style_css())

@SH.on_req('HEAD', hasQ="global_script")
def send_global_script(self: SH, *args, **kwargs):
	"""Send global script"""
	return self.send_script(pt.global_script(), content_type="text/javascript")

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

	path = kwargs.get('path', '')

	if not user.VIEW:
		return self.send_json({
			"status": 0,
			"error_code": HTTPStatus.UNAUTHORIZED,
			"error_message": "You don't have permission to view this folder",

		}, cookie=cookie)


	is_dir = None
	try:
		is_dir = os.path.isdir(path)
	except Exception as e:
		err = traceback.format_exc()
		return self.send_json({
			"status": 0,
			"error_code": HTTPStatus.NOT_FOUND,
			"error_message": str(e),

		})

	if is_dir is None:
		return self.send_json({"status": 0,
								"warning": "Folder not found"}, cookie=cookie)

	data = list_directory(self, path, user, cookie=cookie)

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


	path = kwargs.get('path', '')

	if os.path.isdir(path):
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
			index = os.path.join(path, index)
			if os.path.exists(index):
				path = index
				break
		else:
			return list_directory_html(self, path, user, cookie=cookie)

	# check for trailing "/" which should return 404. See Issue17324
	# The test for this was added in test_httpserver.py
	# However, some OS platforms accept a trailingSlash as a filename
	# See discussion on python-dev and Issue34711 regarding
	# parsing and rejection of filenames with a trailing slash

	if path.endswith("/"):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie=cookie)
		return None



	# else:

	if (not user.DOWNLOAD) or user.NOPERMISSION:
		return self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Download is disabled", cookie=cookie)

	if not os.path.exists(path):
		return self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie=cookie)
	return self.return_file(path, filename, cookie=cookie)












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

	# GET PASSWORD
	password = form.get_multi_field(verify_name='password', decode=T)[1]

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

	# GET PASSWORD
	password = form.get_multi_field(verify_name='password', decode=T)[1]

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


	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)


	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'upload')

	form = post.form

	if not uid:
		return None


	uploaded_files = [] # Uploaded folder list



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


		path = self.translate_path(self.path)
		rltv_path = posixpath.join(url_path, fn)

		temp_fn = os.path.join(path, ".LStemp-"+fn +'.tmp')
		CoreConfig.temp_file.add(temp_fn)


		fn = os.path.join(path, fn)



		line = post.get() # content type
		line = post.get() # line gap



		# ORIGINAL FILE STARTS FROM HERE
		try:
			with open(temp_fn, 'wb') as out:
				preline = post.get()
				while post.remainbytes > 0:
					line = post.get()
					if post.boundary in line:
						preline = preline[0:-1]
						if preline.endswith(b'\r'):
							preline = preline[0:-1]
						out.write(preline)
						uploaded_files.append(rltv_path,)
						break
					else:
						out.write(preline)
						preline = line


			while (not user.MODIFY) and os.path.isfile(fn):
				n = 1
				name, ext = os.path.splitext(fn)
				fn = f"{name}({n}){ext}"
				n += 1
			os.replace(temp_fn, fn)



		except (IOError, OSError):
			traceback.print_exc()

			return self.send_txt("Can't create file to write, do you have permission to write?", HTTPStatus.SERVICE_UNAVAILABLE, cookie=cookie)

		finally:
			try:
				os.remove(temp_fn)
				CoreConfig.temp_file.remove(temp_fn)

			except OSError:
				pass



	return self.return_txt("File(s) uploaded", cookie=cookie)





@SH.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SH, *args, **kwargs):
	"""Move 2 recycle bin"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "You have no permission to delete."}, cookie=cookie)

	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-f')
	form = post.form

	if CoreConfig.disabled_func["send2trash"]:
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1].strip()

	path = self.get_rel_path(filename)
	xpath = self.translate_path(posixpath.join(url_path, filename))

	self.log_warning(f'<-send2trash-> {xpath} by {[uid]}')

	head = "Failed"
	try:
		if CoreConfig.OS == 'Android':
			raise InterruptedError
		send2trash(xpath)
		msg = "Successfully Moved To Recycle bin"+ post.refresh
		head = "Success"
	except TrashPermissionError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except InterruptedError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except Exception as e:
		traceback.print_exc()
		msg = "<b>" + path + "</b> " + e.__class__.__name__

	return self.send_json({"head": head, "body": msg}, cookie=cookie)





@SH.on_req('POST', hasQ="del-p")
def del_permanently(self: SH, *args, **kwargs):
	"""DELETE files permanently"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."}, cookie=cookie)

	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-p')
	form = post.form



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1].strip()
	path = self.get_rel_path(filename)

	xpath = self.translate_path(posixpath.join(url_path, filename))

	self.log_warning(f'Perm. DELETED {xpath} by {[uid]}')


	try:
		if os.path.isfile(xpath): os.remove(xpath)
		else: shutil.rmtree(xpath)

		return self.send_json({"head": "Success", "body": "PERMANENTLY DELETED  " + path + post.refresh}, cookie=cookie)


	except Exception as e:
		traceback.print_exc()
		return self.send_json({"head": "Failed", "body": "<b>" + path + "<b>" + e.__class__.__name__}, cookie=cookie)





@SH.on_req('POST', hasQ="rename")
def rename_content(self: SH, *args, **kwargs):
	"""Rename files"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"head": "Failed", "body": "Renaming is disabled."}, cookie=cookie)


	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'rename')
	form = post.form



	# File link to move to recycle bin
	filename = form.get_multi_field(verify_name='name', decode=T)[1].strip()

	new_name = form.get_multi_field(verify_name='data', decode=T)[1].strip()

	path = self.get_rel_path(filename)


	xpath = self.translate_path(posixpath.join(url_path, filename))


	new_path = self.translate_path(posixpath.join(url_path, new_name))

	self.log_warning(f'Renamed "{xpath}" to "{new_path}" by {[uid]}')


	try:
		os.rename(xpath, new_path)
		return self.send_json({"head": "Renamed Successfully", "body":  post.refresh}, cookie=cookie)
	except Exception as e:
		return self.send_json({"head": "Failed", "body": "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) }, cookie=cookie)





@SH.on_req('POST', hasQ="info")
def get_info(self: SH, *args, **kwargs):
	"""Get files permanently"""
	user, cookie = Authorize_user(self)

	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), HTTPStatus.UNAUTHORIZED, cookie=cookie)


	if user.NOPERMISSION:
		return self.send_json({"head": "Failed", "body": "You have no permission to view."}, cookie=cookie)

	path = kwargs.get('path')
	url_path = kwargs.get('url_path')

	script = None


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'info')
	form = post.form





	# File link to move to check info
	filename = form.get_multi_field(verify_name='name', decode=T)[1].strip()

	path = self.get_rel_path(filename) # the relative path of the file or folder

	xpath = self.translate_path(posixpath.join(url_path, filename)) # the absolute path of the file or folder


	self.log_warning(f'Info Checked "{xpath}" by: {[uid]}')

	if not os.path.exists(xpath):
		return self.send_json({"head":"Failed", "body":"File/Folder Not Found"}, cookie=cookie)

	file_stat = get_stat(xpath)
	if not file_stat:
		return self.send_json({"head":"Failed", "body":"Permission Denied"}, cookie=cookie)

	data = []
	data.append(["Name", urllib.parse.unquote(filename, errors= 'surrogatepass')])

	if os.path.isfile(xpath):
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
		tools.fetch_json(tools.full_path("''' + path + '''?size_n_count")).then(resp => {
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

	data.append(["Path", path])

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


	path = kwargs.get('path')
	url_path = kwargs.get('url_path')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'new_folder')
	form = post.form

	filename = form.get_multi_field(verify_name='name', decode=T)[1].strip()

	path = self.get_rel_path(filename)

	xpath = filename
	if xpath.startswith(('../', '..\\', '/../', '\\..\\')) or '/../' in xpath or '\\..\\' in xpath or xpath.endswith(('/..', '\\..')):
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + path}, cookie=cookie)

	xpath = self.translate_path(posixpath.join(url_path, filename))


	self.log_warning(f'New Folder Created "{xpath}" by: {[uid]}')

	try:
		if os.path.exists(xpath):
			return self.send_json({"head": "Failed", "body": "Folder Already Exists:  " + path}, cookie=cookie)
		if os.path.isfile(xpath):
			return self.send_json({"head": "Failed", "body": "File Already Exists:  " + path}, cookie=cookie)
		os.makedirs(xpath)
		return self.send_json({"head": "Success", "body": "New Folder Created:  " + path +post.refresh}, cookie=cookie)

	except Exception as e:
		self.log_error(traceback.format_exc())
		return self.send_json({"head": "Failed", "body": f"<b>{ path }</b><br><b>{ e.__class__.__name__ }</b>"}, cookie=cookie)





@SH.on_req('POST')
def default_post(self: SH, *args, **kwargs):
	raise PostError("Bad Request")




































# proxy for old versions
def run(*args, **kwargs):
	run_server(handler=SH, *args, **kwargs)

if __name__ == '__main__':
	run(port = 45454)
