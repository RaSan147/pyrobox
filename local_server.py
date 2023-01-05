#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# testing acode
__version__ = "0.6"
enc = "utf-8"
__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler",

]

import os



endl = "\n"

class Config:
	def __init__(self):
		# DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ftp_dir = "." # DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ANDROID_ftp_dir = "/storage/emulated/0/"
		self.LINUX_ftp_dir = "~/"
		self.WIN_ftp_dir= 'D:\\'

		self.IP = None # will be assigned by checking

		# DEFAULT PORT TO LAUNCH SERVER
		self.port= 6969  # DEFAULT PORT TO LAUNCH SERVER

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

		print(self.MAIN_FILE)

		# OS DETECTION
		self.OS = self.get_os()


		# RUNNING SERVER STATS
		self.ftp_dir = self.get_default_dir()

		self.reload = False



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
import contextlib
from functools import partial
from http import HTTPStatus
import pkg_resources as pkg_r, importlib
import re


from string import Template # using this because js also use {$var} and {var} syntax and py .format is often unsafe
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
		for i in text.split("\n"):
			tt += i.center(term_col) + "\n"
		return (f"\n\n{s*term_col}\n{tt}{s*term_col}\n\n")

tools = Tools()
config = Config()

class Custom_dict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __call__(self, key):
		return key in self


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


def get_installed():
	importlib.reload(pkg_r)
	return [pkg.key for pkg in pkg_r.working_set]




disabled_func = {
	"trash": False,
	"zip": False,
}



def run_pip_install():
	import sysconfig
	for i in REQUEIREMENTS:
		if i not in get_installed():

			py_h_loc = os.path.dirname(sysconfig.get_config_h_filename())
			on_linux = f'export CPPFLAGS="-I{py_h_loc}";'
			command = "" if config.OS == "Windows" else on_linux
			comm = f'{command} {sys.executable} -m pip install --disable-pip-version-check --quiet --no-python-version-warning {i}'

			subprocess.run(comm, shell=True)
			if i not in get_installed():
				disabled_func[i] = True

			else:
				REQUEIREMENTS.remove(i)

	if not REQUEIREMENTS:
		print("Reloading...")
		config.reload = True

if config.run_req_check:
	run_pip_install()


#############################################
#                FILE HANDLER               #
#############################################


