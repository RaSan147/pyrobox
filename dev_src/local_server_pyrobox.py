


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

from pyroboxCore import config as CoreConfig, logger, DealPostData as DPD, run as run_server, tools, reload_server, __version__

from _fs_utils import get_titles, dir_navigator, get_dir_size, get_stat, get_tree_count_n_size, fmbytes, humanbytes
from _arg_parser import main as arg_parser
import _page_templates as pt
from _exceptions import LimitExceed
from _zipfly_manager import ZIP_Manager
from _list_maker import list_directory, list_directory_json, list_directory_html


from pyrobox_ServerHost import ServerConfig, ServerHost as SH



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
		with urllib.request.urlopen(url) as response:
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
	username = get("uname")
	token = get("token")

	user = Sconfig.user_handler.get_user(username)
	if user:
		if user.token == token:
			return user
		else:
			return None
	return None


def Authorize_user(self:SH):
	# do cookie stuffs and get user

	if Sconfig.GUESTS:
		return Sconfig.guest_id # default guest user
		



@SH.on_req('HEAD', hasQ="type")
def get_page_type(self: SH, *args, **kwargs):
	"""Return type of the page"""

	
	path = kwargs.get('path', '')
	
	if self.query("admin"):
		return self.return_txt("admin")
	
	if self.query("login"):
		return self.return_txt("login")
	
	if self.query("signup"):
		return self.return_txt("signup")
	
	if self.query("vid"):
		return self.return_txt("vid")
	
	if self.query("czip"):
		return self.return_txt("zip")
	
	if path == "/favicon.ico":
		return self.return_txt("favicon")
	

	if os.path.isdir(path):
		for index in "index.html", "index.htm":
			index = os.path.join(path, index)
			if os.path.exists(index):
				return self.return_txt("html")
			
		return self.return_txt("dir")
	
	if os.path.isfile(path):
		return self.return_txt("file")
	
	return self.return_txt("unknown")




@SH.on_req('HEAD', '/favicon.ico')
def send_favicon(self: SH, *args, **kwargs):
	self.redirect('https://cdn.jsdelivr.net/gh/RaSan147/pyrobox@main/assets/favicon.ico')

@SH.on_req('HEAD', hasQ="reload")
def reload(self: SH, *args, **kwargs):
	# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
	user = Authorize_user(self) 
	
	if not user:
		return self.send_text(pt.login_page(), 403)
	
	if not user.is_admin():
		return self.send_text("You are not authorized to perform this action", 403)
		

	CoreConfig.reload = True
	self.send_text("Reload initiated")

	reload_server()

@SH.on_req('HEAD', hasQ="shutdown")
def shutdown(self: SH, *args, **kwargs):
	# SHUTS DOWN THE SERVER. VULNERABLE
	user = Authorize_user(self) 
	
	if not user:
		return self.send_text(pt.login_page(), 403)
	
	if not user.is_admin():
		return self.send_text("You are not authorized to perform this action", 403)
	
	self.send_text("Shut down initiated")
	self.server.shutdown()

@SH.on_req('HEAD', hasQ="admin")
def admin_page(self: SH, *args, **kwargs):
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
	
	if not user.is_admin():
		return self.send_text("You are not authorized to perform this action", 403)
		
		
	title = "ADMIN PAGE"
	url_path = kwargs.get('url_path', '')
	displaypath = self.get_displaypath(url_path)

	head = pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
												PY_PUBLIC_URL=CoreConfig.address(),
												PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

	tail = pt.admin_page().template
	return self.return_txt(f"{head}{tail}")

@SH.on_req('HEAD', hasQ="update")
def update(self: SH, *args, **kwargs):
	"""Check for update and return the latest version"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
		
	data = fetch_url("https://raw.githack.com/RaSan147/pyrobox/main/VERSION")
	if data:
		data  = data.decode("utf-8").strip()
		ret = json.dumps({"update_available": data > __version__, "latest_version": data})
		return self.return_txt(ret, HTTPStatus.OK)
	else:
		return self.return_txt("Failed to fetch latest version", HTTPStatus.INTERNAL_SERVER_ERROR)


@SH.on_req('HEAD', hasQ="size")
def get_size(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
		
	url_path = kwargs.get('url_path', '')

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.return_txt(json.dumps({"status": 0}))
	if os.path.isfile(xpath):
		size = stat.st_size
	else:
		size = get_dir_size(xpath)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.return_txt(json.dumps({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte}))

@SH.on_req('HEAD', hasQ="size_n_count")
def get_size_n_count(self: SH, *args, **kwargs):
	"""Return size of the file"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
		
	url_path = kwargs.get('url_path', '')

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.return_txt(json.dumps({"status": 0}))
	if os.path.isfile(xpath):
		count, size = 1, stat.st_size
	else:
		count, size = get_tree_count_n_size(xpath)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.return_txt(json.dumps({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte,
														"count": count}))


