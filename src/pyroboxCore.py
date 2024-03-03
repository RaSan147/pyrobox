import traceback
import json
import string
import random
import base64
import re
from http import HTTPStatus
from http.cookies import SimpleCookie
from functools import partial
import contextlib
import urllib.request
import urllib.parse
import time
import sys
import socketserver
import socket  # For gethostbyaddr()
import shutil
import posixpath
import mimetypes
import io
import http.client
import html
import email.utils
import datetime
import argparse
from string import Template
from typing import Union
from queue import Queue
import logging
import atexit
import os

__version__ = "0.9.3"
enc = "utf-8"
DEV_MODE = False


__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler",
]


logging.basicConfig(level=logging.INFO, format='%(levelname)s: \n%(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# set INFO to see all the requests
# set WARNING to see only the requests that made change to the server
# set ERROR to see only the requests that made the errors


endl = "\n"
T = t = true = True  # too lazy to type
F = f = false = False  # too lazy to type


class Config:
	def __init__(self):
		# DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ftp_dir = "."  # DEFAULT DIRECTORY TO LAUNCH SERVER

		self.IP = None  # will be assigned by checking
		self.protocol = "http"  # DEFAULT PROTOCOL TO LAUNCH SERVER

		# DEFAULT PORT TO LAUNCH SERVER
		self.port = 6969  # DEFAULT PORT TO LAUNCH SERVER

		# UPLOAD PASSWORD SO THAT ANYONE RANDOM CAN'T UPLOAD
		# CAN BE CHANGED BY USING --password NEW_PASSWORD
		self.PASSWORD = "SECret"

		# LOGGING
		self.log_location = "./"  # fallback log_location = "./"
		# if you want to see some important LOG in browser, may contain your important information
		self.allow_web_log = True
		self.write_log = False  # if you want to write log to file
		self.log_extra = True

		# ZIP FEATURES
		self.default_zip = "zipfile"  # or "zipfile" to use python built in zip module

		# CHECK FOR MISSING REQUIREMENTS
		self.run_req_check = True

		# FILE INFO
		self.MAIN_FILE = os.path.realpath(__file__)
		self.MAIN_FILE_dir = os.path.dirname(self.MAIN_FILE)

		# OS DETECTION
		self.OS = self.get_os()

		# RUNNING SERVER STATS
		self.ftp_dir = self.get_default_dir()
		self.dev_mode = DEV_MODE
		self.ASSETS = False  # if you want to use assets folder, set this to True
		self.ASSETS_dir = os.path.join(self.MAIN_FILE_dir, "/../assets/")
		self.reload = False

		self.disabled_func = {
			"reload": False,
		}

		# TEMP FILE MAPPING
		self.temp_file = set()

		# CLEAN TEMP FILES ON EXIT
		atexit.register(self.clear_temp)

		# ASSET MAPPING
		self.file_list = {}

		# COMMANDLINE ARGUMENTS PARSER
		self.parser = argparse.ArgumentParser(add_help=False)

		# Default error message template
		self.DEFAULT_ERROR_MESSAGE = Template("""
		<!DOCTYPE HTML>
		<html lang="en">
		<html>
			<head>
				<meta charset="utf-8">
				<title>Error response</title>
			</head>
			<body>
				<h1>Error response</h1>
				<p>Error code: ${code}</p>
				<p>Message: ${message}</p>
				<p>Error code explanation: ${code} - ${explain}</p>
				<h3>PyroBox Version: ${version}</h3>
			</body>
		</html>
		""")

		self.DEFAULT_ERROR_CONTENT_TYPE = "text/html;charset=utf-8"

	def clear_temp(self):
		for i in self.temp_file:
			try:
				os.remove(i)
			except OSError:
				pass

	def get_os(self):
		from platform import system as platform_system

		out = platform_system()
		if out == "Linux" and hasattr(sys, 'getandroidapilevel'):
			# self.IP = "192.168.43.1"
			return 'Android'

		return out

	def get_default_dir(self):
		if self.get_os()== 'Android':
			return '/storage/emulated/0/'
		return './'

	def address(self):
		return f"{self.protocol}://{self.IP}:{self.port}"

	def parse_default_args(self, port=0, directory="", bind=None):
		if not port:
			port = self.port
		if not directory:
			directory = self.ftp_dir
		if not bind:
			bind = None

		parser = self.parser

		parser.add_argument('--bind', '-b',
							metavar='ADDRESS', default=bind,
							help='[xxx.xxx.xxx.xxx] Specify alternate bind address '
								'[default: all interfaces]')
		parser.add_argument('--directory', '-d', default=directory,
							help='[Value] Specify alternative directory '
								'[default: current directory]')
		parser.add_argument('port', action='store',
							default=port, type=int,
							nargs='?',
							help=f'[Value] Specify alternate port [default: {port}]')
		parser.add_argument('--version', '-v', action='version',
							version=__version__)

		parser.add_argument('-h', '--help', action='help',
								default='==SUPPRESS==',
								help=('[Option] show this help message and exit'))


		parser.add_argument('--no-extra-log',
							action='store_true',
							default=False,
							help="[Flag] Disable file path and [= + - #] based logs (default: %(default)s)")


		args = parser.parse_known_args()[0]

		self.log_extra = not args.no_extra_log

		return args


class Tools:
	def __init__(self):
		self.styles = {
			"equal": "=",
			"star": "*",
			"hash": "#",
			"dash": "-",
			"udash": "_"
		}

	@staticmethod
	def term_width():
		""" Return CLI screen size (if not found, returns default value)
		"""
		return shutil.get_terminal_size()[0]

	def text_box(self, *text, style="equal", sep=" "):
		"""
		Returns a string of text with a border around it.
		"""
		text = sep.join(map(str, text))
		term_col = shutil.get_terminal_size()[0]

		s = self.styles[style] if style in self.styles else style
		tt = ""
		for i in text.split('\n'):
			tt += i.center(term_col) + '\n'
		return (f"\n\n{s*term_col}\n{tt}{s*term_col}\n\n")

	@staticmethod
	def random_string(length=10):
		"""Generates a random string
		length : length of string
		"""
		letters = string.ascii_lowercase
		return ''.join(random.choice(letters) for i in range(length))


tools = Tools()
config = Config()



class Callable_dict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __call__(self, *key):
		return all([i in self for i in key])




def reload_server():
	"""reload the server process from file"""
	file = config.MAIN_FILE
	logger.info("Reloading...\n" +
				" ".join(
					["RE-RUNNING: ", sys.executable,
						sys.executable, file, *sys.argv[1:]]
				))
	try:
		os.execl(sys.executable, sys.executable, file, *sys.argv[1:])
	except OSError:
		traceback.print_exc()
	sys.exit(0)


def null(*args, **kwargs):
	pass


class Zfunc(object):
	"""Thread safe sequncial printing/queue task handler class"""

	__all__ = ["new", "update"]

	def __init__(self, caller, store_return=False):
		super().__init__()

		self.queue = Queue()
		# stores [args, kwargs], ...
		self.store_return = store_return
		self.returner = Queue()
		# queue to store return value if store_return enabled

		self.BUSY = False

		self.caller = caller

	def next(self):
		""" check if any item in queje and call, if already running or queue empty, returns """
		if self.queue.empty() or self.BUSY:
			return None

		self.BUSY = True
		args, kwargs = self.queue.get()

		x = self.caller(*args, **kwargs)
		if self.store_return:
			self.returner.put(x)

		self.BUSY = False

		if not self.queue.empty():
			# will make the loop continue running
			return True

	def update(self, *args, **kwargs):
		""" Uses xprint and parse string"""

		self.queue.put((args, kwargs))
		while self.next() is True:
			# use while instead of recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion.... error
			pass

	def new(self, caller, store_return=False):
		self.__init__(caller=caller, store_return=store_return)

	def destroy(self):
		"""Clear the queue
		however if running, caller function will still keep running till end"""
		self.__init__(caller=null, store_return=False)


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
	if start is not None:
		infile.seek(start)
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
		raise ValueError(f'Invalid byte range {byte_range}')

	# first, last = [x and int(x) for x in m.groups()] #

	first, last = map((lambda x: int(x) if x else None), m.groups())

	if last and last < first:
		raise ValueError(f'Invalid byte range { byte_range}')
	return first, last

# ---------------------------x--------------------------------


def URL_MANAGER(url: str):
	"""
	returns a tuple of (`path`, `query_dict`, `fragment`)\n

	`url` = `'/store?page=10&limit=15&price=ASC#dskjfhs'`\n
	`path` = `'/store'`\n
	`query_dict` = `{'page': ['10'], 'limit': ['15'], 'price': ['ASC']}`\n
	`fragment` = `dskjfhs`\n
	"""

	# url = '/store?page=10&limit=15&price#dskjfhs'
	parse_result = urllib.parse.urlparse(url)

	dict_result = Callable_dict(urllib.parse.parse_qs(
		parse_result.query, keep_blank_values=True))

	return (parse_result.path, dict_result, parse_result.fragment)



class HTTPServer(socketserver.TCPServer):

	allow_reuse_address = True  # Seems to make sense in testing environment

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
		self.header_flushed = False # true when headers are flushed by self.flush_headers()
		self.response_code_sent = False # true when response code (>=200) is sent by self.send_response()


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
				#     separate integers;
				#   - HTTP/2.4 is a lower version than HTTP/2.13, which in
				#     turn is lower than HTTP/12.3;
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

		# Load cookies from request
		# Uses standard SimpleCookie
		# doc: https://docs.python.org/3/library/http.cookies.html
		self.cookie = SimpleCookie()
		self.cookie.load(self.headers.get('Cookie', ""))
		# print(tools.text_box("Cookie: ", self.cookie))

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

			self.use_range = False

			_hash = abs(hash((self.raw_requestline, tools.random_string(10))))
			self.req_hash = base64.b64encode(
					str(_hash).encode('ascii')
				).decode()[:10]

			_w = tools.term_width()
			w = _w - len(str(self.req_hash)) - 2
			w = w//2
			if config.log_extra:
				logger.info('='*w + f' {self.req_hash} ' + '='*w + '\n' +
						'\n'.join(
								[f'{self.req_hash}|=>\t request\t: {self.command}',
								 f'{self.req_hash}|=>\t url     \t: {url_path}',
								 f'{self.req_hash}|=>\t query   \t: {query}',
								 f'{self.req_hash}|=>\t fragment\t: {fragment}',
								 f'{self.req_hash}|=>\t full url \t: {self.path}',
								 ]) + '\n' +
						'+'*w + f' {self.req_hash} ' + '+'*w
						)

			try:
				method()
			except Exception:
				traceback.print_exc()

			if config.log_extra:
				logger.info('-'*w + f' {self.req_hash} ' + '-'*w + '\n' +
						'#'*_w
						)

			# actually send the response if not already done.
			self.wfile.flush()

		except (TimeoutError, socket.timeout) as e:
			# a read or a write timed out.  Discard this connection
			self.log_error("Request timed out:", e)
			self.close_connection = True
			return

	def handle(self):
		"""Handle multiple requests if necessary."""
		self.close_connection = True

		self.handle_one_request()
		while not self.close_connection:
			self.handle_one_request()

	def send_error(self, code, message=None, explain=None, error_message_format: Template = None, cookie:Union[SimpleCookie, str]=None):
		"""Send and log an error reply.

		Arguments are
		* code:	an HTTP error code
					3 digits
		* message: a simple optional 1 line reason phrase.
					*( HTAB / SP / VCHAR / %x80-FF )
					defaults to short entry matching the response code
		* explain: a detailed message defaults to the long entry
					matching the response code.
		* error_message_format: a `string.Template` for the error message
					defaults to `config.DEFAULT_ERROR_MESSAGE`

					auto-formatting values:
						`${code}`: the HTTP error code
						`${message}`: the HTTP error message
						`${explain}`: the detailed error message
						`${version}`: the server software version string

		This sends an error response (so it must be called before any
		output has been generated), logs the error, and finally sends
		a piece of HTML explaining the error to the user.

		"""

		error_message_format = error_message_format if error_message_format else config.DEFAULT_ERROR_MESSAGE

		error_content_type = config.DEFAULT_ERROR_CONTENT_TYPE

		try:
			shortmsg, longmsg = self.responses[code]
		except KeyError:
			shortmsg, longmsg = '???', '???'
		if message is None:
			message = shortmsg
		if explain is None:
			explain = longmsg
		self.log_error("code", code, "message", message)
		self.send_response(code, message)

		self._send_cookie(cookie=cookie)

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
			content = (error_message_format.safe_substitute(
				code=code,
				message=html.escape(message, quote=False),
				explain=html.escape(explain, quote=False),
				version=__version__
			))
			body = content.encode('UTF-8', 'replace')
			self.send_header("Content-Type", error_content_type)
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
		if self.response_code_sent:
			return

		if not code//100 ==1: # 1xx - Informational (allowes multiple responses)
			self.response_code_sent = True

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

	def send_header_string(self, lines:str):
		"""Send a header multiline string to the headers buffer."""
		for i in lines.split("\r\n"):
			if not i:
				continue
			tag, _, msg = i.partition(":")
			self.send_header(tag.strip(), msg.strip())


	def _send_cookie(self, cookie:Union[SimpleCookie, str]=None):
		"""Must send cookie after self.send_response(XXX)"""
		if cookie is not None:
			if isinstance(cookie, SimpleCookie):
				cookie = cookie.output()

			self.send_header_string(cookie)




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
		"""Flush the headers buffer."""
		if self.header_flushed:
			try:
				raise RuntimeError("Headers already flushed")
			except RuntimeError:
				traceback.print_exc()
			return
		if hasattr(self, '_headers_buffer'):
			self.wfile.write(b"".join(self._headers_buffer))
			self._headers_buffer = []

		self.header_flushed = True

	def log_request(self, code='-', size='-'):
		"""Log an accepted request.

		This is called by send_response().

		"""
		if isinstance(code, HTTPStatus):
			code = code.value
		self.log_message(f'"{self.requestline}"', code, size)

	def log_error(self, *args, **kwargs):
		"""Log an error. [ERROR PRIORITY]

		This is called when a request cannot be fulfilled.  By
		default it passes the message on to log_message().

		Arguments are the same as for log_message().

		XXX This should go to the separate error log.

		"""
		self.log_message(*args, **kwargs, error=True)

	def log_warning(self, *args, **kwargs):
		"""Log a warning message [HIGH PRIORITY]"""
		self.log_message(*args, **kwargs, warning=True)

	def log_debug(self, *args, write=True, **kwargs):
		"""Log a debug message [LOWEST PRIORITY]"""
		self.log_message(*args, **kwargs, debug=True, write=write)

	def log_info(self, *args, write=False, **kwargs):
		"""Default log message [MEDIUM PRIORITY]"""
		self.log_message(*args, **kwargs, write=write)

	def _log_writer(self, message):
		os.makedirs(config.log_location, exist_ok=True)
		with open(config.log_location + 'log.txt', 'a+') as f:
			f.write(
				(f"#{self.req_hash} by [{self.address_string()}] at [{self.log_date_time_string()}]|=> {message}\n"))

	def log_message(self, *args, error=False, warning=False, debug=False, write=True, **kwargs):
		"""Log an arbitrary message.

		This is used by all other logging functions.  Override
		it if you have specific logging wishes.

		The client ip and current date/time are prefixed to
		every message.

		"""
		if not args:
			return

		sep = kwargs.get('sep', ' ')
		end = kwargs.get('end', '\n')

		message = sep.join(map(str, args)) + end

		message = f"# {self.req_hash} by [{self.address_string()}] at [{self.log_date_time_string()}]|=> {message}\n"

		if error:
			logger.error(message)
		elif warning:
			logger.warning(message)
		elif debug:
			logger.debug(message)
		else:
			logger.info(message)

		if not config.write_log:
			return

		if not hasattr(self, "Zlog_writer"):
			self.Zlog_writer = Zfunc(self._log_writer)

		try:
			self.Zlog_writer.update(message)
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
		mimetypes.init()  # try to read system mime.types
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
		'': 'application/octet-stream',  # Default
			'.py': 'text/x-python',
			'.c': 'text/x-c',
			'.h': 'text/x-c',
			'.css': 'text/css',

			'.gz': 'application/gzip',
			'.Z': 'application/octet-stream',
			'.bz2': 'application/x-bzip2',
			'.xz': 'application/x-xz',

			'.webp': 'image/webp',

			'opus': 'audio/opus',
			'.oga': 'audio/ogg',
			'.wav': 'audio/wav',

			'.ogv': 'video/ogg',
			'.ogg': 'application/ogg',
			'm4a': 'audio/mp4',
	})

	handlers = {
		'HEAD': [],
		'POST': [],
	}

	def __init__(self, *args, directory=None, **kwargs):
		if directory is None:
			directory = os.getcwd()
		# os.fspath() same as directory, but str, new in 3.6
		self.directory = os.fspath(directory)
		super().__init__(*args, **kwargs)
		self.query = Callable_dict()

	def do_GET(self):
		"""Serve a GET request."""
		try:
			resp = self.send_head()
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return

		if resp:
			try:
				self.copyfile(resp, self.wfile)
			except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
				self.log_info(tools.text_box(e.__class__.__name__,
							  e, "\nby ", self.address_string()))
			finally:
				resp.close()

	def do_(self):
		'''incase of errored request'''
		self.send_error(HTTPStatus.BAD_REQUEST, "Bad request.")

	@staticmethod
	def on_req(type='', url='', hasQ=(), QV={}, fragent='', url_regex='', func=null):
		'''called when request is received
		type: GET, POST, HEAD, ...
		url: url (must start with /)
		hasQ: if url has query
		QV: match query value
		fragent: fragent of request
		url_regex: url regex (must start with /) url regex, the url must start and end with this regex

		if query is tuple|list, it will only check existence of key
		if query is dict, it will check value of key
		'''
		self = __class__

		type = type.upper()
		if type == 'GET':
			type = 'HEAD'

		if type not in self.handlers:
			self.handlers[type] = []

		# FIXING TYPE ISSUE
		if isinstance(hasQ, str):
			hasQ = (hasQ,)

		if url == '' and url_regex == '':
			url_regex = '.*'

		to_check = (url, hasQ, QV, fragent, url_regex)

		def decorator(func):
			self.handlers[type].append((to_check, func))
			return func
		return decorator

	def test_req(self, url='', hasQ=(), QV={}, fragent='', url_regex=''):
		'''test if request is matched'

		args:
			url: url relative path (must start with /)
			hasQ: if url has query
			QV: match query value
			fragent: fragent of request
			url_regex: url regex, the url must start and end with this regex


		'''
		if url_regex and not re.search("^"+url_regex+'$', self.url_path):
				return False
		if url and url != self.url_path:
			return False

		if isinstance(hasQ, str):
			hasQ = (hasQ,)

		if hasQ and self.query(*hasQ) is False:
			return False
		if QV:
			for k, v in QV.items():
				if not self.query(k):
					return False
				if self.query[k] != v:
					return False

		if fragent and self.fragment != fragent:
			return False

		return True

	def do_HEAD(self):
		"""Serve a HEAD request."""
		resp = None
		try:
			resp = self.send_head()
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return
		finally:
			if resp:
				resp.close()

	def do_POST(self):
		"""Serve a POST request."""
		self.range = None, None

		path = self.translate_path(self.path)
		# DIRECTORY DONT CONTAIN SLASH / AT END

		url_path, query, fragment = self.url_path, self.query, self.fragment
		spathsplit = self.url_path.split("/")

		try:
			for case, func in self.handlers['POST']:
				if self.test_req(*case):
					try:
						resp = func(self, url_path=url_path, query=query,
								fragment=fragment, path=path, spathsplit=spathsplit)
					except PostError:
						traceback.print_exc()
						# break if error is raised and send BAD_REQUEST (at end of loop)
						break

					if resp:
						try:
							self.copyfile(resp, self.wfile)
						except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
							logger.info(tools.text_box(
								e.__class__.__name__, e, "\nby ", [self.address_string()]))
						finally:
							resp.close()
					return

			return self.send_error(HTTPStatus.BAD_REQUEST, "Invalid request.")

		except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
			logger.info(tools.text_box(e.__class__.__name__,
						e, "\nby ", [self.address_string()]))
			return
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return

	def redirect(self, location, cookie:Union[SimpleCookie, str]=None):
		'''redirect to location'''
		print("REDIRECT ", location)
		self.send_response(302)
		self.send_header("Location", location)
		self._send_cookie(cookie)
		self.end_headers()



	def return_txt(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/html; charset=utf-8", cookie:Union[SimpleCookie, str]=None):
		'''returns only the head to client
		and returns a file object to be used by copyfile'''
		self.log_debug(f'[RETURNED] {code} to client')
		if isinstance(msg, Template):
			msg = msg.safe_substitute(
				code=code,
				message=HTTPStatus(code).phrase,
				explain=HTTPStatus(code).description,
				version=__version__
			)
		if not isinstance(msg, bytes):
			encoded = msg.encode('utf-8', 'surrogateescape')
		else:
			encoded = msg

		box = io.BytesIO()
		box.write(encoded)
		box.seek(0)

		self.send_response(code)

		self._send_cookie(cookie)



		self.send_header("Content-Type", content_type)
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return box

	def send_txt(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/html; charset=utf-8", cookie:Union[SimpleCookie, str]=None):
		'''sends the head and file to client'''
		file = self.return_txt(msg, code, content_type, cookie)
		if self.command == "HEAD":
			return  # to avoid sending file on get request
		self.copyfile(file, self.wfile)
		file.close()

	def send_text(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/html; charset=utf-8", cookie:Union[SimpleCookie, str]=None):
		'''proxy to send_txt'''
		self.send_txt(msg, code, content_type, cookie)

	def return_script(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/javascript; charset=utf-8", cookie:Union[SimpleCookie, str]=None):
		'''proxy to send_txt'''
		return self.return_txt(msg, code, content_type, cookie)

	def send_script(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/javascript; charset=utf-8"):
		'''proxy to send_txt'''
		return self.send_txt(msg, code, content_type)

	def return_css(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/css; charset=utf-8", cookie:Union[SimpleCookie, str]=None):
		'''proxy to send_txt'''
		return self.return_txt(msg, code, content_type, cookie)

	def send_css(self, msg:Union[str, bytes, Template], code:int=200, content_type="text/css; charset=utf-8"):
		'''proxy to send_txt'''
		return self.send_txt(msg, code, content_type)

	def send_json(self, obj:Union[object, str, bytes], code=200, cookie:Union[SimpleCookie, str]=None):
		"""send object as json
		obj: json-able object or json.dumps() string"""
		if not isinstance(obj, str):
			obj = json.dumps(obj, indent=1)
		file = self.return_txt(obj, code, content_type="application/json", cookie=cookie)
		if self.command == "HEAD":
			return  # to avoid sending file on get request
		self.copyfile(file, self.wfile)
		file.close()

	def return_file(self, path, filename=None, download=False, cache_control="", cookie:Union[SimpleCookie, str]=None):
		file = None
		is_attachment = "attachment;" if (self.query("dl") or download) else ""

		first, last = 0, None

		C_encoding = None

		try:
			ctype = self.guess_type(path)

			# make sure texts are sent as utf-8
			if ctype.startswith("text/"):
				ctype += "; charset=utf-8"

			# if file is gziped, send as gzip
			if ctype == "application/gzip" and "gzip" in self.headers.get("Accept-Encoding", ""):
				C_encoding = "gzip"

			file = open(path, 'rb')
			fs = os.fstat(file.fileno())

			file_len = fs[6]
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
							file.close()

							return None

			if self.use_range:
				first = self.range[0]
				if first is None:
					first = 0
				last = self.range[1]
				if last is None or last >= file_len:
					last = file_len - 1

				if first >= file_len:  # PAUSE AND RESUME SUPPORT
					self.send_error(416, 'Requested Range Not Satisfiable', cookie=cookie)
					return None

				self.send_response(206)
				self._send_cookie(cookie=cookie)

				self.send_header('Accept-Ranges', 'bytes')

				response_length = last - first + 1

				self.send_header('Content-Range',
								f'bytes {first}-{last}/{file_len}')
				self.send_header('Content-Length', str(response_length))

			else:
				self.send_response(HTTPStatus.OK)
				self._send_cookie(cookie)

				self.send_header("Content-Length", str(file_len))

			if cache_control:
				self.send_header("Cache-Control", cache_control)

			self.send_header("Last-Modified",
							self.date_time_string(fs.st_mtime))
			self.send_header("Content-Type", ctype)

			if C_encoding:
				self.send_header("Content-Encoding", C_encoding)

			self.send_header("Content-Disposition", is_attachment+' filename="%s"' %
							(os.path.basename(path) if filename is None else filename))
			self.end_headers()

			return file

		except PermissionError:
			self.send_error(HTTPStatus.FORBIDDEN, "Permission denied", cookie)
			return None

		except OSError:
			self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie)
			return None

		except Exception:
			traceback.print_exc()

			# if f and not f.closed(): f.close()
			raise

	def send_file(self, path, filename=None, download=False, cache_control='', cookie:Union[SimpleCookie, str]=None):
		'''sends the head and file to client'''
		file = self.return_file(path, filename, download, cache_control, cookie=cookie)
		if self.command == "HEAD":
			return  # to avoid sending file on get request
		try:
			self.copyfile(file, self.wfile)
		finally:
			file.close()


	def send_head(self):
		"""Common code for GET and HEAD commands.

		This sends the response code and MIME headers.

		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.

		"""

		if 'Range' not in self.headers:
			self.range = None, None
			first, last = 0, 0

		else:
			try:
				self.range = parse_byte_range(self.headers['Range'])
				first, last = self.range
				self.use_range = True
			except ValueError as e:
				self.send_error(400, 'Invalid byte range')
				return None

		path = self.translate_path(self.path)
		# DIRECTORY DONT CONTAIN SLASH / AT END

		url_path, query, fragment = self.url_path, self.query, self.fragment

		spathsplit = self.url_path.split("/")

		# GET WILL Also BE HANDLED BY HEAD
		for case, func in self.handlers['HEAD']:
			if self.test_req(*case):
				return func(self, url_path=url_path, query=query, fragment=fragment, path=path, spathsplit=spathsplit)

		return self.send_error(HTTPStatus.NOT_FOUND, "File not found")

	def get_displaypath(self, url_path):
		"""
		Helper to produce a display path for the directory listing.
		"""

		try:
			displaypath = urllib.parse.unquote(
				url_path, errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(url_path)
		displaypath = html.escape(displaypath, quote=False)

		return displaypath

	def get_rel_path(self, filename):
		"""Return the relative path to the file, FOR OS."""
		return urllib.parse.unquote(posixpath.join(self.url_path, filename), errors='surrogatepass')

	def translate_path(self, path):
		"""Translate a /-separated PATH to the local filename syntax.

		Components that mean special things to the local file system
		(e.g. drive or directory names) are ignored.  (XXX They should
		probably be diagnosed.)

		"""
		# abandon query parameters
		path = path.split('?', 1)[0]
		path = path.split('#', 1)[0]
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

		return os.path.normpath(path)  # fix OS based path issue

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
		try:
			# check if file readable
			source.read(1)
			source.seek(0)
		except OSError as e:
			traceback.print_exc()
			raise e

		if not self.range:
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

		return self.extensions_map['']  # return 'application/octet-stream'


class PostError(Exception):
	pass


class ContentDisposition:
	def __init__(self, content_disposition):
		self.content_disposition = content_disposition
		self.items = {}
		self.parse()

	def parse(self):
		# Content-Disposition: form-data; name="post-type"
		# Content-Disposition: form-data; name="file"; filename="C:\Users\user\Desktop\test.txt"
		# Content-Disposition: form-data; name="file"; filename*=utf-8''%E6%B5%8B%E8%AF%95.txt

		line = re.subn(r"Content-Disposition:", "",
					   self.content_disposition, flags=re.IGNORECASE, count=1)[0]

		# form-data; name="post-type"
		# form-data; name="file"; filename="C:\Users\user\Desktop\test.txt"
		# form-data; name="file"; filename*=utf-8''%E6%B5%8B%E8%AF%95.txt
		parts = (i.strip() for i in line.split(";") if i.strip())

		# form-data
		# name="post-type"
		# name="file"
		# filename="C:\Users\user\Desktop\test.txt"
		# filename*=utf-8''%E6%B5%8B%E8%AF%95.txt

		for part in parts:
			pair = [i.strip() for i in part.split("=", 1)]

			key = pair[0]
			value = pair[1] if len(pair) > 1 else ""

			if key.lower() == "filename*" and value.lower().startswith("utf-8''"):
				value = urllib.parse.unquote(
					value[7:], encoding="utf-8", errors='surrogatepass')

				key = "filename"

			self.items[key.lower()] = value.strip('"')

	def get(self, key, default=None):
		return self.items.get(key.lower(), default)

	def __getitem__(self, key):
		return self.items[key.lower()]

	def __contains__(self, key):
		return key.lower() in self.items


class DealPostData:
	"""do_login

#get starting boundary
0: b'------WebKitFormBoundary7RGDIyjMpWhLXcZa\r\n'
1: b'Content-Disposition: form-data; name="post-type"\r\n'
2: b'\r\n'
3: b'login\r\n'
4: b'------WebKitFormBoundary7RGDIyjMpWhLXcZa\r\n'
5: b'Content-Disposition: form-data; name="username"\r\n'
6: b'\r\n'
7: b'xxx\r\n'
8: b'------WebKitFormBoundary7RGDIyjMpWhLXcZa\r\n'
9: b'Content-Disposition: form-data; name="password"\r\n'
10: b'\r\n'
11: b'ccc\r\n'
12: b'------WebKitFormBoundary7RGDIyjMpWhLXcZa--\r\n'
"""

	boundary = b''
	num = 0
	remainbytes = 0

	def __init__(self, req: SimpleHTTPRequestHandler) -> None:
		"""After init, must call start() to get boundary and content_length"""
		self.req = req
		self.content_length = 0
		self.content_type = ""

		self.form = FormData(req, self, fake=True)


	refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh &#128259;</div>"

	def is_multipart(self):
		return self.content_type.startswith("multipart/form-data")

	def is_urlencoded(self):
		return self.content_type.startswith("application/x-www-form-urlencoded")

	def is_form_data(self):
		return self.is_urlencoded() or self.is_multipart()

	def is_json(self):
		return self.content_type == "application/json"

	def check_size_limit(self, max_size=-1):
		"""
		* check if content size is within limit
		* return True if within limit
		"""
		if not max_size < 0 or self.content_length <= max_size:
			raise PostError(
				f"Content size limit exceeded: {self.content_length} > {max_size}")

	def get(self, show=F, strip=F, Timeout=10, chunk_size=0):
		"""
		show: print line
		strip: strip \r\n at end
		Timeout: if having network issue on any side, will keep trying to get content until Timeout (in seconds)
		"""
		req = self.req

		if self.remainbytes <= 0:
			return b""

		if chunk_size <= 0:
			chunk_size = self.remainbytes

		for _ in range(Timeout*2):
			if self.is_multipart():
				line = req.rfile.readline()
			else:
				line = req.rfile.read(chunk_size)
			if line:
				break
			time.sleep(.5)
		else:
			raise ConnectionAbortedError

		if show:
			print(f"{self.num}: {line}")
		self.remainbytes -= len(line)
		self.num += 1

		if strip and self.is_multipart() and line.endswith(b"\r\n"):
			line = line.rpartition(b"\r\n")[0]

		return line

	def get_content(self, max_size=-1, chunk_size=0):
		"""
		* get content if not multipart
		* return content
		"""

		self.check_size_limit(max_size=max_size)

		n = self.remainbytes
		line = b""

		while n > 0:
			chunk = n % 1024
			n -= chunk

			_line = self.get(chunk_size=chunk)
			if not _line:
				break
			line += _line

		return line

	def get_json(self, max_size=-1):
		"""
		* get json data
		* return parsed json data
		"""

		if not self.content_type == "application/json":
			raise PostError("Content-Type is not application/json")

		line = self.get_content(max_size=max_size)

		return json.loads(line)

	def skip(self,):
		self.get()

	def start(self):
		'''reads upto line 0'''
		req = self.req
		self.content_type = req.headers['content-type']

		if not self.content_type:
			raise PostError("POST request without Content-Type")
		if self.is_multipart():
			self.boundary = self.content_type.split("=")[1].encode()

		self.remainbytes = int(req.headers['content-length'])
		self.content_length = self.remainbytes

		# print(f"Content-Type: {self.content_type}")
		# print(f"Content-Length: {self.content_length}")
		# print(f"Request-header: {req.headers}")
		# print(self.is_form_data())

		if self.is_form_data():
			self.form = FormData(req, self)


class FormData:
	"""
	Handler for
	`multipart/form-data` and
	`application/x-www-form-urlencoded`
	"""

	def __init__(self, req: SimpleHTTPRequestHandler, dpd: DealPostData, fake=False) -> None:
		"""
		must be initialized from DealPostData
		"""
		self.req = req
		self.dpd = dpd
		self.fake = fake

		self.content_length = dpd.content_length
		self.content_type = dpd.content_type

		self.is_multipart = self.dpd.is_multipart()
		if self.fake:
			return
		self.boundary = dpd.boundary
		if self.is_multipart:
			# pass first boundary line (because after every field, there is a boundary line)
			self.pass_bound()


	def pass_bound(self):
		"""
		* pass boundary line in multipart
		* raise error if boundary not found
		"""
		if self.fake:
			raise PostError("Fake FormData")

		if not self.is_multipart:
			raise PostError("Not multipart")

		line = self.dpd.get()
		if not self.boundary in line:
			self.req.log_error(f"Content boundary missing on line {self.dpd.num}\n", [
							   line, self.boundary])

	def get_a_dline(self, line: Union[bytes, str, None] = None):
		"""
		* get a line if not provided
		* decoded if its in bytes
		* return decoded line
		"""
		if self.fake:
			raise PostError("Fake FormData")
		# only these 2 needs fake check

		if not line:
			line = self.dpd.get()

		if isinstance(line, bytes):
			line = line.decode()

		return line

	def get_file_name(self, line: Union[bytes, str, None] = None):
		"""
		* get file name from Content-Disposition
		* return file name
		"""
		line = self.get_a_dline(line)

		cd = ContentDisposition(line)
		fn = cd.get('filename')

		if not fn:
			raise PostError("Can't find out file name...")

		return fn

	def get_field_name(self, line=None):
		"""
		* get field name from Content-Disposition
		* return field name
		"""
		line = self.get_a_dline(line)

		# get name from Content-Disposition
		return ContentDisposition(line).get('name')

	def match_field_name(self, field_name: Union[None, str] = None):
		"""
		field_name: Expecting name of the field (str)
		* if None, skip checking field name
		* if `empty string`, field name must be empty too
		"""
		line = self.dpd.get()

		got_field_name = self.get_field_name(line)

		if field_name is not None and got_field_name != field_name:
			raise PostError(
				f"Invalid request: Expected {field_name} but got {got_field_name}")

		return got_field_name

	def get_multi_field(self, verify_name: Union[None, bytes, str] = None, verify_msg: Union[None, bytes, str] = None, decode=F):
		'''read a form field
		ends at boundary
		verify_name: name of the field (str|bytes|None)
		verify_msg: message to verify (str|bytes)
		decode: decode the message
		* if None, skip checking field name
		* if `empty string`, field name must be empty too

		returns: field `(name, value)` (str|bytes)
		'''
		decoded = False

		if isinstance(verify_name, bytes):
			verify_name = verify_name.decode()

		# LINE 0 (boundary)
		field_name = self.match_field_name(verify_name)  # LINE 1 (field name)
		# if not verified, raise PostError

		if not field_name:
			return None, None

		self.dpd.skip()  # LINE 2 (blank line)

		line = b''
		while 1:
			_line = self.dpd.get()  # from LINE 3 till boundary (form field value)
			if (not _line) or (self.boundary in _line):  # boundary
				break
			line += _line

		if not line:
			return None, None

		line = line.rpartition(b"\r\n")[0]  # remove \r\n at end
		if decode:
			line = line.decode()
			decoded = True
		if verify_msg is not None:
			if not decoded:
				if isinstance(verify_msg, str):
					verify_msg = verify_msg.encode()

			if line != verify_msg:
				raise PostError(
					f"Invalid post request.\n Expected: {[verify_msg]}\n Got: {[line]}")

		# self.pass_bound() # LINE 5 (boundary)

		return field_name, line

	def get_urlencoded_field(self, verify_name: Union[None, bytes, str] = None, verify_msg: Union[None, bytes, str] = None):
		"""
		* get a field from form data
		* return decoded name, value

		"""
		line = b""
		data = self.dpd.get(chunk_size=1)
		while data or data == b"&":
			line += data

			data = self.dpd.get(chunk_size=1)

		name, value = line.split(b"=", 1)
		# URL decode
		name, value = urllib.parse.unquote(name), urllib.parse.unquote(value)

		if verify_name is not None:
			if isinstance(verify_name, bytes):
				verify_name = verify_name.decode()

			if name != verify_name:
				raise PostError(
					f"Invalid post request.\n Expected: {verify_name}\n Got: {name}")

		if verify_msg is not None:
			if isinstance(verify_msg, bytes):
				verify_msg = verify_msg.decode()

			if value != verify_msg:
				raise PostError(
					f"Invalid post request.\n Expected: {verify_msg}\n Got: {value}")
		return name, value

	def get_urlencoded_iter(self, max_size=-1):
		"""
		Generator that yields the parts of the form data as dict.
		"""

		self.dpd.check_size_limit(max_size)


		data = self.dpd.get().decode()
		for part in data.split("&"):
			name, value = part.split("=")
			name, value = urllib.parse.unquote(
				name), urllib.parse.unquote(value)

			yield name, value

	def get_multipart_iter(self, max_size=-1):
		"""
		Generator that yields the parts of the form data as dict.
		"""

		self.dpd.check_size_limit(max_size)

		while True:
			field_name, value = self.get_multi_field(decode=True)
			if not field_name:
				break
			yield field_name, value

	def get_parts(self, max_size=-1):
		"""
		Generator that yields the parts of the form data.
		"""
		if self.is_multipart:
			g = self.get_multipart_iter
		else:
			g = self.get_urlencoded_iter

		for part in g(max_size):
			yield part


def _get_best_family(*address):
	infos = socket.getaddrinfo(
		*address,
		type=socket.SOCK_STREAM,
		flags=socket.AI_PASSIVE
	)
	family, type, proto, canonname, sockaddr = next(iter(infos))
	return family, sockaddr


def get_ip(bind=None):
	IP = bind  # or "127.0.0.1"
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(0)
	try:
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		try:
			if config.OS == "Android":
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
	if sys.version_info >= (3, 8):  # BACKWARD COMPATIBILITY
		ServerClass.address_family, addr = _get_best_family(bind, port)
	else:
		addr = (bind if bind != None else '', port)

	device_ip = bind or "127.0.0.1"
	# bind can be None (=> 127.0.0.1) or a string (=> 127.0.0.DDD)

	HandlerClass.protocol_version = protocol
	httpd = ServerClass(addr, HandlerClass)
	host, port = httpd.socket.getsockname()[:2]
	url_host = f'[{host}]' if ':' in host else host
	hostname = socket.gethostname()
	local_ip = config.IP if config.IP else get_ip(device_ip)
	config.IP = local_ip

	on_network = local_ip != (device_ip)

	logger.info(tools.text_box(
		# TODO: need to check since the output is "Serving HTTP on :: port 6969"
		f"Serving HTTP on {host} port {port} \n",
		# TODO: need to check since the output is "(http://[::]:6969/) ..."
		f"(http://{url_host}:{port}/) ...\n",
		f"Server is probably running on\n",
		(f"[over NETWORK] {config.address()}\n" if on_network else ""),
		f"[on DEVICE] http://localhost:{config.port} & http://127.0.0.1:{config.port}", style="star", sep=""
	)
	)
	try:
		httpd.serve_forever(poll_interval=0.1)
	except KeyboardInterrupt:
		logger.info("\nKeyboard interrupt received, exiting.")

	except OSError:
		logger.info("\nOSError received, exiting.")
	finally:
		if not config.reload:
			sys.exit(0)


class DualStackServer(ThreadingHTTPServer):  # UNSUPPORTED IN PYTHON 3.7

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
								 directory=config.ftp_dir)


def run(port=0, directory="", bind="", arg_parse=True, handler=SimpleHTTPRequestHandler):

	if arg_parse:
		args = config.parse_default_args(
			port=port, directory=directory, bind=bind)

		port = args.port
		directory = args.directory
		bind = args.bind

	logger.info(tools.text_box("Running pyroboxCore: ",
				config.MAIN_FILE, "Version: ", __version__))

	if directory == config.ftp_dir and not os.path.isdir(config.ftp_dir):
		logger.warning(
			config.ftp_dir, "not found!\nReseting directory to current directory")
		directory = "."

	handler_class = partial(handler,
							directory=directory)

	config.port = port
	if port > 65535 or port < 0:
		raise ValueError("Port must be between 0 and 65535")

	config.ftp_dir = directory

	if not config.reload:
		if sys.version_info > (3, 8):
			test(
				HandlerClass=handler_class,
				ServerClass=DualStackServer,
				port=port,
				bind=bind,
			)
		else:  # BACKWARD COMPATIBILITY
			test(
				HandlerClass=handler_class,
				ServerClass=ThreadingHTTPServer,
				port=port,
				bind=bind,
			)

	if config.reload == True:
		reload_server()


if __name__ == '__main__':
	run()