def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns `-1`
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	"""
	r=[] #if return_list
	total_size = 0
	start_path = os.path.normpath(start_path)

	for dirpath, dirnames, filenames in os.walk(start_path, onerror= print):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if return_list:
				r.append(fp if full_dir else fp.replace(start_path, "", 1))

			if not os.path.islink(fp):
				total_size += os.path.getsize(fp)
			if limit!=None and total_size>limit:
				# print('counted upto', total_size)
				if return_list: return -1, False
				return -1
	if return_list: return total_size, r
	return total_size


def fmbytes(B):
	'Return the given bytes as a file manager friendly KB, MB, GB, or TB string'
	B = B
	KB = 1024
	MB = (KB ** 2) # 1,048,576
	GB = (KB ** 3) # 1,073,741,824
	TB = (KB ** 4) # 1,099,511,627,776


	if B/TB>1:
		return '%.2f TB  '%(B/TB)
		B%=TB
	if B/GB>1:
		return '%.2f GB  '%(B/GB)
		B%=GB
	if B/MB>1:
		return '%.2f MB  '%(B/MB)
		B%=MB
	if B/KB>1:
		return '%.2f KB  '%(B/KB)
		B%=KB
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
	import os
	import time

	return max(os.stat(root).st_mtime for root,_,_ in os.walk(path))


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



			self.comment = f'Written using Zipfly v{zf__version__}'
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
						path[self.arcname]
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

except Exception:
	disabled_func["zip"] = True

class ZIP_Manager:
	def __init__(self) -> None:
		self.zip_temp_dir = tempfile.gettempdir() + '/zip_temp/'
		self.zip_ids = Custom_dict()
		self.zip_path_ids = Custom_dict()
		self.zip_in_progress = Custom_dict()
		self.zip_id_status = Custom_dict()

		self.assigend_zid = Custom_dict()

		shutil.rmtree(self.zip_temp_dir, ignore_errors=True)  # CLEAR ZiP TEMP DIR


		os.makedirs(self.zip_temp_dir, exist_ok=True)

	def cleanup(self):
		shutil.rmtree(self.zip_temp_dir, ignore_errors=True)

	def get_id(self, path, size=None):
		source_size = size if size else get_dir_size(path)
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
		if disabled_func["zip"]:
			return err("ZIP FUNTION DISABLED")




		# run zipfly
		self.zip_in_progress[zid] = 0

		source_size = size if size else get_dir_size(path)
		source_m_time = get_dir_m_time(path)


		dir_name = os.path.basename(path)



		zfile_name = os.path.join(self.zip_temp_dir, dir_name + f"({zid})" + ".zip")

		os.makedirs(self.zip_temp_dir, exist_ok=True)

		fm = list_dir(path , both=True)

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




from send2trash import send2trash, TrashPermissionError
import natsort


def _get_txt(path):
	with open(path, encoding=enc) as f:
		return f.read()

# WILL ADD DATA LATER TO MAKE PYTHON PART CLEANER
directory_explorer_header = Template("")

_js_script = Template("")

_video_script = Template("")

_zip_script = Template("")


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



from urllib.parse import urlparse, parse_qs
def URL_MANAGER(url:str):
	"""
	returns a tuple of (`path`, `query_dict`, `fragment`)\n

	`url` = `'/store?page=10&limit=15&price=ASC#dskjfhs'`\n
	`path` = `'/store'`\n
	`query_dict` = `{'page': ['10'], 'limit': ['15'], 'price': ['ASC']}`\n
	`fragment` = `dskjfhs`\n
	"""

	# url = '/store?page=10&limit=15&price#dskjfhs'
	parse_result = urlparse(url)


	dict_result = Custom_dict(parse_qs(parse_result.query, keep_blank_values=True))

	return (parse_result.path, dict_result, parse_result.fragment)



# Default error message template
DEFAULT_ERROR_MESSAGE = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
		"http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
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
		self.command = None  # set in case of error on the first line
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

		sys.stderr.write("%s - - [%s] %s\n" %
						 (self.address_string(),
						  self.log_date_time_string(),
						  format%args))

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

	def __init__(self, *args, directory=None, **kwargs):
		if directory is None:
			directory = os.getcwd()
		self.directory = directory #os.fspath(directory)
		super().__init__(*args, **kwargs)

	def do_GET(self):
		"""Serve a GET request."""
		f = self.send_head()
		if f:
			try:
				self.copyfile(f, self.wfile)
			except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
				print(tools.text_box(e.__class__.__name__, e,"\nby ", self.client_address))
			finally:
				f.close()

	def do_HEAD(self):
		"""Serve a HEAD request."""
		f = self.send_head()
		if f:
			f.close()

	def do_POST(self):
		"""Serve a POST request."""
		self.range = None # bug patch
		DO_NOT_JSON = False # wont convert r, info to json



		try:
			post_type, r, info = self.deal_post_data()
		except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
			print(tools.text_box(e.__class__.__name__, e,"\nby ", self.client_address))
			return
		if post_type=='get-json':
			return self.list_directory_json()

		if post_type== "upload":
			DO_NOT_JSON = True


		print((r, post_type, "by: ", self.client_address))

		if r==True:
			head = "Success"
		elif r==False:
			head = "Failed"

		else:
			head = r

		body = info


		f = io.BytesIO()

		if DO_NOT_JSON:
			data = (head + body)
			content_type = 'text/html'
		else:
			data = json.dumps([head, body])
			content_type = 'application/json'


		f.write(data.encode('utf-8'))

		length = f.tell()
		f.seek(0)
		self.send_response(200)
		self.send_header("Content-type", content_type)
		self.send_header("Content-Length", str(length))
		self.end_headers()

		self.copyfile(f, self.wfile)

		f.close()

	def deal_post_data(self):
		boundary = None
		uid = None
		num = 0
		post_type = None
		blank = 0 # blank is used to check if the post is empty or Connection Aborted

		refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh &#128259;</div>"


		def get_rel_path(filename):
			return urllib.parse.unquote(posixpath.join(self.path, filename), errors='surrogatepass')


		def get(show=True, strip=False, self=self):
			"""
			show: print line
			strip: strip \r\n at end
			"""
			nonlocal num, remainbytes, blank

			line = self.rfile.readline()

			if line == b'':
				blank += 1
			else:
				blank = 0
			if blank>=10:
				self.send_error(408, "Request Timeout")
				time.sleep(1) # wait for the client to close the connection

				raise ConnectionAbortedError
			if show:
				# print(num, line)
				num+=1
			remainbytes -= len(line)

			if strip and line.endswith(b"\r\n"):
				line = line.rpartition(b"\r\n")[0]

			return line

		def pass_bound(self=self):
			nonlocal remainbytes
			line = get(0)
			if not boundary in line:
				return (False, "Content NOT begin with boundary")

		def get_type(line=None, self=self):
			nonlocal remainbytes
			if not line:
				line = get()
			try:
				return re.findall(r'Content-Disposition.*name="(.*?)"', line.decode())[0]
			except: return None

		def skip(self=self):
			get(0)

		def handle_files(self=self):
			nonlocal remainbytes
			uploaded_files = [] # Uploaded folder list

			# pass boundary
			pass_bound()

			uploading_path = self.path


			# PASSWORD SYSTEM
			if get_type()!="password":
				return (False, "Invalid request")


			skip()
			password= get(0)
			print('post password: ',  password)
			if password != config.PASSWORD + b'\r\n': # readline returns password with \r\n at end
				return (False, "Incorrect password") # won't even read what the random guy has to say and slap 'em

			pass_bound()


			while remainbytes > 0:
				line =get()

				fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
				if not fn:
					return (False, "Can't find out file name...")
				path = self.translate_path(self.path)
				rltv_path = posixpath.join(self.path, fn[0])

				fn = os.path.join(path, fn[0])
				line = get(0) # content type
				line = get(0) # line gap

				# ORIGINAL FILE STARTS FROM HERE
				try:
					with open(fn, 'wb') as out:
						preline = get(0)
						while remainbytes > 0:
							line = get(0)
							if boundary in line:
								preline = preline[0:-1]
								if preline.endswith(b'\r'):
									preline = preline[0:-1]
								out.write(preline)
								uploaded_files.append(rltv_path,)
								break
							else:
								out.write(preline)
								preline = line

				except IOError:
					return (False, "Can't create file to write, do you have permission to write?")



			return (True, ("<!DOCTYPE html><html>\n<title>Upload Result Page</title>\n<body>\n<h2>Upload Result Page</h2>\n<hr>\nFile '%s' upload success!" % ",".join(uploaded_files)) +"<br><br><h2><a href=\"%s\">back</a></h2>" % uploading_path)


		def del_data(self=self):

			if disabled_func["trash"]:
				return (False, "Trash not available. Please contact the Host...")

			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()


			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))

			print('send2trash "%s" by: %s'%(xpath, uid))

			bool = False
			try:
				send2trash(xpath)
				msg = "Successfully Moved To Recycle bin"+refresh
				bool = True
			except TrashPermissionError:
				msg = "Recycling unavailable! Try deleting permanently..."
			except Exception as e:
				traceback.print_exc()
				msg = "<b>" + path + "<b>" + e.__class__.__name__

			return (bool, msg)


		def del_permanently(self=self):

			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()


			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))

			print('Perm. DELETED "%s" by: %s'%(xpath, uid))


			try:
				if os.path.isfile(xpath): os.remove(xpath)
				else: shutil.rmtree(xpath)

				return (True, "PERMANENTLY DELETED  " + path +refresh)


			except Exception as e:
				return (False, "<b>" + path + "<b>" + e.__class__.__name__ + " : " + str(e))


		def rename(self=self):
			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()

			pass_bound()

			if get_type()!="data":
				return (False, "Invalid request")


			skip()
			new_name = get(strip=1).decode()


			path = get_rel_path(filename)


			xpath = self.translate_path(posixpath.join(self.path, filename))


			new_path = self.translate_path(posixpath.join(self.path, new_name))

			print('Renamed "%s" by: %s'%(xpath, uid))


			try:
				os.rename(xpath, new_path)
				return (True, "Rename successful!" + refresh)
			except Exception as e:
				return (False, "<b>" + path + "</b><br><b>" + e.__class__.__name__ + "</b> : " + str(e) )


		def get_info(self=self):


			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()



			path = get_rel_path(filename)

			xpath = self.translate_path(posixpath.join(self.path, filename))

			print('Info Checked "%s" by: %s'%(xpath, uid))

			data = {}
			data["Name"] = urllib.parse.unquote(filename, errors= 'surrogatepass')
			if os.path.isfile(xpath):
				data["Type"] = "File"
				if "." in filename:
					data["Extension"] = filename.rpartition(".")[2]

				size = int(os.path.getsize(xpath))

			else: #if os.path.isdir(xpath):
				data["Type"] = "Folder"
				size = get_dir_size(xpath)

			data["Size"] = humanbytes(size) + " (%i bytes)"%size
			data["Path"] = path

			def get_dt(time):
				return datetime.datetime.fromtimestamp(time)

			data["Created on"] = get_dt(os.path.getctime(xpath))
			data["Last Modified"] = get_dt(os.path.getmtime(xpath))
			data["Last Accessed"] = get_dt(os.path.getatime(xpath))

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
			for i, j in data.items():
				body += f"<tr><td>{ i }</td><td>{ j }</td></tr>"
			body += "</table>"

			return ("Properties", body)


		def new_folder(self=self):


			# pass boundary
			pass_bound()


			# File link to move to recycle bin
			if get_type()!="name":
				return (False, "Invalid request")


			skip()
			filename = get(strip=1).decode()



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

		r, info = (True, "Something")

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
			r, info = get_info()

		elif handle_type == "new folder":
			r, info = new_folder()

		elif handle_type == "get-json":
			r, info = (None, "get-json")


		return handle_type, r, info

	def return_txt(self, code, msg):

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

	def return_file(self, path, first, last, filename=None):
		f = None

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
				self.send_header("Content-Length", str(fs[6]))

			self.send_header("Last-Modified",
							self.date_time_string(fs.st_mtime))
			self.send_header("Content-Disposition", 'attachment; filename="%s"' % (os.path.basename(path) if filename is None else filename))
			self.end_headers()

			return f

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



		url_path, query, fragment = URL_MANAGER(self.path)

		spathsplit = url_path.split("/")

		filename = None

		if self.path == '/favicon.ico':
			self.send_response(301)
			self.send_header('Location','https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.ico')
			self.end_headers()
			return None




		print(f'url: {url_path}\nquery: {query}\nfragment: {fragment}')


		if query("reload"):
			# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
			config.reload = True

			httpd.server_close()
			httpd.shutdown()

		########################################################
		#    TO	TEST ASSETS
		#elif spathsplit[1]=="@assets":
		#	path = "./assets/"+ "/".join(spathsplit[2:])

		########################################################

		elif query("czip"):
			"""Create ZIP task and return ID"""
			if disabled_func["zip"]:
				self.return_txt(HTTPStatus.INTERNAL_SERVER_ERROR, "ZIP FEATURE IS UNAVAILABLE !")

			dir_size = get_dir_size(path, limit=6*1024*1024*1024)

			if dir_size == -1:
				msg = "Directory size is too large, please contact the host"
				return self.return_txt(HTTPStatus.OK, msg)

			try:
				displaypath = urllib.parse.unquote(url_path, errors='surrogatepass')
			except UnicodeDecodeError:
				displaypath = urllib.parse.unquote(url_path)
			displaypath = html.escape(displaypath, quote=False)

			filename = spathsplit[-2] + ".zip"


			try:
				zid = zip_manager.get_id(path, dir_size)
				title = "Creating ZIP"

				head = directory_explorer_header.safe_substitute(PY_PAGE_TITLE=title,
														PY_PUBLIC_URL=config.address(),
														PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath))

				tail = _zip_script.safe_substitute(PY_ZIP_ID = zid,
				PY_ZIP_NAME = filename)
				return self.return_txt(HTTPStatus.OK,
				f"{head} {tail}")
			except Exception:
				self.log_error(traceback.format_exc())
				return self.return_txt(HTTPStatus.OK, "ERROR")

		elif query("zip"):
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





		elif query("json"):
			return self.list_directory_json()


		elif query("vid"):
			vid_source = url_path
			# SEND VIDEO PLAYER
			if self.guess_type(path).startswith('video/'):
				r = []
				try:
					displaypath = urllib.parse.unquote(url_path,
													errors='surrogatepass')
				except UnicodeDecodeError:
					displaypath = urllib.parse.unquote(url_path)
				displaypath = html.escape(displaypath, quote=False)



				title = self.get_titles(displaypath)

				r.append(directory_explorer_header.safe_substitute(PY_PAGE_TITLE=title,
																PY_PUBLIC_URL=config.address(),
																PY_DIR_TREE_NO_JS=self.dir_navigator(displaypath)))


				r.append("</ul></div>")


				if self.guess_type(path) not in ['video/mp4', 'video/ogg', 'video/webm']:
					r.append('<h2>It seems HTML player can\'t play this Video format, Try Downloading</h2>')
				else:
					ctype = self.guess_type(path)
					r.append(_video_script.safe_substitute(PY_VID_SOURCE=vid_source,
															PY_CTYPE=ctype))

				r.append(f'<br><a href="{vid_source}"  download class=\'pagination\'>Download</a></li>')


				r.append('\n<hr>\n</body>\n</html>\n')

				encoded = '\n'.join(r).encode(enc, 'surrogateescape')
				return self.return_txt(HTTPStatus.OK, encoded)

		f = None
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




	def list_directory_json(self, path=None):
		"""Helper to produce a directory listing (JSON).
		Return json file of available files and folders"""
		if path == None:
			path = self.translate_path(self.path)

		try:
			dir_list = natsort.humansorted(os.listdir(path))
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

		url_path, query, fragment = URL_MANAGER(self.path)

		try:
			dir_list = natsort.humansorted(os.listdir(path))
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		r = []
		try:
			displaypath = urllib.parse.unquote(url_path, errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(url_path)
		displaypath = html.escape(displaypath, quote=False)


		title = self.get_titles(displaypath)


		r.append(directory_explorer_header.safe_substitute(PY_PAGE_TITLE=title,
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
				size = fmbytes(os.path.getsize(fullname))
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

		r.append(_js_script.safe_substitute(PY_LINK_LIST=str(r_li),
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

	print(
		f"Serving HTTP on {host} port {port} \n" #TODO: need to check since the output is "Serving HTTP on :: port 6969"
		f"(http://{url_host}:{port}/) ...\n" #TODO: need to check since the output is "(http://[::]:6969/) ..."
		f"Server is probably running on {config.address()}"

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

	def finish_request(self, request, client_address):
			self.RequestHandlerClass(request, client_address, self,
									directory=args.directory)




directory_explorer_header = Template(r"""
<!DOCTYPE HTML>
<!-- test1 -->
<html>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<head>
<link href='https://fonts.googleapis.com/css?family=Open Sans' rel='stylesheet'>
</head>
<title>${PY_PAGE_TITLE}</title>