@SH.on_req('HEAD', hasQ="czip")
def create_zip(self: SH, *args, **kwargs):
	"""Create ZIP task and return ID"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
		
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')

	if CoreConfig.disabled_func["zip"] or user.check_permission("zip") == False:
		return self.return_txt("ERROR: ZIP FEATURE IS UNAVAILABLE !", HTTPStatus.INTERNAL_SERVER_ERROR)

	# dir_size = get_dir_size(path, limit=6*1024*1024*1024)

	# if dir_size == -1:
	# 	msg = "Directory size is too large, please contact the host"
	# 	return self.return_txt(HTTPStatus.OK, msg)

	displaypath = self.get_displaypath(url_path)
	filename = spathsplit[-2] + ".zip"

	title = "Creating ZIP"

	head = pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
											PY_PUBLIC_URL=CoreConfig.address(),
											PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

	try:
		zid = zip_manager.get_id(path)

		tail = pt.zip_script().safe_substitute(PY_ZIP_ID = zid,
												PY_ZIP_NAME = filename)
		return self.return_txt(f"{head} {tail}")

	except LimitExceed:
		tail = "<h3>Directory size is too large, please contact the host</h3>"
		return self.return_txt(f"{head} {tail}", HTTPStatus.SERVICE_UNAVAILABLE)
	except Exception:
		self.log_error(traceback.format_exc())
		return self.return_txt("ERROR")

@SH.on_req('HEAD', hasQ="zip")
def get_zip(self: SH, *args, **kwargs):
	"""Return ZIP file if available
	Else return progress of the task"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
		
	path = kwargs.get('path', '')
	spathsplit = kwargs.get('spathsplit', '')

	query = self.query
	msg = False

	def reply(status, msg=""):
		return self.send_json({
			"status": status,
			"message": msg
		})

	if not os.path.isdir(path):
		msg = "Folder not found. Failed to create zip"
		self.log_error(msg)
		return reply("ERROR", msg)


	filename = spathsplit[-2] + ".zip"

	id = query["zid"][0]

	# IF NOT STARTED
	if zip_manager.calculating(id):
		return reply("CALCULATING")

	if not zip_manager.zip_id_status(id):
		t = zip_manager.archive_thread(path, id)
		t.start()

		return reply("SUCCESS", "ARCHIVING")


	if zip_manager.zip_id_status[id] == "DONE":
		if query("download"):
			path = zip_manager.zip_ids[id]

			return self.return_file(path, filename, True)


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
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		

	return list_directory_json(self)

@SH.on_req('HEAD', hasQ="vid")
def send_video_page(self: SH, *args, **kwargs):
	# SEND VIDEO PLAYER
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		

	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	vid_source = url_path
	if not self.guess_type(path).startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE")
		return None

	r = []

	displaypath = self.get_displaypath(url_path)



	title = get_titles(displaypath, file=True)

	r.append(pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
													PY_PUBLIC_URL=CoreConfig.address(),
													PY_DIR_TREE_NO_JS= dir_navigator(displaypath)))

	content_type = self.guess_type(path)
	warning = ""

	if content_type not in ['video/mp4', 'video/ogg', 'video/webm']:
		warning = ('<h2>It seems HTML player may not be able to play this Video format, Try Downloading</h2>')


	r.append(pt.video_script().safe_substitute(PY_VID_SOURCE=vid_source,
												PY_FILE_NAME = displaypath.split("/")[-1],
												PY_CONTENT_TYPE=content_type,
												PY_UNSUPPORTED_WARNING=warning))



	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(encoded)



# @SH.on_req('HEAD', url_regex="/@assets/.*")
# def send_assets(self: SH, *args, **kwargs):
# 	"""Send assets"""
# 	user = Authorize_user(self) 
	
# 	if not user: # guest or not will be handled in Authentication
# 		return self.send_text(pt.login_page(), 403)

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

@SH.on_req('HEAD', hasQ="file_list_script")
def send_file_list_script(self: SH, *args, **kwargs):
	"""Send file list script"""
	return self.send_script(pt.file_list_script())

@SH.on_req('HEAD', hasQ="login")
def login_page(self: SH, *args, **kwargs):
	"""Send login page"""
	return self.send_text(pt.login_page())

@SH.on_req('HEAD', hasQ="signup")
def signup_page(self: SH, *args, **kwargs):
	"""Send signup page"""
	return self.send_text(pt.signup_page())

@SH.on_req('HEAD', hasQ="get_users")
def get_users(self: SH, *args, **kwargs):
	"""Send list of users"""
	user = Authorize_user(self) 
	
	if not user:
		return self.send_text(pt.login_page(), 403)
	
	return self.send_json(Sconfig.get_users())




@SH.on_req('HEAD')
def default_get(self: SH, filename=None, *args, **kwargs):
	"""Serve a GET request."""
	user = Authorize_user(self)

	print("/"*50)
	print(user.permission)
	print("/"*50)
	
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
			return list_directory_html(self, path, user)

	# check for trailing "/" which should return 404. See Issue17324
	# The test for this was added in test_httpserver.py
	# However, some OS platforms accept a trailingSlash as a filename
	# See discussion on python-dev and Issue34711 regarding
	# parsing and rejection of filenames with a trailing slash

	if path.endswith("/"):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return None



	# else:

	if (not user.DOWNLOAD) or user.NOPERMISSION:
		if not os.path.exists(path):
			return self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "Download is disabled")
	return self.return_file(path, filename)












