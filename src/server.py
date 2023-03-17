#!/usr/bin/env python3
# -*- coding: utf-8 -*-


enc = "utf-8"

import html
import io
import os
import sys
import posixpath
import shutil

import time
import datetime

from queue import Queue
import importlib.util
import re

import urllib.parse
import urllib.request

from string import Template as _Template # using this because js also use {$var} and {var} syntax and py .format is often unsafe
import threading

import subprocess
import tempfile
import random
import string
import json
from http import HTTPStatus

import traceback
import atexit

from .pyroboxCore import config, logger, SimpleHTTPRequestHandler as SH, DealPostData as DPD, run as run_server, tools, Callable_dict, reload_server, __version__

__version__ = __version__
true = T = True
false = F = False


config.parser.add_argument('--password', '-k',
							default=config.PASSWORD,
							type=str,
							help='Upload Password (default: %(default)s)')


args = config.parser.parse_known_args()[0]
config.PASSWORD = args.password

config.MAIN_FILE = os.path.abspath(__file__)

config.disabled_func.update({
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

class LimitExceed(Exception):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

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

# TODO
# ----------------------------------------------------------------
# * ADD MORE FILE TYPES
# * ADD SEARCH


# INSTALL REQUIRED PACKAGES
REQUEIREMENTS= ['send2trash', 'natsort']




def check_installed(pkg):
	return bool(importlib.util.find_spec(pkg))



def run_update():
	dep_modified = False

	import sysconfig, pip

	i = "pyrobox"
	more_arg = ""
	if pip.__version__ >= "6.0":
		more_arg += " --disable-pip-version-check"
	if pip.__version__ >= "20.0":
		more_arg += " --no-python-version-warning"


	py_h_loc = os.path.dirname(sysconfig.get_config_h_filename())
	on_linux = f'export CPPFLAGS="-I{py_h_loc}";'
	command = "" if config.OS == "Windows" else on_linux
	comm = f'{command} {sys.executable} -m pip install -U --user {more_arg} {i}'

	try:
		subprocess.call(comm, shell=True)
	except Exception as e:
		logger.error(traceback.format_exc())
		return False


	#if i not in get_installed():
	if not check_installed(i):
		return False

	ver = subprocess.check_output(['pyrobox', "-v"]).decode()

	if ver > __version__:
		return True


	else:
		print("Failed to load ", i)
		return False


#############################################
#                FILE HANDLER               #
#############################################

# TODO: delete this on next update
def check_access(path):
	"""
	Check if the user has access to the file.

	path: path to the file
	"""
	if os.path.exists(path):
		try:
			with open(path):
				return True
		except Exception:
			pass
	return False

def get_stat(path):
	"""
	Get the stat of a file.

	path: path to the file

	* can act as check_access(path)
	"""
	try:
		return os.stat(path)
	except Exception:
		return False

# TODO: can be used in search feature
def get_tree(path, include_dir=True):
	"""
	returns a list of files in a directory and its subdirectories.
	[full path, relative path]
	"""
	home = path

	Q = Queue()
	Q.put(path)
	tree = []
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)

			if include_dir or not is_dir:
				tree.append([entry.path, entry.path.replace(home, "", 1)])

		dir.close()
	return tree



def _get_tree_count(path):
	count = 0

	Q = Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				count += 1

		dir.close()
	return count


def get_file_count(path):
	"""
	Get the number of files in a directory.
	"""
	return _get_tree_count(path)

	return sum(1 for _, _, files in os.walk(path) for f in files)

def _get_tree_size(path, limit=None, return_list= False, full_dir=True, both=False, must_read=False):
	r=[] #if return_list
	total = 0
	start_path = path

	Q= Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				try:
					total += entry.stat(follow_symlinks=False).st_size
					if limit and total>limit:
						raise LimitExceed
				except OSError:
					continue

				if must_read:
					try:
						with open(entry.path, "rb") as f:
							f.read(1)
					except Exception:
						continue

				if return_list:
					_path = entry.path
					if both: r.append((_path, _path.replace(start_path, "", 1)))
					else:    r.append(_path if full_dir else _path.replace(start_path, "", 1))

		dir.close()

	if return_list: return total, r
	return total

def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True, both=False, must_read=False):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns `-1`
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	both (bool): if True returns a tuple of (total folder size, (full path, relative path))
	must_read (bool): if True only counts files that can be read
	"""

	return _get_tree_size(start_path, limit, return_list, full_dir, both, must_read)


	r=[] #if return_list
	total_size = 0
	start_path = os.path.normpath(start_path)

	for dirpath, dirnames, filenames in os.walk(start_path, onerror= None):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if os.path.islink(fp):
				continue

			stat = get_stat(fp)
			if not stat: continue
			if must_read and not check_access(fp): continue

			total_size += stat.st_size
			if limit!=None and total_size>limit:
				if return_list: return -1, False
				return -1

			if return_list:
				if both: r.append((fp, fp.replace(start_path, "", 1)))
				else:    r.append(fp if full_dir else fp.replace(start_path, "", 1))

	if return_list: return total_size, r
	return total_size

def _get_tree_count_n_size(path):
	total = 0
	count = 0
	Q= Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				try:
					total += entry.stat(follow_symlinks=False).st_size
					count += 1
				except OSError as error:
					continue

		dir.close()
	return count, total

def get_tree_count_n_size(start_path):
	"""
	Get the size of a directory and all its subdirectories.
	returns a tuple of (total folder size, total file count)
	"""

	return _get_tree_count_n_size(start_path)

	size = 0
	count = 0
	for dirpath, dirnames, filenames in os.walk(start_path, onerror= None):
		for f in filenames:
			count +=1
			fp = os.path.join(dirpath, f)
			if os.path.islink(fp):
				continue

			stat = get_stat(fp)
			if not stat: continue

			size += stat.st_size

	return count, size

def fmbytes(B=0, path=''):
	'Return the given bytes as a file manager friendly KB, MB, GB, or TB string'
	if path:
		stat = get_stat(path)
		if not stat: return "Unknown"
		B = stat.st_size

	B = B
	KB = 1024
	MB = (KB ** 2) # 1,048,576
	GB = (KB ** 3) # 1,073,741,824
	TB = (KB ** 4) # 1,099,511,627,776


	if B/TB>1:
		return '%.2f TB  '%(B/TB)
	if B/GB>1:
		return '%.2f GB  '%(B/GB)
	if B/MB>1:
		return '%.2f MB  '%(B/MB)
	if B/KB>1:
		return '%.2f KB  '%(B/KB)
	if B>1:
		return '%i bytes'%B

	return "%i byte"%B


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

def get_dir_m_time(path):
	"""
	Get the last modified time of a directory and all its subdirectories.
	"""

	stat = get_stat(path)
	return stat.st_mtime if stat else 0





def get_titles(path, file=False):
	"""Make titles for the header directory
	path: the path of the file or directory
	file: if True, path is a file, else it's a directory

	output: `Viewing NAME`"""

	paths = path.split('/')
	if file:
		return 'Viewing ' + paths[-1]
	if paths[-2]=='':
		return 'Viewing &#127968; HOME'
	else:
		return 'Viewing ' + paths[-2]



def dir_navigator(path):
	"""Makes each part of the header directory accessible like links
	just like file manager, but with less CSS"""

	dirs = re.sub("/{2,}", "/", path).split('/')
	urls = ['/']
	names = ['&#127968; HOME']
	r = []

	for i in range(1, len(dirs)-1):
		dir = dirs[i]
		urls.append(urls[i-1] + urllib.parse.quote(dir, errors='surrogatepass' )+ '/' if not dir.endswith('/') else "")
		names.append(dir)

	for i in range(len(names)):
		tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>"
		r.append(tag)

	return '<span class="dir_arrow">&#10151;</span>'.join(r)



def list_directory_json(self:SH, path=None):
	"""Helper to produce a directory listing (JSON).
	Return json file of available files and folders"""
	if path == None:
		path = self.translate_path(self.path)

	try:
		dir_list = scansort(os.scandir(path))
	except OSError:
		self.send_error(
			HTTPStatus.NOT_FOUND,
			"No permission to list directory")
		return None
	dir_dict = []


	for file in dir_list:
		name = file.name
		displayname = linkname = name


		if file.is_dir():
			displayname = name + "/"
			linkname = name + "/"
		elif file.is_symlink():
			displayname = name + "@"

		dir_dict.append([urllib.parse.quote(linkname, errors='surrogatepass'),
						html.escape(displayname, quote=False)])

	encoded = json.dumps(dir_dict).encode("utf-8", 'surrogateescape')
	f = io.BytesIO()
	f.write(encoded)
	f.seek(0)
	self.send_response(HTTPStatus.OK)
	self.send_header("Content-type", "application/json; charset=%s" % "utf-8")
	self.send_header("Content-Length", str(len(encoded)))
	self.end_headers()
	return f



def list_directory(self:SH, path):
	"""Helper to produce a directory listing (absent index.html).

	Return value is either a file object, or None (indicating an
	error).  In either case, the headers are sent, making the
	interface the same as for send_head().

	"""

	try:
		dir_list = scansort(os.scandir(path))
	except OSError:
		self.send_error(
			HTTPStatus.NOT_FOUND,
			"No permission to list directory")
		return None
	r = []

	displaypath = self.get_displaypath(self.url_path)


	title = get_titles(displaypath)


	r.append(directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
													PY_PUBLIC_URL=config.address(),
													PY_DIR_TREE_NO_JS=dir_navigator(displaypath)))

	r_li= [] # type + file_link
				# f  : File
				# d  : Directory
				# v  : Video
				# h  : HTML
	f_li = [] # file_names
	s_li = [] # size list

	r_folders = [] # no js
	r_files = [] # no js


	LIST_STRING = '<li><a class= "%s" href="%s">%s</a></li><hr>'

	r.append("""
			<div id="content_list">
				<ul id="linkss">
					<!-- CONTENT LIST (NO JS) -->
			""")


	# r.append("""<a href="../" style="background-color: #000;padding: 3px 20px 8px 20px;border-radius: 4px;">&#128281; {Prev folder}</a>""")
	for file in dir_list:
		#fullname = os.path.join(path, name)
		name = file.name
		displayname = linkname = name
		size=0
		# Append / for directories or @ for symbolic links
		_is_dir_ = True
		if file.is_dir():
			displayname = name + "/"
			linkname = name + "/"
		elif file.is_symlink():
			displayname = name + "@"
		else:
			_is_dir_ =False
			size = fmbytes(file.stat().st_size)
			__, ext = posixpath.splitext(name)
			if ext=='.html':
				r_files.append(LIST_STRING % ("link", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

				r_li.append('h'+ urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(html.escape(displayname, quote=False))

			elif self.guess_type(linkname).startswith('video/'):
				r_files.append(LIST_STRING % ("vid", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

				r_li.append('v'+ urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(html.escape(displayname, quote=False))

			elif self.guess_type(linkname).startswith('image/'):
				r_files.append(LIST_STRING % ("file", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

				r_li.append('i'+ urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(html.escape(displayname, quote=False))

			else:
				r_files.append(LIST_STRING % ("file", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

				r_li.append('f'+ urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(html.escape(displayname, quote=False))
		if _is_dir_:
			r_folders.append(LIST_STRING % ("", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

			r_li.append('d' + urllib.parse.quote(linkname, errors='surrogatepass'))
			f_li.append(html.escape(displayname, quote=False))

		s_li.append(size)



	r.extend(r_folders)
	r.extend(r_files)

	r.append("""</ul>
				</div>
				<!-- END CONTENT LIST (NO JS) -->
				<div id="js-content_list" class="jsonly"></div>
			""")

	r.append(_js_script().safe_substitute(PY_LINK_LIST=str(r_li),
										PY_FILE_LIST=str(f_li),
										PY_FILE_SIZE =str(s_li)))


	encoded = '\n'.join(r).encode(enc, 'surrogateescape')

	return self.send_txt(HTTPStatus.OK, encoded)




#############################################
#               ZIP INITIALIZE              #
#############################################

try:
	# -*- coding: utf-8 -*-
	zf__version__ = '6.0.5'
	# v

	import io
	import zipfile

	ZIP64_LIMIT = (1 << 31) + 1

	class ZipflyStream(io.RawIOBase):
		def __init__(self):
			self._buffer = b''
			self._size = 0

		def writable(self):
			return True

		def write(self, b):
			if self.closed:
				raise RuntimeError("ZipFly stream was closed!")
			self._buffer += b
			return len(b)

		def get(self):
			chunk = self._buffer
			self._buffer = b''
			self._size += len(chunk)
			return chunk

		def size(self):
			return self._size


	class ZipFly:

		def __init__(self,
					mode = 'w',
					paths = [],
					chunksize = 0x8000,
					compression = zipfile.ZIP_STORED,
					allowZip64 = True,
					compresslevel = None,
					storesize = 0,
					encode = 'utf-8',):

			"""
			@param store size : int : size of all files
			in paths without compression
			"""
			if isinstance(chunksize, str):
				chunksize = int(chunksize, 16)



			self.comment = 'Written using Zipfly v' + zf__version__
			self.mode = mode
			self.paths = paths
			self.filesystem = 'fs'
			self.arcname = 'n'
			self.compression = compression
			self.chunksize = chunksize
			self.allowZip64 = allowZip64
			self.compresslevel = compresslevel
			self.storesize = storesize
			self.encode = encode
			self.ezs = int('0x8e', 16) # empty zip size in bytes

		def generator(self):

			# stream
			stream = ZipflyStream()

			with zipfile.ZipFile(
				stream,
				mode = self.mode,
				compression = self.compression,
				allowZip64 = self.allowZip64,) as zf:

				for path in self.paths:
					if not self.arcname in path:

						# arcname will be default path
						path[self.arcname] = path[self.filesystem]

					z_info = zipfile.ZipInfo.from_file(
						path[self.filesystem],
						path[self.arcname],
						strict_timestamps=False
					)

					with open( path[self.filesystem], 'rb' ) as e:
						# Read from filesystem:
						with zf.open( z_info, mode=self.mode ) as d:

							for chunk in iter( lambda: e.read(self.chunksize), b'' ):

								d.write(chunk)
								yield stream.get(), len(chunk)
			_chunk = stream.get()
			yield _chunk,  len(_chunk)
			self._buffer_size = stream.size()

			# Flush and close this stream.
			stream.close()

		def get_size(self):
			return self._buffer_size
except ImportError:
	config.disabled_func["zip"] = True
	logger.warning("Failed to initialize zipfly, ZIP feature is disabled.")

class ZIP_Manager:
	def __init__(self) -> None:
		self.zip_temp_dir = tempfile.gettempdir() + '/zip_temp/'
		self.zip_ids = Callable_dict()
		self.zip_path_ids = Callable_dict()
		self.zip_in_progress = Callable_dict()
		self.zip_id_status = Callable_dict()

		self.assigend_zid = Callable_dict()

		self.cleanup()
		atexit.register(self.cleanup)

		self.init_dir()


	def init_dir(self):
		os.makedirs(self.zip_temp_dir, exist_ok=True)


	def cleanup(self):
		shutil.rmtree(self.zip_temp_dir, ignore_errors=True)

	def get_id(self, path, size=None):
		source_size = size if size else get_dir_size(path, must_read=True)
		source_m_time = get_dir_m_time(path)

		exist = 1

		prev_zid, prev_size, prev_m_time = 0,0,0
		if self.zip_path_ids(path):
			prev_zid, prev_size, prev_m_time = self.zip_path_ids[path]

		elif self.assigend_zid(path):
			prev_zid, prev_size, prev_m_time = self.assigend_zid[path]

		else:
			exist=0


		if exist and prev_m_time == source_m_time and prev_size == source_size:
			return prev_zid


		id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))+'_'+ str(time.time())
		id += '0'*(25-len(id))


		self.assigend_zid[path] = (id, source_size, source_m_time)
		return id




	def archive(self, path, zid, size=None):
		"""
		archive the folder

		`path`: path to archive
		`zid`: id of the folder
		`size`: size of the folder (optional)
		"""
		def err(msg):
			self.zip_in_progress.pop(zid, None)
			self.assigend_zid.pop(path, None)
			self.zip_id_status[zid] = "ERROR: " + msg
			return False
		if config.disabled_func["zip"]:
			return err("ZIP FUNTION DISABLED")




		# run zipfly
		self.zip_in_progress[zid] = 0

		source_size, fm = size if size else get_dir_size(path, return_list=True, both=True, must_read=True)

		if len(fm)==0:
			return err("FOLDER HAS NO FILES")

		source_m_time = get_dir_m_time(path)


		dir_name = os.path.basename(path)



		zfile_name = os.path.join(self.zip_temp_dir, "{dir_name}({zid})".format(dir_name=dir_name, zid=zid) + ".zip")

		self.init_dir()


		paths = []
		for i,j in fm:
			paths.append({"fs": i, "n":j})

		zfly = ZipFly(paths = paths, chunksize=0x80000)



		archived_size = 0

		self.zip_id_status[zid] = "ARCHIVING"

		try:
			with open(zfile_name, "wb") as zf:
				for chunk, c_size in zfly.generator():
					zf.write(chunk)
					archived_size += c_size
					if source_size==0:
						source_size+=1 # prevent division by 0
					self.zip_in_progress[zid] = (archived_size/source_size)*100
		except Exception as e:
			traceback.print_exc()
			return err(e)
		self.zip_in_progress.pop(zid, None)
		self.assigend_zid.pop(path, None)
		self.zip_id_status[zid] = "DONE"



		self.zip_path_ids[path] = zid, source_size, source_m_time
		self.zip_ids[zid] = zfile_name
		# zip_ids are never cleared in runtime due to the fact if someones downloading a zip, the folder content changed, other person asked for zip, new zip created and this id got removed, the 1st user wont be able to resume


		return zid

	def archive_thread(self, path, zid, size=None):
		return threading.Thread(target=self.archive, args=(path, zid, size))

zip_manager = ZIP_Manager()

#---------------------------x--------------------------------


if not os.path.isdir(config.log_location):
	try:
		os.mkdir(path=config.log_location)
	except Exception:
		config.log_location ="./"




if not config.disabled_func["send2trash"]:
	try:
		from send2trash import send2trash, TrashPermissionError
	except Exception:
		config.disabled_func["send2trash"] = True
		logger.warning("send2trash module not found, send2trash function disabled")

if not config.disabled_func["natsort"]:
	try:
		import natsort
	except Exception:
		config.disabled_func["natsort"] = True
		logger.warning("natsort module not found, natsort function disabled")

def humansorted(li):
	if not config.disabled_func["natsort"]:
		return natsort.humansorted(li)

	return sorted(li, key=lambda x: x.lower())

def scansort(li):
	if not config.disabled_func["natsort"]:
		return natsort.humansorted(li, key=lambda x:x.name)

	return sorted(li, key=lambda x: x.name.lower())

def listsort(li):
	return humansorted(li)


class Template(_Template):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __add__(self, other):
		if isinstance(other, _Template):
			return Template(self.template + other.template)
		return Template(self.template + str(other))


def _get_template(path):
	if config.dev_mode:
		with open(path, encoding=enc) as f:
			return Template(f.read())

	return Template(config.file_list[path])

def directory_explorer_header():
	return _get_template("html_page.html")

def _global_script():
	return _get_template("global_script.html")

def _js_script():
	return _global_script() + _get_template("html_script.html")

def _video_script():
	return _global_script() + _get_template("html_vid.html")

def _zip_script():
	return _global_script() + _get_template("html_zip_page.html")

def _admin_page():
	return _global_script() + _get_template("html_admin.html")



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


@SH.on_req('HEAD', '/favicon.ico')
def send_favicon(self: SH, *args, **kwargs):
	self.redirect('https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.ico')

@SH.on_req('HEAD', hasQ="reload")
def reload(self: SH, *args, **kwargs):
	# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
	config.reload = True

	reload_server()

@SH.on_req('HEAD', hasQ="admin")
def admin_page(self: SH, *args, **kwargs):
	title = "ADMIN PAGE"
	url_path = kwargs.get('url_path', '')
	displaypath = self.get_displaypath(url_path)

	head = directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
												PY_PUBLIC_URL=config.address(),
												PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

	tail = _admin_page().template
	return self.return_txt(HTTPStatus.OK,  f"{head}{tail}")

@SH.on_req('HEAD', hasQ="update")
def update(self: SH, *args, **kwargs):
	"""Check for update and return the latest version"""
	data = fetch_url("https://raw.githubusercontent.com/RaSan147/py_httpserver_Ult/main/VERSION")
	if data:
		data  = data.decode("utf-8").strip()
		ret = json.dumps({"update_available": data > __version__, "latest_version": data})
		return self.return_txt(HTTPStatus.OK, ret)
	else:
		return self.return_txt(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to fetch latest version")

@SH.on_req('HEAD', hasQ="update_now")
def update_now(self: SH, *args, **kwargs):
	"""Run update"""
	if config.disabled_func["update"]:
		return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0, "message": "UPDATE FEATURE IS UNAVAILABLE !"}))
	else:
		data = run_update()

		if data:
			return self.return_txt(HTTPStatus.OK, json.dumps({"status": 1, "message": "UPDATE SUCCESSFUL !"}))
		else:
			return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0, "message": "UPDATE FAILED !"}))

@SH.on_req('HEAD', hasQ="size")
def get_size(self: SH, *args, **kwargs):
	"""Return size of the file"""
	url_path = kwargs.get('url_path', '')

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0}))
	if os.path.isfile(xpath):
		size = stat.st_size
	else:
		size = get_dir_size(xpath)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.return_txt(HTTPStatus.OK, json.dumps({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte}))

@SH.on_req('HEAD', hasQ="size_n_count")
def get_size_n_count(self: SH, *args, **kwargs):
	"""Return size of the file"""
	url_path = kwargs.get('url_path', '')

	xpath = self.translate_path(url_path)

	stat = get_stat(xpath)
	if not stat:
		return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0}))
	if os.path.isfile(xpath):
		count, size = 1, stat.st_size
	else:
		count, size = get_tree_count_n_size(xpath)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.return_txt(HTTPStatus.OK, json.dumps({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte,
														"count": count}))


@SH.on_req('HEAD', hasQ="czip")
def create_zip(self: SH, *args, **kwargs):
	"""Create ZIP task and return ID"""
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')

	if config.disabled_func["zip"]:
		return self.return_txt(HTTPStatus.INTERNAL_SERVER_ERROR, "ERROR: ZIP FEATURE IS UNAVAILABLE !")

	dir_size = get_dir_size(path, limit=6*1024*1024*1024)

	if dir_size == -1:
		msg = "Directory size is too large, please contact the host"
		return self.return_txt(HTTPStatus.OK, msg)

	displaypath = self.get_displaypath(url_path)
	filename = spathsplit[-2] + ".zip"


	try:
		zid = zip_manager.get_id(path, dir_size)
		title = "Creating ZIP"

		head = directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
												PY_PUBLIC_URL=config.address(),
												PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

		tail = _zip_script().safe_substitute(PY_ZIP_ID = zid,
		PY_ZIP_NAME = filename)
		return self.return_txt(HTTPStatus.OK,
		f"{head} {tail}")
	except Exception:
		self.log_error(traceback.format_exc())
		return self.return_txt(HTTPStatus.OK, "ERROR")

@SH.on_req('HEAD', hasQ="zip")
def get_zip(self: SH, *args, **kwargs):
	"""Return ZIP file if available
	Else return progress of the task"""
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')
	first, last = self.range

	query = self.query

	msg = False

	if not os.path.isdir(path):
		msg = "Zip function is not available, please Contact the host"
		self.log_error(msg)
		return self.return_txt(HTTPStatus.OK, msg)


	filename = spathsplit[-2] + ".zip"

	id = query["zid"][0]

	# IF NOT STARTED
	if not zip_manager.zip_id_status(id):
		t = zip_manager.archive_thread(path, id)
		t.start()

		return self.return_txt(HTTPStatus.OK, "SUCCESS")


	if zip_manager.zip_id_status[id] == "DONE":
		if query("download"):
			path = zip_manager.zip_ids[id]

			return self.return_file(path, filename, True)


		if query("progress"):
			return self.return_txt(HTTPStatus.OK, "DONE") #if query("progress") or no query

	# IF IN PROGRESS
	if zip_manager.zip_id_status[id] == "ARCHIVING":
		progress = zip_manager.zip_in_progress[id]
		return self.return_txt(HTTPStatus.OK, "%.2f" % progress)

	if zip_manager.zip_id_status[id].startswith("ERROR"):
		return self.return_txt(HTTPStatus.OK, zip_manager.zip_id_status[id])

@SH.on_req('HEAD', hasQ="json")
def send_ls_json(self: SH, *args, **kwargs):
	"""Send directory listing in JSON format"""
	return list_directory_json(self)

@SH.on_req('HEAD', hasQ="vid")
def send_video_page(self: SH, *args, **kwargs):
	# SEND VIDEO PLAYER
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	vid_source = url_path
	if not self.guess_type(path).startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE")
		return None

	r = []

	displaypath = self.get_displaypath(url_path)



	title = get_titles(displaypath, file=True)

	r.append(directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
													PY_PUBLIC_URL=config.address(),
													PY_DIR_TREE_NO_JS= dir_navigator(displaypath)))

	ctype = self.guess_type(path)
	warning = ""

	if ctype not in ['video/mp4', 'video/ogg', 'video/webm']:
		warning = ('<h2>It seems HTML player may not be able to play this Video format, Try Downloading</h2>')


	r.append(_video_script().safe_substitute(PY_VID_SOURCE=vid_source,
												PY_FILE_NAME = displaypath.split("/")[-1],
												PY_CTYPE=ctype,
												PY_UNSUPPORT_WARNING=warning))



	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(HTTPStatus.OK, encoded)