<script>
function request_reload() {
	fetch('/?reload');
}
const public_url = "${PY_PUBLIC_URL}";
</script>

<style type="text/css">


body {
	position: relative;
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
	padding: 8px;
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
	width: 70%;
}

.link_name {
	width: calc(100% - 57px);
}

.file-remove {
  padding: 12px 16px;
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

#upload-pass {
	background-color: #000;
	padding: 5px;
	border-radius: 4px;
	font: 1.5em sans-serif;
}

#upload-pass-box {
	/* make text field larger */
	font-size: 1.5em;
	border: #aa00ff solid 2px;;
	border-radius: 4px;
	background-color: #0f0f0f;
}


#upload-box {
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
.drag-area button, #submit-btn{
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





</style>

<noscript>
	<style>
		.jsonly {
			display: none !important
		}
	</style>
</noscript>

<link rel="icon" href="https://cdn.jsdelivr.net/gh/RaSan147/py_httpserver_Ult@main/assets/favicon.png?raw=true" type="image/png">

</head>

<body>

<div id="popup-container"></div>

<h1 id="dir-tree">${PY_DIR_TREE_NO_JS}</h1>
<hr>

<script>
const dir_tree = document.getElementById("dir-tree");
dir_tree.scrollLeft = dir_tree.scrollWidth;
</script>

