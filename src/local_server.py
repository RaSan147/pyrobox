#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = "0.5"
enc = "utf-8"
__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler",

]

import os
import atexit



endl = "\n"
T = t = true = True # too lazy to type
F = f = false = False # too lazy to type

class Config:
	def __init__(self):
		# DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ftp_dir = "." # DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ANDROID_ftp_dir = "/storage/emulated/0/"
		self.LINUX_ftp_dir = "~/"
		self.WIN_ftp_dir= 'D:\\'

		self.IP = None # will be assigned by checking

		# DEFAULT PORT TO LAUNCH SERVER
		self.port= 45454  # DEFAULT PORT TO LAUNCH SERVER

		# UPLOAD PASSWORD SO THAT ANYONE RANDOM CAN'T UPLOAD
		self.PASSWORD= "SECret".encode('utf-8')

		# LOGGING
		self.log_location = "./"  # fallback log_location = "./"
		self.allow_web_log = True # if you want to see some important LOG in browser, may contain your important information

		# ZIP FEATURES
		self.default_zip = "zipfile" # or "zipfile" to use python built in zip module

		# CHECK FOR MISSING REQUEIREMENTS
		self.run_req_check = True

		# FILE INFO
		self.MAIN_FILE = os.path.realpath(__file__)
		self.MAIN_FILE_dir = os.path.dirname(self.MAIN_FILE)

		print(tools.text_box("Running File: ",self.MAIN_FILE))

		# OS DETECTION
		self.OS = self.get_os()


		# RUNNING SERVER STATS
		self.ftp_dir = self.get_default_dir()
		self.dev_mode = True
		self.ASSETS = False # if you want to use assets folder, set this to True
		self.ASSETS_dir = os.path.join(self.MAIN_FILE_dir, "/../assets/")
		self.reload = False


		self.disabled_func = {
			"send2trash": False,
			"natsort": False,
			"zip": False,
			"update": False,
			"delete": False,
			"download": False,
			"upload": False,
			"new_folder": False,
			"rename": False,
			"reload": False,
		}

		# TEMP FILE MAPPING
		self.temp_file = set()

		# CLEAN TEMP FILES ON EXIT
		atexit.register(self.clear_temp)


		# ASSET MAPPING
		self.file_list = {}

	def clear_temp(self):
		for i in self.temp_file:
			try:
				os.remove(i)
			except:
				pass



	def get_os(self):
		from platform import system as platform_system

		out = platform_system()
		if out=="Linux":
			if hasattr(sys, 'getandroidapilevel'):
				#self.IP = "192.168.43.1"
				return 'Android'

		return out

	def get_default_dir(self):
		OS = self.OS
		if OS=='Windows':
			return self.WIN_ftp_dir
		elif OS=='Linux':
			return self.LINUX_ftp_dir
		elif OS=='Android':
			return self.ANDROID_ftp_dir

		return './'


	def address(self):
		return "http://%s:%i"%(self.IP, self.port)





import datetime
import email.utils
import html
import http.client
import io
import mimetypes
import posixpath
import shutil
import socket # For gethostbyaddr()
import socketserver
import sys
import time
import urllib.parse
import urllib.request
import contextlib
from functools import partial
from http import HTTPStatus

import importlib.util
import re


from string import Template as _Template # using this because js also use {$var} and {var} syntax and py .format is often unsafe
import threading

import subprocess
import tempfile, random, string, json


import traceback




class Tools:
	def __init__(self):
		self.styles = {
			"equal" : "=",
			"star"    : "*",
			"hash"  : "#",
			"dash"  : "-",
			"udash": "_"
		}

	def text_box(self, *text, style = "equal"):
		"""
		Returns a string of text with a border around it.
		"""
		text = " ".join(map(str, text))
		term_col = shutil.get_terminal_size()[0]

		s = self.styles[style] if style in self.styles else style
		tt = ""
		for i in text.split('\n'):
			tt += i.center(term_col) + '\n'
		return (f"\n\n{s*term_col}\n{tt}{s*term_col}\n\n")

tools = Tools()
config = Config()


class Custom_dict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __call__(self, *key):
		return all([i in self for i in key])


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
REQUEIREMENTS= ['send2trash', 'natsort']




def check_installed(pkg):
	return bool(importlib.util.find_spec(pkg))


def run_pip_install():
	dep_modified = False

	import sysconfig, pip
	for i in REQUEIREMENTS:
		if check_installed(i):
			continue

		more_arg = ""
		if pip.__version__ >= "6.0":
			more_arg += " --disable-pip-version-check"
		if pip.__version__ >= "20.0":
			more_arg += " --no-python-version-warning"


		py_h_loc = os.path.dirname(sysconfig.get_config_h_filename())
		on_linux = f'export CPPFLAGS="-I{py_h_loc}";'
		command = "" if config.OS == "Windows" else on_linux
		comm = f'{command} {sys.executable} -m pip install  --quiet {more_arg} {i}'

		subprocess.call(comm, shell=True)


		#if i not in get_installed():
		if check_installed(i):
			dep_modified = True


		else:
			print("Failed to load ", i)
			config.disabled_func[i] = True

	if dep_modified:
		print("Reloading...")
		config.reload = True

if config.run_req_check:
	run_pip_install()