@SH.on_req('HEAD', url_regex="/@assets/.*")
def send_assets(self: SH, *args, **kwargs):
	"""Send assets"""
	if not config.ASSETS:
		self.send_error(HTTPStatus.NOT_FOUND, "Assets not available")
		return None


	path = kwargs.get('path', '')
	spathsplit = kwargs.get('spathsplit', '')

	path = config.ASSETS_dir + "/".join(spathsplit[2:])
	#	print("USING ASSETS", path)

	if not os.path.isfile(path):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return None

	return self.return_file(path)



@SH.on_req('HEAD')
def default_get(self: SH, filename=None, *args, **kwargs):
	"""Serve a GET request."""
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
			return list_directory(self, path)

	# check for trailing "/" which should return 404. See Issue17324
	# The test for this was added in test_httpserver.py
	# However, some OS platforms accept a trailingSlash as a filename
	# See discussion on python-dev and Issue34711 regarding
	# parseing and rejection of filenames with a trailing slash

	if path.endswith("/"):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return None



	# else:

	return self.return_file(path, filename)













def AUTHORIZE_POST(req: SH, post:DPD, post_type=''):
	"""Check if the user is authorized to post"""

	# START
	post.start()

	verify_1 = post.get_part(verify_name='post-type', verify_msg=post_type, decode=T)


	# GET UID
	uid_verify = post.get_part(verify_name='post-uid', decode=T)

	if not uid_verify[0]:
		raise PostError("Invalid request: No uid provided")


	uid = uid_verify[1]


	##################################

	# HANDLE USER PERMISSION BY CHECKING UID

	##################################

	return uid