<hr>
<div id="content_list">
	<ul id="linkss">
		<!-- CONTENT LIST (NO JS) -->

""")




#######################################################

#######################################################


_js_script = Template(r"""
</ul>
</div>
<hr>

<div class='pagination jsonly' onclick="request_reload()">RELOAD 🧹</div>
<noscript><a href="/?reload" class='pagination'>RELOAD 🧹</a><br></noscript>
<br>
<div class='pagination' onclick="Show_folder_maker()">Create Folder</div><br>

<br>
<hr><br>


<form ENCTYPE="multipart/form-data" method="post" id="uploader">


	<center>
		<h1><u>Upload file</u></h1>


		<input type="hidden" name="post-type" value="upload">
		<input type="hidden" name="post-uid" value="12345">

		<span id="upload-pass">Upload PassWord:</span>&nbsp;&nbsp;<input name="password" type="text" label="Password" id="upload-pass-box">
		<br><br>
		<!-- <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" multiple /><br><br> -->
		<div id="upload-box">
			<div class="drag-area">
				<div class="drag-icon">⬆️</div>
				<header>Drag & Drop to Upload File</header>
				<span>OR</span>
				<button id="drag-browse">Browse File</button>
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
const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);


String.prototype.toHtmlEntities = function() {
	return this.replace(/./ugm, s => s.match(/[a-z0-9\s]+/i) ? s : "&#" + s.codePointAt(0) + ";");
};