if config.reload == True:
	subprocess.call([sys.executable, config.MAIN_FILE] + sys.argv[1:])
	sys.exit(0)

def null(*args, **kwargs):
	pass


#############################################
#                FILE HANDLER               #
#############################################


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

def get_file_count(path):
	# n = 0
	# for _,_,files in os.walk(path, onerror= print):
	# 	n += len(files)
	# return n
	return sum(1 for _, _, files in os.walk(path) for f in files)


def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True, both=False, must_read=False):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns `-1`
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	both (bool): if True returns a tuple of (total folder size, (full path, full path))
	must_read (bool): if True only counts files that can be read
	"""
	r=[] #if return_list
	total_size = 0
	start_path = os.path.normpath(start_path)

	for dirpath, dirnames, filenames in os.walk(start_path, onerror= print):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if not os.path.islink(fp):
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



def list_dir(start_path = '.', full_dir=True, both=False):
	b =[]
	p =[]
	for dirpath, dirnames, filenames in os.walk(start_path, onerror= print):
		for f in filenames:
			fp = os.path.join(dirpath, f)

			if both:
				b.append((fp, fp.replace(start_path, "", 1)))

			elif full_dir:
				p.append(fp)
			else:
				p.append(fp.replace(start_path, "", 1))

	if both:
		return b

	return p


#############################################
#               ZIP INITIALIZE              #
#############################################

try:
	from zipfly_local import ZipFly
except ImportError:
	config.disabled_func["zip"] = True

class ZIP_Manager:
	def __init__(self) -> None:
		self.zip_temp_dir = tempfile.gettempdir() + '/zip_temp/'
		self.zip_ids = Custom_dict()
		self.zip_path_ids = Custom_dict()
		self.zip_in_progress = Custom_dict()
		self.zip_id_status = Custom_dict()

		self.assigend_zid = Custom_dict()

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
		source_m_time = get_dir_m_time(path)


		dir_name = os.path.basename(path)



		zfile_name = os.path.join(self.zip_temp_dir, "{dir_name}({zid})".format(dir_name=dir_name, zid=zid) + ".zip")

		self.init_dir()

		# fm = list_dir(path , both=True)

		if len(fm)==0:
			return err("FOLDER HAS NO FILES")


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

if not config.disabled_func["natsort"]:
	try:
		import natsort
	except Exception:
		config.disabled_func["natsort"] = True

def humansorted(li):
	if not config.disabled_func["natsort"]:
		return natsort.humansorted(li)

	return sorted(li, key=lambda x: x.lower())



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



"""HTTP server classes.

Note: BaseHTTPRequestHandler doesn't implement any HTTP request; see
SimpleHTTPRequestHandler for simple implementations of GET, HEAD and POST,
and CGIHTTPRequestHandler for CGI scripts.

It does, however, optionally implement HTTP/1.1 persistent connections,
as of version 0.3.

XXX To do:

- log requests even later (to capture byte count)
- log user-agent header and other interesting goodies
- send error log to separate file
"""




##############################################
#         PAUSE AND RESUME FEATURE           #
##############################################

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

	#first, last = [x and int(x) for x in m.groups()] #

	first, last = map((lambda x: int(x) if x else None), m.groups())

	if last and last < first:
		raise ValueError('Invalid byte range %s' % byte_range)
	return first, last

#---------------------------x--------------------------------



# download file from url using urllib
def fetch_url(url, file = None):
	try:
		with urllib.request.urlopen(url) as response:
			data = response.read() # a `bytes` object
			if not file:
				return data

		with open(file, 'wb') as f:
			f.write(data)
		return True
	except Exception:
		traceback.print_exc()
		return None


def URL_MANAGER(url:str):
	"""
	returns a tuple of (`path`, `query_dict`, `fragment`)\n

	`url` = `'/store?page=10&limit=15&price=ASC#dskjfhs'`\n
	`path` = `'/store'`\n
	`query_dict` = `{'page': ['10'], 'limit': ['15'], 'price': ['ASC']}`\n
	`fragment` = `dskjfhs`\n
	"""

	# url = '/store?page=10&limit=15&price#dskjfhs'
	parse_result = urllib.parse.urlparse(url)


	dict_result = Custom_dict(urllib.parse.parse_qs(parse_result.query, keep_blank_values=True))

	return (parse_result.path, dict_result, parse_result.fragment)



# Default error message template
DEFAULT_ERROR_MESSAGE = """
<!DOCTYPE HTML>
<html lang="en">
<html>
	<head>
		<meta charset="utf-8">
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

	allow_reuse_address = True	# Seems to make sense in testing environment

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
		self.command = ''  # set in case of error on the first line
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


		# gh-87389: The purpose of replacing '//' with '/' is to protect
		# against open redirect attacks possibly triggered if the path starts
		# with '//' because http clients treat //path as an absolute URI
		# without scheme (similar to http://path) rather than a path.
		if self.path.startswith('//'):
			self.path = '/' + self.path.lstrip('/')  # Reduce to a single /

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

			url_path, query, fragment = URL_MANAGER(self.path)
			self.url_path = url_path
			self.query = query
			self.fragment = fragment


			method()
			self.wfile.flush() #actually send the response if not already done.
		except (TimeoutError, socket.timeout) as e:
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

		message = format % args

		sys.stderr.write("%s - - [%s] %s\n" %
						 (self.address_string(),
						  self.log_date_time_string(),
						  message))

		try:
			# create config.log_location if it doesn't exist
			os.makedirs(config.log_location, exist_ok=True)
			with open(config.log_location + 'log.txt','a+') as f:
				f.write("\n\n" + "%s - - [%s] %s\n" %
							(self.address_string(),
							self.log_date_time_string(),
							format%args))
		except Exception:
			traceback.print_exc()

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

	if not mimetypes.inited:
		mimetypes.init() # try to read system mime.types
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
		'': 'application/octet-stream', # Default
		'.py': 'text/plain',
		'.c': 'text/plain',
		'.h': 'text/plain',
		'.css': 'text/css',

		'.gz': 'application/gzip',
		'.Z': 'application/octet-stream',
		'.bz2': 'application/x-bzip2',
		'.xz': 'application/x-xz',
	})
	
	handlers = {
			'HEAD': [],
			'POST': [],
		}

	def __init__(self, *args, directory=None, **kwargs):
		if directory is None:
			directory = os.getcwd()
		self.directory = os.fspath(directory) # same as directory, but str, new in 3.6
		super().__init__(*args, **kwargs)
		self.query = Custom_dict()

	def do_GET(self):
		"""Serve a GET request."""
		try:
			f = self.send_head()
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return

		if f:
			try:
				self.copyfile(f, self.wfile)
			except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
				print(tools.text_box(e.__class__.__name__, e,"\nby ", self.client_address))
			finally:
				f.close()

	def do_(self):
		'''incase of errored request'''
		self.send_error(HTTPStatus.BAD_REQUEST, "Bad request.")

	@staticmethod
	def on_req(type='', url='.*', hasQ=(), QV={}, fragent='', func=null, escape=None):
		'''called when request is received
		type: GET, POST, HEAD, ...
		url: url regex, * for all, must escape special char and start with /
		hasQ: if url has query
		QV: match query value
		fragent: fragent of request

		if query is tuple, it will only check existence of key
		if query is dict, it will check value of key
		'''
		self = __class__
		if type not in self.handlers:
			self.handlers[type] = []

		if isinstance(hasQ, str):
			hasQ = (hasQ,)

		if escape or (escape is None and '*' not in url):
			url = re.escape(url)

		to_check = (url, hasQ, QV, fragent)

		def decorator(func):
			self.handlers[type].append((to_check, func))
			return func
		return decorator
	
	def test_req(self, url, hasQ, QV, fragent):
		'''test if request is matched'''
		# print("^"+url, hasQ, QV, fragent)
		# print(self.url_path, self.query, self.fragment)
		# print(self.url_path != url, self.query(*hasQ), self.query, self.fragment != fragent)

		if not re.search("^"+url, self.url_path): return False
		if hasQ and self.query(*hasQ)==False: return False
		if QV:
			for k, v in QV.items():
				if not self.query(k): return False
				if self.query[k] != v: return False
		
		if fragent and self.fragment != fragent: return False

		return True

	def do_HEAD(self):
		"""Serve a HEAD request."""
		try:
			f = self.send_head()
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return
		if f:
			f.close()

	def do_POST(self):
		"""Serve a POST request."""
		self.range = None # bug patch
		DO_NOT_JSON = False # wont convert r, info to json

		
		path = self.translate_path(self.path)
		# DIRECTORY DONT CONTAIN SLASH / AT END

		url_path, query, fragment = self.url_path, self.query, self.fragment
		spathsplit = self.url_path.split("/")

		# print(f'url: {url_path}\nquery: {query}\nfragment: {fragment}')
		print(self.handlers['POST'])
		try:
			for case, func in self.handlers['POST']:
				print(case)
				if self.test_req(*case):
					return func(self, url_path=url_path, query=query, fragment=fragment, path=path, spathsplit=spathsplit)
			
		except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
			print(tools.text_box(e.__class__.__name__, e,"\nby ", self.client_address))
			return
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return

	# 	try:
	# 		post_type, r, info, script = self.deal_post_data()
	# 	except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
	# 		print(tools.text_box(e.__class__.__name__, e,"\nby ", self.client_address))
	# 		return
	# 	if post_type=='get-json':
	# 		return self.list_directory_json()

	# 	if post_type== "upload":
	# 		DO_NOT_JSON = True


	# 	print((r, post_type, "by: ", self.client_address))

	# 	if r==True:
	# 		head = "Success"
	# 	elif r==False:
	# 		head = "Failed"

	# 	else:
	# 		head = r


	# 	body = str(info)


	# 	f = io.BytesIO()

	# 	if DO_NOT_JSON:
	# 		data = f"{head} {body}"
	# 		content_type = 'text/html'
	# 	else:
	# 		data = json.dumps({"head": head, "body": body, "script": script})
	# 		content_type = 'application/json'


	# 	f.write(data.encode('utf-8'))

	# 	length = f.tell()
	# 	f.seek(0)
	# 	self.send_response(200)
	# 	self.send_header("Content-type", content_type)
	# 	self.send_header("Content-Length", str(length))
	# 	self.end_headers()

	# 	self.copyfile(f, self.wfile)

	# 	f.close()


	# def deal_post_data(self):
	# 	boundary = b''
	# 	uid = None
	# 	num = 0
	# 	blank = 0 # blank is used to check if the post is empty or Connection Aborted

	# 	refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh &#128259;</div>"


	# 	def get_rel_path(filename):
	# 		return urllib.parse.unquote(posixpath.join(self.path, filename), errors='surrogatepass')


	# 	def get(show=True, strip=False):
	# 		"""
	# 		show: print line
	# 		strip: strip \r\n at end
	# 		"""
	# 		nonlocal num, remainbytes, blank

	# 		line = self.rfile.readline()

	# 		if line == b'':
	# 			blank += 1
	# 		else:
	# 			blank = 0
	# 		if blank>=20: # allow 20 loss packets
	# 			self.send_error(408, "Request Timeout")
	# 			time.sleep(1) # wait for the client to close the connection

	# 			raise ConnectionAbortedError
	# 		if show:
	# 			num+=1
	# 		remainbytes -= len(line)

	# 		if strip and line.endswith(b"\r\n"):
	# 			line = line.rpartition(b"\r\n")[0]

	# 		return line

	# 	def pass_bound():
	# 		nonlocal remainbytes
	# 		line = get(F)
	# 		if not boundary in line:
	# 			return (False, "Content NOT begin with boundary")

	# 	def get_type(line=None, ):
	# 		nonlocal remainbytes
	# 		if not line:
	# 			line = get()
	# 		try:
	# 			return re.findall(r'Content-Disposition.*name="(.*?)"', line.decode())[0]
	# 		except: return None

	# 	def skip():
	# 		get(F)

	# 	def handle_files():
	# 		nonlocal remainbytes
	# 		uploaded_files = [] # Uploaded folder list

	# 		# pass boundary
	# 		pass_bound()


	# 		# PASSWORD SYSTEM
	# 		if get_type()!="password":
	# 			return (False, "Invalid request")

	# 		skip()
	# 		password= get(F)
	# 		print('post password: ',  password)
	# 		if password != config.PASSWORD + b'\r\n': # readline returns password with \r\n at end

	# 			self.send_error(HTTPStatus.UNAUTHORIZED, "Incorrect password")
	# 			# raise ConnectionAbortedError
	# 			return (False, "Incorrect password") # won't even read what the random guy has to say and slap 'em

	# 		pass_bound()

	# 		while remainbytes > 0:
	# 			line =get()

	# 			fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
	# 			if not fn:
	# 				return (False, "Can't find out file name...")


	# 			path = self.translate_path(self.path)
	# 			rltv_path = posixpath.join(self.path, fn[0])

	# 			temp_fn = os.path.join(path, ".LStemp-"+fn[0]+'.tmp')
	# 			config.temp_file.add(temp_fn)


	# 			fn = os.path.join(path, fn[0])



	# 			line = get(F) # content type
	# 			line = get(F) # line gap



	# 			# ORIGINAL FILE STARTS FROM HERE
	# 			try:
	# 				with open(temp_fn, 'wb') as out:
	# 					preline = get(F)
	# 					while remainbytes > 0:
	# 						line = get(F)
	# 						if boundary in line:
	# 							preline = preline[0:-1]
	# 							if preline.endswith(b'\r'):
	# 								preline = preline[0:-1]
	# 							out.write(preline)
	# 							uploaded_files.append(rltv_path,)
	# 							break
	# 						else:
	# 							out.write(preline)
	# 							preline = line


	# 				os.replace(temp_fn, fn)



	# 			except (IOError, OSError):
	# 				return (False, "Can't create file to write, do you have permission to write?")

	# 			finally:
	# 				try:
	# 					os.remove(temp_fn)
	# 					config.temp_file.remove(temp_fn)

	# 				except OSError:
	# 					pass



	# 		return (True, "File(s) uploaded")

	# 	def del_data():

	# 		if config.disabled_func["send2trash"]:
	# 			return (False, "Trash not available. Please contact the Host...")

	# 		# pass boundary
	# 		pass_bound()


	# 		# File link to move to recycle bin
	# 		if get_type()!="name":
	# 			return (False, "Invalid request")


	# 		skip()
	# 		filename = get(strip=T).decode()


	# 		path = get_rel_path(filename)

	# 		xpath = self.translate_path(posixpath.join(self.path, filename))

	# 		print('send2trash "%s" by: %s'%(xpath, uid))

	# 		bool = False
	# 		try:
	# 			send2trash(xpath)
	# 			msg = "Successfully Moved To Recycle bin"+refresh
	# 			bool = True
	# 		except TrashPermissionError:
	# 			msg = "Recycling unavailable! Try deleting permanently..."
	# 		except Exception as e:
	# 			traceback.print_exc()
	# 			msg = "<b>" + path + "</b> " + e.__class__.__name__

	# 		return (bool, msg)


		# def del_permanently():

		# 	# pass boundary
		# 	pass_bound()


		# 	# File link to move to recycle bin
		# 	if get_type()!="name":
		# 		return (False, "Invalid request")


		# 	skip()
		# 	filename = get(strip=T).decode()


		# 	path = get_rel_path(filename)

		# 	xpath = self.translate_path(posixpath.join(self.path, filename))

		# 	print('Perm. DELETED "%s" by: %s'%(xpath, uid))


		# 	try:
		# 		if os.path.isfile(xpath): os.remove(xpath)
		# 		else: shutil.rmtree(xpath)

		# 		return (True, "PERMANENTLY DELETED  " + path +refresh)


		# 	except Exception as e:
		# 		return (False, "<b>" + path + "<b>" + e.__class__.__name__ + " : " + str(e))


		def rename():
			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=T).decode()

			pass_bound()

			if get_type()!="data":
				return (False, "Invalid request")


			skip()
			new_name = get(strip=T).decode()


			path = get_rel_path(filename)


			xpath = self.translate_path(posixpath.join(self.path, filename))


			new_path = self.translate_path(posixpath.join(self.path, new_name))

			print('Renamed "%s" by: %s'%(xpath, uid))


			try:
				os.rename(xpath, new_path)
				return (True, "Rename successful!" + refresh)
			except Exception as e:
				return (False, "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) )


		def get_info():
			script = None

			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request", script)


			skip()
			filename = get(strip=T).decode() # the filename
			path = get_rel_path(filename) # the relative path of the file or folder

			xpath = self.translate_path(posixpath.join(self.path, filename)) # the absolute path of the file or folder

			print(f'Info Checked "{xpath}" by: {uid}')

			file_stat = get_stat(xpath)
			if not file_stat:
				return (False, "Permission Denied", script)

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

				data.append(["Total Files", get_file_count(xpath)])

				print("files: ", get_file_count(xpath))

				data.append(["Total Size", '<span id="f_size">Please Wait</span>'])
				script = '''
				tools.fetch_json(tools.full_path("''' + path + '''?size")).then(size_resp => {
				console.log(size_resp);
				if (size_resp.status) {
					document.getElementById("f_size").innerHTML = size_resp.humanbyte + " (" + size_resp.byte + " bytes)";
				} else {
					throw new Error(size_resp.msg);
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

			return ("Properties", body, script)


		def new_folder():


			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=T).decode()



			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))

			print(f'Info Checked "{xpath}" by: {uid}')

			try:
				os.makedirs(xpath)
				return (True, "New Folder Created:  " + path +refresh)

			except Exception as e:
				return (False, f"<b>{ path }</b><br><b>{ e.__class__.__name__ }</b> : { str(e) }")

		while 0:
			line = get()


		content_type = self.headers['content-type']

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

		r, info, script = (True, "Something", None)

		if handle_type == "upload":
			r, info = handle_files()


		elif handle_type == "test":
			while remainbytes > 0:
				line =get()

		elif handle_type == "del-f":
			r, info = del_data()

		elif handle_type == "del-p":
			r, info = del_permanently()

		elif handle_type=="rename":
			r, info = rename()

		elif handle_type=="info":
			r, info, script = get_info()

		elif handle_type == "new folder":
			r, info = new_folder()

		elif handle_type == "get-json":
			r, info = (None, "get-json")


		return handle_type, r, info, script


	def return_txt(self, code, msg):
		print(tools.text_box(f"Returning {code} {msg}"))

		if not isinstance(msg, bytes):
			encoded = msg.encode('utf-8', 'surrogateescape')
		else:
			encoded = msg

		f = io.BytesIO()
		f.write(encoded)
		f.seek(0)

		self.send_response(code)
		self.send_header("Content-type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return f
	
	def send_txt(self, code, msg):
		f = self.return_txt(code, msg)
		self.copyfile(f, self.wfile)
		f.close()

	def send_json(self, obj):
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		self.wfile.write(json.dumps(obj).encode())

	def return_file(self, path, first, last, filename=None):
		f = None
		is_attachment = "attachment;" if self.query("dl") else ""


		try:
			ctype = self.guess_type(path)

			f = open(path, 'rb')
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
				self.send_header('Content-Type', ctype)
				self.send_header('Accept-Ranges', 'bytes')


				if last is None or last >= file_len:
					last = file_len - 1
				response_length = last - first + 1

				self.send_header('Content-Range',
								'bytes %s-%s/%s' % (first, last, file_len))
				self.send_header('Content-Length', str(response_length))



			else:
				self.send_response(HTTPStatus.OK)
				self.send_header("Content-Type", ctype)
				self.send_header("Content-Length", str(file_len))

			self.send_header("Last-Modified",
							self.date_time_string(fs.st_mtime))
			self.send_header("Content-Disposition", is_attachment+'filename="%s"' % (os.path.basename(path) if filename is None else filename))
			self.end_headers()

			return f

		except PermissionError:
			self.send_error(HTTPStatus.FORBIDDEN, "Permission denied")
			return None

		except OSError:
			self.send_error(HTTPStatus.NOT_FOUND, "File not found")
			return None


		except:
			f.close()
			raise



	def send_head(self):
		"""Common code for GET and HEAD commands.

		This sends the response code and MIME headers.

		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.

		"""


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
		# DIRECTORY DONT CONTAIN SLASH / AT END

		url_path, query, fragment = self.url_path, self.query, self.fragment
		spathsplit = self.url_path.split("/")

		print(f'url: {url_path}\nquery: {query}\nfragment: {fragment}')


		for case, func in self.handlers['HEAD']:
			if self.test_req(*case):
				return func(self, url_path=url_path, query=query, fragment=fragment, path=path, first=first, last=last, spathsplit=spathsplit)




	def get_displaypath(self, url_path):
		"""Helper to produce a display path for the directory listing.
		"""

		try:
			displaypath = urllib.parse.unquote(url_path, errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(url_path)
		displaypath = html.escape(displaypath, quote=False)

		return displaypath





	def list_directory_json(self, path=None):
		"""Helper to produce a directory listing (JSON).
		Return json file of available files and folders"""
		if path == None:
			path = self.translate_path(self.path)

		try:
			dir_list = humansorted(os.listdir(path))
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		dir_dict = []


		for name in dir_list:
			fullname = os.path.join(path, name)
			displayname = linkname = name


			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			elif os.path.islink(fullname):
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



	def list_directory(self, path):
		"""Helper to produce a directory listing (absent index.html).

		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().

		"""

		try:
			dir_list = humansorted(os.listdir(path))
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		r = []

		displaypath = self.get_displaypath(self.url_path)


		title = self.get_titles(displaypath)


		r.append(directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
														PY_PUBLIC_URL=config.address(),
														PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath)))

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
		for name in dir_list:
			fullname = os.path.join(path, name)
			displayname = linkname = name
			size=0
			# Append / for directories or @ for symbolic links
			_is_dir_ = True
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			elif os.path.islink(fullname):
				displayname = name + "@"
			else:
				_is_dir_ =False
				size = fmbytes(path=fullname)
				__, ext = posixpath.splitext(fullname)
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
		
	
	def get_rel_path(self, filename):
		return urllib.parse.unquote(posixpath.join(self.url_path, filename), errors='surrogatepass')


	def dir_navigator(self, path):
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
		guess, _ = mimetypes.guess_type(path)
		if guess:
			return guess

		return self.extensions_map[''] #return 'application/octet-stream'



@SimpleHTTPRequestHandler.on_req('HEAD', '/favicon.ico')
def send_favicon(self: SimpleHTTPRequestHandler, *args, **kwargs):
	self.send_response(301)
	self.send_header('Location','https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.ico')
	self.end_headers()
	return None

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="reload")
def reload(self: SimpleHTTPRequestHandler, *args, **kwargs):
	# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
	config.reload = True

	httpd.server_close()
	httpd.shutdown()

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="admin")
def admin_page(self: SimpleHTTPRequestHandler, *args, **kwargs):
	title = "ADMIN PAGE"
	url_path = kwargs.get('url_path', '')
	displaypath = self.get_displaypath(url_path)

	head = directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
												PY_PUBLIC_URL=config.address(),
												PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath))

	tail = _admin_page().template
	return self.return_txt(HTTPStatus.OK,  f"{head}{tail}")

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="update")
def update(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Check for update and return the latest version"""
	data = fetch_url("https://raw.githubusercontent.com/RaSan147/py_httpserver_Ult/main/VERSION")
	if data:
		data  = data.decode("utf-8").strip()
		ret = json.dumps({"update_available": data > __version__, "latest_version": data})
		return self.return_txt(HTTPStatus.OK, ret)
	else:
		return self.return_txt(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to fetch latest version")

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="update_now")
def update_now(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Run update"""
	if config.disabled_func["update"]:
		return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0, "message": "UPDATE FEATURE IS UNAVAILABLE !"}))
	else:
		data = fetch_url("https://raw.githubusercontent.com/RaSan147/py_httpserver_Ult/main/local_server.py", config.MAIN_FILE)
		if data:
			return self.return_txt(HTTPStatus.OK, json.dumps({"status": 1, "message": "UPDATE SUCCESSFUL !"}))
		else:
			return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0, "message": "UPDATE FAILED !"}))

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="size")
def get_size(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Return size of the file"""
	path = kwargs.get('url_path', '')

	stat = get_stat(path)
	if not stat:
		return self.return_txt(HTTPStatus.OK, json.dumps({"status": 0}))
	if os.path.isfile(path):
		size = stat.st_size
	else:
		size = get_dir_size(path)

	humanbyte = humanbytes(size)
	fmbyte = fmbytes(size)
	return self.return_txt(HTTPStatus.OK, json.dumps({"status": 1,
														"byte": size,
														"humanbyte": humanbyte,
														"fmbyte": fmbyte}))


@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="czip")
def create_zip(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Create ZIP task and return ID"""
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')
	
	if config.disabled_func["zip"]:
		self.return_txt(HTTPStatus.INTERNAL_SERVER_ERROR, "ZIP FEATURE IS UNAVAILABLE !")

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
												PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath))

		tail = _zip_script().safe_substitute(PY_ZIP_ID = zid,
		PY_ZIP_NAME = filename)
		return self.return_txt(HTTPStatus.OK,
		f"{head} {tail}")
	except Exception:
		self.log_error(traceback.format_exc())
		return self.return_txt(HTTPStatus.OK, "ERROR")

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="zip")
def get_zip(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Return ZIP file if available
	Else return progress of the task"""
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')
	first = kwargs.get('first', '')
	last = kwargs.get('last', '')

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

			return self.return_file(path, first, last, filename)


		if query("progress"):
			return self.return_txt(HTTPStatus.OK, "DONE") #if query("progress") or no query

	# IF IN PROGRESS
	if zip_manager.zip_id_status[id] == "ARCHIVING":
		progress = zip_manager.zip_in_progress[id]
		return self.return_txt(HTTPStatus.OK, "%.2f" % progress)

	if zip_manager.zip_id_status[id].startswith("ERROR"):
		return self.return_txt(HTTPStatus.OK, zip_manager.zip_id_status[id])

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="json")
def send_ls_json(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Send directory listing in JSON format"""
	return self.list_directory_json()

@SimpleHTTPRequestHandler.on_req('HEAD', hasQ="vid")
def send_video_page(self: SimpleHTTPRequestHandler, *args, **kwargs):
	# SEND VIDEO PLAYER
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')

	vid_source = url_path
	if not self.guess_type(path).startswith('video/'):
		self.send_error(HTTPStatus.NOT_FOUND, "THIS IS NOT A VIDEO FILE")
		return None

	r = []

	displaypath = self.get_displaypath(url_path)



	title = self.get_titles(displaypath)

	r.append(directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
													PY_PUBLIC_URL=config.address(),
													PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath)))


	r.append("</ul></div>")


	if self.guess_type(path) not in ['video/mp4', 'video/ogg', 'video/webm']:
		r.append('<h2>It seems HTML player can\'t play this Video format, Try Downloading</h2>')
	else:
		ctype = self.guess_type(path)
		r.append(_video_script().safe_substitute(PY_VID_SOURCE=vid_source,
												PY_CTYPE=ctype))

	r.append(f'<br><a href="{vid_source}"  download class=\'pagination\'>Download</a></li>')


	r.append('\n<hr>\n</body>\n</html>\n')

	encoded = '\n'.join(r).encode(enc, 'surrogateescape')
	return self.return_txt(HTTPStatus.OK, encoded)



@SimpleHTTPRequestHandler.on_req('HEAD', url="/@assets/.*")
def send_assets(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Send assets"""
	if not config.ASSETS:
		self.send_error(HTTPStatus.NOT_FOUND, "Assets not available")
		return None


	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')
	first = kwargs.get('first', '')
	last = kwargs.get('last', '')

	path = config.ASSETS_dir + "/".join(spathsplit[2:])
	#	print("USING ASSETS", path)

	if not os.path.isfile(path):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return None

	return self.return_file(path, first, last)



@SimpleHTTPRequestHandler.on_req('HEAD')
def default_get(self: SimpleHTTPRequestHandler, filename=None, *args, **kwargs):
	print(kwargs)
	"""Serve a GET request."""
	path = kwargs.get('path', '')
	url_path = kwargs.get('url_path', '')
	spathsplit = kwargs.get('spathsplit', '')
	first = kwargs.get('first', '')
	last = kwargs.get('last', '')

	
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
			return self.list_directory(path)

	# check for trailing "/" which should return 404. See Issue17324
	# The test for this was added in test_httpserver.py
	# However, some OS platforms accept a trailingSlash as a filename
	# See discussion on python-dev and Issue34711 regarding
	# parseing and rejection of filenames with a trailing slash
	if path.endswith("/"):
		self.send_error(HTTPStatus.NOT_FOUND, "File not found")
		return None



	# else:

	return self.return_file(path, first, last, filename)















class DealPostData:
	boundary = b''
	uid = None
	num = 0
	blank = 0 # blank is used to check if the post is empty or Connection Aborted
	remainbytes = 0

	def __init__(self, req:SimpleHTTPRequestHandler) -> None:
		self.req = req
		

	refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh &#128259;</div>"


	def get(self, show=True, strip=False):
		"""
		show: print line
		strip: strip \r\n at end
		"""
		req = self.req
		line = req.rfile.readline()

		if line == b'':
			self.blank += 1
		else:
			self.blank = 0
		if self.blank>=20: # allow 20 loss packets
			req.send_error(408, "Request Timeout")
			time.sleep(1) # wait for the client to close the connection

			raise ConnectionAbortedError
		if show:
			self.num+=1
		self.remainbytes -= len(line)

		if strip and line.endswith(b"\r\n"):
			line = line.rpartition(b"\r\n")[0]

		return line

	def pass_bound(self):
		line = self.get(F)
		if not self.boundary in line:
			return (False, "Content NOT begin with boundary")

	def get_type(self, line=None, ):
		if not line:
			line = self.get()
		try:
			return re.findall(r'Content-Disposition.*name="(.*?)"', line.decode())[0]
		except: return None

	def skip(self,):
		self.get(F)

	def start(self, post_type=b''):
		req = self.req
		content_type = req.headers['content-type']

		if not content_type:
			return (False, "Content-Type header doesn't contain boundary")
		self.boundary = content_type.split("=")[1].encode()

		self.remainbytes = int(req.headers['content-length'])


		self.pass_bound()# LINE 1

		# get post type
		if self.get_type()=="post-type":
			self.skip() # newline
		else:
			return (False, "Invalid post request")

		line = self.get()
		handle_type = line.decode().strip() # post type LINE 3

		if handle_type != post_type.decode():
			return (False, "Invalid post request")

		self.pass_bound() #boundary for password or guid of user

		return (True, handle_type)

	def get_uid(self,):
		if self.get_type()=="post-uid":
			self.skip() # newline
		else:
			return (False, "Unknown User request")

		uid = self.get() # uid LINE 5


		return (True, uid)




def AUTHORIZE_POST(req: SimpleHTTPRequestHandler, post:DealPostData, post_type=b''):
	"""Check if the user is authorized to post"""
	
	# START
	post_verify = post.start(post_type)
	if not post_verify[0]:
		return req.send_txt(HTTPStatus.BAD_REQUEST, post_verify[1])

	# GET UID
	uid_verify = post.get_uid()
	if not uid_verify[0]:
		return req.send_txt(HTTPStatus.BAD_REQUEST, uid_verify[1])
	
	uid = uid_verify[1].decode()

	
	##################################

	# HANDLE USER PERMISSION BY CHECKING UID

	##################################

	return uid








@SimpleHTTPRequestHandler.on_req('POST', hasQ="upload")
def upload(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""GET Uploaded files"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DealPostData(self)

	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, b'upload')


	uploaded_files = [] # Uploaded folder list

	# pass boundary
	post.pass_bound()


	# PASSWORD SYSTEM
	if post.get_type()!="password":
		return self.send_txt(HTTPStatus.BAD_REQUEST, "Invalid request")

	post.skip()
	password= post.get(F)
	print('post password: ',  password)
	if password != config.PASSWORD + b'\r\n': # readline returns password with \r\n at end

		return self.send_txt(HTTPStatus.UNAUTHORIZED, "Incorrect password")


	post.pass_bound()

	while post.remainbytes > 0:
		line = post.get()

		fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
		if not fn:
			return (False, "Can't find out file name...")


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



	return self.send_txt(HTTPStatus.OK, "File(s) uploaded")





@SimpleHTTPRequestHandler.on_req('POST', hasQ="del-f")
def del_2_recycle(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""Move 2 recycle bin"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DealPostData(self)
	
	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, b'del-f')

	
	if config.disabled_func["send2trash"]:
		return self.send_json({"head": "Failed", "body": "Recycling unavailable! Try deleting permanently..."})

	# pass boundary
	post.pass_bound()


	# File link to move to recycle bin
	if post.get_type()!="name":
		return self.send_json({"head": "Failed", "body":  "Invalid request"})


	post.skip()
	filename = post.get(strip=T).decode()


	path = self.get_rel_path(filename)

	xpath = self.translate_path(posixpath.join(url_path, filename))
	print(path, self.path, filename, xpath)

	print('send2trash "%s" by: %s'%(xpath, uid))

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





@SimpleHTTPRequestHandler.on_req('POST', hasQ="del-p")
def del_permanently(self: SimpleHTTPRequestHandler, *args, **kwargs):
	"""DELETE files permanently"""
	path = kwargs.get('path')
	url_path = kwargs.get('url_path')


	post = DealPostData(self)
	
	# AUTHORIZE
	uid = AUTHORIZE_POST(self, post, b'del-p')


	# pass boundary
	post.pass_bound()


	# File link to move to recycle bin
	if post.get_type()!="name":
		return self.send_json({"head": "Failed", "body": "Invalid request"})


	post.skip()
	filename = post.get(strip=T).decode()


	path = self.get_rel_path(filename)

	xpath = self.translate_path(posixpath.join(url_path, filename))

	print('Perm. DELETED "%s" by: %s'%(xpath, uid))


	try:
		if os.path.isfile(xpath): os.remove(xpath)
		else: shutil.rmtree(xpath)

		return self.send_json({"head": "Success", "body": "PERMANENTLY DELETED  " + path + post.refresh})


	except Exception as e:
		traceback.print_exc()
		return self.send_json({"head": "Failed", "body": "<b>" + path + "<b>" + e.__class__.__name__})





















































def _get_best_family(*address):
	infos = socket.getaddrinfo(
		*address,
		type=socket.SOCK_STREAM,
		flags=socket.AI_PASSIVE
	)
	family, type, proto, canonname, sockaddr = next(iter(infos))
	return family, sockaddr

def get_ip():
	IP = '127.0.0.1'
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(0)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		try:
			if config.OS=="Android":
				IP = s.connect(("192.168.43.1",  1))
				IP = s.getsockname()[0]
				# Assigning this variable because Android does't return actual IP when hosting a hotspot
		except (socket.herror, OSError):
			pass
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

	print(tools.text_box(
		f"Serving HTTP on {host} port {port} \n" #TODO: need to check since the output is "Serving HTTP on :: port 6969"
		f"(http://{url_host}:{port}/) ...\n" #TODO: need to check since the output is "(http://[::]:6969/) ..."
		f"Server is probably running on {config.address()}"
		, style="star"
		)
	)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print("\nKeyboard interrupt received, exiting.")

	except OSError:
		print("\nOSError received, exiting.")
	finally:
		if not config.reload:
			sys.exit(0)


class DualStackServer(ThreadingHTTPServer): # UNSUPPORTED IN PYTHON 3.7

	def handle_error(self, request, client_address):
		pass

	def server_bind(self):
		# suppress exception when protocol is IPv4
		with contextlib.suppress(Exception):
			self.socket.setsockopt(
				socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
		return super().server_bind()

	# def finish_request(self, request, client_address):
	# 		self.RequestHandlerClass(request, client_address, self,
	# 								directory=args.directory)




if __name__ == '__main__':
	import argparse



	parser = argparse.ArgumentParser()

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

	handler_class = partial(SimpleHTTPRequestHandler,
								directory=args.directory)

	config.port = args.port

	if not config.reload:
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

if config.reload == True:
	subprocess.call([sys.executable, config.MAIN_FILE] + sys.argv[1:])
	sys.exit(0)