@SH.on_req('POST', hasQ="upload")
def upload(self: SH, *args, **kwargs):
	"""GET Uploaded files"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'upload')

	if not uid:
		return None


	uploaded_files = [] # Uploaded folder list



	# PASSWORD SYSTEM
	password = post.get_part(verify_name='password', decode=T)[1]

	self.log_debug(f'post password: {[password]} by client')
	if password != config.PASSWORD: # readline returns password with \r\n at end
		self.log_info(f"Incorrect password by {uid}")

		return self.send_txt(HTTPStatus.UNAUTHORIZED, "Incorrect password")

	while post.remainbytes > 0:
		line = post.get()

		fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
		if not fn:
			return self.send_error(HTTPStatus.BAD_REQUEST, "Can't find out file name...")


		path = self.translate_path(self.path)
		rltv_path = posixpath.join(url_path, fn[0])

		if len(fn[0])==0:
			return self.send_txt(HTTPStatus.BAD_REQUEST, "Invalid file name")

		temp_fn = os.path.join(path, ".LStemp-"+fn[0]+'.tmp')
		config.temp_file.add(temp_fn)


		fn = os.path.join(path, fn[0])



		line = post.get(F) # content type
		line = post.get(F) # line gap



		# ORIGINAL FILE STARTS FROM HERE
		try:
			with open(temp_fn, 'wb') as out:
				preline = post.get(F)
				while post.remainbytes > 0:
					line = post.get(F)
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


			os.replace(temp_fn, fn)



		except (IOError, OSError):
			traceback.print_exc()
			return self.send_txt(HTTPStatus.FORBIDDEN, "Can't create file to write, do you have permission to write?")

		finally:
			try:
				os.remove(temp_fn)
				config.temp_file.remove(temp_fn)

			except OSError:
				pass



	return self.return_txt(HTTPStatus.OK, "File(s) uploaded")





@SH.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SH, *args, **kwargs):
	"""Move 2 recycle bin"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-f')

	if config.disabled_func["send2trash"]:
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."})



	# File link to move to recycle bin
	filename = post.get_part(verify_name='name', decode=T)[1].strip()

	path = self.get_rel_path(filename)
	xpath = self.translate_path(posixpath.join(url_path, filename))

	self.log_warning(f'<-send2trash-> {xpath} by {[uid]}')

	head = "Failed"
	try:
		send2trash(xpath)
		msg = "Successfully Moved To Recycle bin"+ post.refresh
		head = "Success"
	except TrashPermissionError:
		msg = "Recycling unavailable! Try deleting permanently..."
	except Exception as e:
		traceback.print_exc()
		msg = "<b>" + path + "</b> " + e.__class__.__name__

	return self.send_json({"head": head, "body": msg})