const r_li = ${PY_LINK_LIST};
const f_li = ${PY_FILE_LIST};
const s_li = ${PY_FILE_SIZE};

byId("uploader").addEventListener('submit', e => {
	e.preventDefault()
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
			if (request.status === 204 || request.status === 200) msg = 'Success'
			if (request.status === 0) msg = 'Connection failed'
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
})

function null_func() {
	return true
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
	download(dataurl, filename = null) {
		const link = createElement("a");
		link.href = dataurl;
		link.download = filename;
		link.click();
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
		log(tools.hasClass(this.popup_obj, "active"))
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
			popup_msg.createPopup(data[0], data[1]);
		} else {
			popup_msg.createPopup("Failed", "Server didn't respond<br>response: " + self.status);
		}
		popup_msg.open_popup()
	}
	menu_click(action, link, more_data = null) {
		var that = this
		popup_msg.close()

		var url = ".";
		var xhr = new XMLHttpRequest();
		xhr.open("POST", url);
		xhr.onreadystatechange = function() {
			if (this.readyState === 4) {
				that.on_result(this)
			}
		};
		var formData = new FormData();
		formData.append("post-type", action);
		formData.append("post-uid", 123456);
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
		if (type == "video") {
			var download = createElement("div")
			download.innerText = "⬇️" + " Download"
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
			dl_zip.innerText = "🗃️" + " Download as Zip"
			dl_zip.classList.add("menu_options")
			dl_zip.onclick = function() {
				popup_msg.close()
				window.open(go_link('czip', file), '_blank');
				// czip = "Create Zip"
			}
			menu.appendChild(dl_zip)
		}

		var copy = createElement("div")
		copy.innerText = "⧉" + " Copy link"
		copy.classList.add("menu_options")
		copy.onclick = async function(ev) {
			popup_msg.close()
			let fake_a = createElement("a")
			fake_a.href = file;
			let success = await tools.copy_2(ev, fake_a.href)
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

		function r_u_sure() {
			popup_msg.close()
			var box = createElement("div")
			var msggg = createElement("p")
			msggg.innerHTML = "This can't be undone!!!"
			box.appendChild(msggg)
			var y_btn = createElement("div")
			y_btn.innerText = "Continue"
			y_btn.className = "pagination center"
			y_btn.onclick = function() {
				that.menu_click('del-p', file);
			};
			var n_btn = createElement("div")
			n_btn.innerText = "Cancel"
			n_btn.className = "pagination center"
			n_btn.onclick = popup_msg.close;
			box.appendChild(y_btn)
			box.appendChild(n_btn)
			popup_msg.createPopup("Are you sure?", box)
			popup_msg.open_popup()
		}
		del_P.onclick = r_u_sure
		menu.appendChild(del_P)
		var property = createElement("div")
		property.innerText = "ℹ️" + " Properties"
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
		this.menu_click('new folder', folder_name)
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
var dir_container = byId("content_list")
dir_container.appendChild(folder_li)
dir_container.appendChild(file_li)



</script>


<script>
//selecting all required elements
var uploader = byId("uploader");
const dropArea = document.querySelector(".drag-area"),
dragText = dropArea.querySelector("header"),
button = dropArea.querySelector("button"),
input = dropArea.querySelector("input");
let files; //this is a global variable and we'll use it inside multiple functions
file_display = byId("drag-file-list");

button.onclick = (e)=>{
	e.preventDefault();
	input.click(); //if user click on the button then the input also clicked
}

input.addEventListener("change", function(){
	//getting user select file and [0] this means if user select multiple files then we'll select only the first one
	files = this.files;
	dropArea.classList.add("active");
	showFiles(); //calling function
});


//If user Drag File Over DropArea
dropArea.addEventListener("dragover", (event)=>{
	event.preventDefault(); //preventing from default behaviour
	dropArea.classList.add("active");
	dragText.textContent = "Release to Upload File";
});

//If user leave dragged File from DropArea
dropArea.addEventListener("dragleave", ()=>{
	dropArea.classList.remove("active");
	dragText.textContent = "Drag & Drop to Upload File";
});

//If user drop File on DropArea
dropArea.addEventListener("drop", (event)=>{
	event.preventDefault(); //preventing from default behaviour
	//getting user select file and [0] this means if user select multiple files then we'll select only the first one
	files = event.dataTransfer.files;
	showFiles(); //calling function
});

function removeFileFromFileList(index) {
	const formData = new FormData(uploader)
	const dt = new DataTransfer()
	// const input = byId('files')
	// const { files } = input

	for (let i = 0; i < files.length; i++) {
	const file = files[i]
	if (index !== i)
		dt.items.add(file) // here you exclude the file. thus removing it.
	}

	files = dt.files
	input.files = dt.files // Assign the updates list
	showFiles()
}

function showFiles() {
	tools.del_child(file_display)
	let heading = byId("has-selected-up")
	if(files.length){
		heading.style.display = "block"
	} else {
		heading.style.display = "none"
	}
	for (let i = 0; i <files.length; i++) {
		showFile(files[i], i);
	}
}

function showFile(file, index){
	let filename = file.name;
	let size = file.size;

	let item = createElement("div");
	item.className = "upload-file-item";
	item.innerHTML = `
			<span class="file-name">${filename}</span>
			<span class="file-size">${size} bytes</span>

		<span class="file-remove" onclick="removeFileFromFileList(${index})">&times;</span>
	`;

	file_display.appendChild(item);

}



</script>


<p>v4 I ❤️ emoji!</p>

</body>

</html>

""")




#######################################################

#######################################################


_video_script = Template(r"""
<!-- using from http://plyr.io  -->
<link rel="stylesheet" href="https://raw.githack.com/RaSan147/py_httpserver_Ult/main/assets/video.css" />

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


//var script = document.createElement('script'); script.src = "//cdn.jsdelivr.net/npm/eruda"; document.body.appendChild(script); script.onload = function () { eruda.init() };
const log = console.log,
	byId = document.getElementById.bind(document),
	byClass = document.getElementsByClassName.bind(document),
	byTag = document.getElementsByTagName.bind(document),
	byName = document.getElementsByName.bind(document),
	createElement = document.createElement.bind(document);




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
""")


#######################################################

#######################################################

_zip_script = Template(r"""
</ul>
</div>

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
		if (this.readyState == 4 && this.status == 200) {
			// Typical action to be performed when the document is ready:
			//document.getElementById("demo").innerHTML = xhttp.responseText;
			var resp = xhttp.responseText;
			if (resp == "SUCCESS") {
				check_prog = true;
			} else if (resp == "DONE") {
				dl_now = true;
				clearTimeout(prog_timer)
				run_dl()
			} else if (resp.startsWith("ERROR")) {
				message.innerHTML = resp;
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
	var a = document.createElement('a');
	a.href= window.location.pathname + "?zip&zid=" + id + "&download";
	a.download = filename;
	a.style.display = 'none';
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
}
var prog_timer = setInterval(function() {
	ping(window.location.pathname + "?zip&zid=" + id + "&progress")}, 500)


</script>
""")















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