# TODO check against user_mgmt
def AUTHORIZE_POST(req: SH, post:DPD, post_type=''):
	"""Check if the user is authorized to post"""

	# START
	post.start()
	form = post.form

	verify_1 = form.get_multi_field(verify_name='post-type', verify_msg=post_type, decode=T)


	# GET UID
	uid_verify = form.get_multi_field(verify_name='post-uid', decode=T)

	uid = uid_verify[1]

	if not uid:
		raise PostError("Invalid request: No uid provided")




	##################################

	# HANDLE USER PERMISSION BY CHECKING UID

	##################################

	return uid




# TODO check against user_mgmt
@SH.on_req('POST', hasQ="upload")
def upload(self: SH, *args, **kwargs):
	"""GET Uploaded files"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
	if user.NOPERMISSION or (not user.UPLOAD):
		return self.send_txt("Upload not allowed", HTTPStatus.SERVICE_UNAVAILABLE)


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
	if password != CoreConfig.PASSWORD: # readline returns password with \r\n at end
		self.log_info(f"Incorrect password by {uid}")

		return self.send_txt("Incorrect password", HTTPStatus.UNAUTHORIZED)

	while post.remainbytes > 0:
		fn = form.get_file_name() # reads the next line and returns the file name
		if not fn:
			return self.send_error(HTTPStatus.BAD_REQUEST, "Can't find out file name...")


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
			return self.send_txt("Can't create file to write, do you have permission to write?", HTTPStatus.SERVICE_UNAVAILABLE)

		finally:
			try:
				os.remove(temp_fn)
				CoreConfig.temp_file.remove(temp_fn)

			except OSError:
				pass



	return self.return_txt("File(s) uploaded")





@SH.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SH, *args, **kwargs):
	"""Move 2 recycle bin"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "You have no permission to delete."})

	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-f')
	form = post.form

	if CoreConfig.disabled_func["send2trash"]:
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."})



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

	return self.send_json({"head": head, "body": msg})





@SH.on_req('POST', hasQ="del-p")
def del_permanently(self: SH, *args, **kwargs):
	"""DELETE files permanently"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
		
	if user.NOPERMISSION or (not user.DELETE):
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."})

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

		return self.send_json({"head": "Success", "body": "PERMANENTLY DELETED  " + path + post.refresh})


	except Exception as e:
		traceback.print_exc()
		return self.send_json({"head": "Failed", "body": "<b>" + path + "<b>" + e.__class__.__name__})





@SH.on_req('POST', hasQ="rename")
def rename_content(self: SH, *args, **kwargs):
	"""Rename files"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		

	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"head": "Failed", "body": "Renaming is disabled."})


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
		return self.send_json({"head": "Renamed Successfully", "body":  post.refresh})
	except Exception as e:
		return self.send_json({"head": "Failed", "body": "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) })





@SH.on_req('POST', hasQ="info")
def get_info(self: SH, *args, **kwargs):
	"""Get files permanently"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
	
	if user.NOPERMISSION:
		return self.send_json({"head": "Failed", "body": "You have no permission to view."})

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
		return self.send_json({"head":"Failed", "body":"File/Folder Not Found"})

	file_stat = get_stat(xpath)
	if not file_stat:
		return self.send_json({"head":"Failed", "body":"Permission Denied"})

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
		console.log(resp);
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

	return self.send_json({"head":"Properties", "body":body, "script":script})



@SH.on_req('POST', hasQ="new_folder")
def new_folder(self: SH, *args, **kwargs):
	"""Create new folder"""
	user = Authorize_user(self) 
	
	if not user: # guest or not will be handled in Authentication
		return self.send_text(pt.login_page(), 403)
		
	if user.NOPERMISSION or (not user.MODIFY):
		return self.send_json({"head": "Failed", "body": "Permission denied."})
		
		
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
		return self.send_json({"head": "Failed", "body": "Invalid Path:  " + path})

	xpath = self.translate_path(posixpath.join(url_path, filename))


	self.log_warning(f'New Folder Created "{xpath}" by: {[uid]}')

	try:
		if os.path.exists(xpath):
			return self.send_json({"head": "Failed", "body": "Folder Already Exists:  " + path})
		if os.path.isfile(xpath):
			return self.send_json({"head": "Failed", "body": "File Already Exists:  " + path})
		os.makedirs(xpath)
		return self.send_json({"head": "Success", "body": "New Folder Created:  " + path +post.refresh})

	except Exception as e:
		self.log_error(traceback.format_exc())
		return self.send_json({"head": "Failed", "body": f"<b>{ path }</b><br><b>{ e.__class__.__name__ }</b>"})





@SH.on_req('POST')
def default_post(self: SH, *args, **kwargs):
	raise PostError("Bad Request")




































# proxy for old versions
def run(*args, **kwargs):
	run_server(handler=SH, *args, **kwargs)

if __name__ == '__main__':
	run(port = 45454)