@SH.on_req('POST', hasQ="del-p")
def del_permanently(self: SH, *args, **kwargs):
	"""DELETE files permanently"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'del-p')



	# File link to move to recycle bin
	filename = post.get_part(verify_name='name', decode=T)[1].strip()
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
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'rename')



	# File link to move to recycle bin
	filename = post.get_part(verify_name='name', decode=T)[1].strip()

	new_name = post.get_part(verify_name='data', decode=T)[1].strip()

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
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')

	script = None


	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'info')





	# File link to move to check info
	filename = post.get_part(verify_name='name', decode=T)[1].strip()

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
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')

	post = DPD(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, 'new_folder')

	filename = post.get_part(verify_name='name', decode=T)[1].strip()

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
// tools.enable_debug() // TODO: Disable this in production
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
<hr>


<div class='pagination' onclick="Show_folder_maker()">Create Folder</div><br>

<br>
<hr><br>

<noscript>

<form ENCTYPE="multipart/form-data" method="post" action="?upload">
	<!-- using "?upload" action so that user can go back to the page -->
	<center>
		<h1><u>Upload file</u></h1>


		<input type="hidden" name="post-type" value="upload">
		<input type="hidden" name="post-uid" value="12345">

		<span class="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="text" label="Password" class="upload-pass-box">
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

		<span class="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="text" label="Password" class="upload-pass-box">
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
<center><div id="upload-task" style="display:none;font-size:20px;font-weight:700">
	<p id="upload-status"></p>
	<progress id="upload-progress" value="0" max="100" style="width:300px"> </progress>
</div></center>
<hr>

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
			else if (request.status === 0) msg = 'Connection failed (Possible cause: Incorrect password)'
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
			var resp = xhttp.responseText;
			log(resp)

			if (resp.startsWith("SUCCESS")) {
				check_prog = true;
			} else if (resp.startsWith("DONE")) {
				message.innerHTML = "Downloading";
				percentage.innerText = "";
				dl_now = true;
				clearTimeout(prog_timer)
				run_dl()
			} else if (resp.startsWith("ERROR")) {
				message.innerHTML = "Error";
				percentage.innerText = resp;
				clearTimeout(prog_timer)
			} else {
				percentage.innerText = resp + "%";
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





# proxy for old versions
run = run_server

if __name__ == '__main__':
	run()
