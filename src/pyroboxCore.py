__version__ = "0.7.4"
enc = "utf-8"
__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler",

]

import os
import atexit
import logging
from queue import Queue
from typing import Union
from string import Template

import argparse


logging.basicConfig(level=logging.INFO, format='%(levelname)s: \n%(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# set INFO to see all the requests
# set WARNING to see only the requests that made change to the server
# set ERROR to see only the requests that made the errors



endl = "\n"
T = t = true = True # too lazy to type
F = f = false = False # too lazy to type

class Config:
	def __init__(self):
		# DEFAULT DIRECTORY TO LAUNCH SERVER
		self.ftp_dir = "." # DEFAULT DIRECTORY TO LAUNCH SERVER

		self.IP = None # will be assigned by checking

		# DEFAULT PORT TO LAUNCH SERVER
		self.port= 6969  # DEFAULT PORT TO LAUNCH SERVER

		# UPLOAD PASSWORD SO THAT ANYONE RANDOM CAN'T UPLOAD
		# CAN BE CHANGED BY USING --password NEW_PASSWORD
		self.PASSWORD= "SECret"

		# LOGGING
		self.log_location = "./"  # fallback log_location = "./"
		self.allow_web_log = True # if you want to see some important LOG in browser, may contain your important information
		self.write_log = False # if you want to write log to file

		# ZIP FEATURES
		self.default_zip = "zipfile" # or "zipfile" to use python built in zip module

		# CHECK FOR MISSING REQUEIREMENTS
		self.run_req_check = True

		# FILE INFO
		self.MAIN_FILE = os.path.realpath(__file__)
		self.MAIN_FILE_dir = os.path.dirname(self.MAIN_FILE)


		# OS DETECTION
		self.OS = self.get_os()


		# RUNNING SERVER STATS
		self.ftp_dir = self.get_default_dir()
		self.dev_mode = False
		self.ASSETS = False # if you want to use assets folder, set this to True
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
		return './'


	def address(self):
		return "http://%s:%i"%(self.IP, self.port)

	def parse_default_args(self, port = None, directory = None, bind = None, ):
		if port is None:
			port = self.port
		if directory is None:
			directory = self.ftp_dir
		if bind is None:
			bind = None

		parser = self.parser

		parser.add_argument('--bind', '-b',
							metavar='ADDRESS', default=bind,
							help='Specify alternate bind address '
								'[default: all interfaces]')
		parser.add_argument('--directory', '-d', default=directory,
							help='Specify alternative directory '
							'[default: current directory]')
		parser.add_argument('port', action='store',
							default=port, type=int,
							nargs='?',
							help=f'Specify alternate port [default: {port}]')
		parser.add_argument('--version', '-v', action='version',
							version=__version__)

		self.parser.add_argument('-h', '--help', action='help',
								default='==SUPPRESS==',
								help=('show this help message and exit'))

		args = parser.parse_known_args()[0]

		return args









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

import re
import base64

import random
import string
import json
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

	def term_width(self):
		return shutil.get_terminal_size()[0]

	def text_box(self, *text, style = "equal", sep=" "):
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

	def random_string(self, length=10):
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
	logger.info("Reloading...\n"+
				" ".join(
					["RE-RUNNING: ", sys.executable, sys.executable, file, *sys.argv[1:]]
				))
	try:
		os.execl(sys.executable, sys.executable, file, *sys.argv[1:])
	except:
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


	dict_result = Callable_dict(urllib.parse.parse_qs(parse_result.query, keep_blank_values=True))

	return (parse_result.path, dict_result, parse_result.fragment)



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

			self.use_range = False


			_hash = abs(hash((self.raw_requestline, tools.random_string(10))))
			self.req_hash = base64.b64encode(str(_hash).encode('ascii')).decode()[:10]

			_w = tools.term_width()
			w = _w - len(str(self.req_hash)) -2
			w = w//2
			logger.info('='*w + f' {self.req_hash} ' + '='*w + '\n'+
					'\n'.join(
						[f'{self.req_hash}|=>\t request\t: {self.command}',
						f'{self.req_hash}|=>\t url     \t: {url_path}',
						f'{self.req_hash}|=>\t query   \t: {query}',
						f'{self.req_hash}|=>\t fragment\t: {fragment}',
						f'{self.req_hash}|=>\t full url \t: {self.path}',
						]) + '\n'+
					'+'*w + f' {self.req_hash} ' + '+'*w
				)




			try:
				method()
			except Exception:
				traceback.print_exc()

			logger.info('-'*w + f' {self.req_hash} ' + '-'*w + '\n'+
						'#'*_w
						)
			self.wfile.flush() #actually send the response if not already done.
		except (TimeoutError, socket.timeout) as e:
			#a read or a write timed out.  Discard this connection
			self.log_error("Request timed out:", e)
			self.close_connection = True
			return

	def handle(self):
		"""Handle multiple requests if necessary."""
		self.close_connection = True

		self.handle_one_request()
		while not self.close_connection:
			self.handle_one_request()

	def send_error(self, code, message=None, explain=None, error_message_format:Template=None):
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
				code= code,
				message= html.escape(message, quote=False),
				explain= html.escape(explain, quote=False),
				version= __version__
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
		self.log_message(f'"{self.requestline}"', code, size)

	def log_error(self, *args):
		"""Log an error. [ERROR PRIORITY]

		This is called when a request cannot be fulfilled.  By
		default it passes the message on to log_message().

		Arguments are the same as for log_message().

		XXX This should go to the separate error log.

		"""
		self.log_message(args, error = True)

	def log_warning(self, *args):
		"""Log a warning message [HIGH PRIORITY]"""
		self.log_message(args, warning = True)

	def log_debug(self, *args, write = True):
		"""Log a debug message [LOWEST PRIORITY]"""
		self.log_message(args, debug = True, write = write)

	def log_info(self, *args, write = False):
		"""Default log message [MEDIUM PRIORITY]"""
		self.log_message(args, write = write)

	def _log_writer(self, message):
		os.makedirs(config.log_location, exist_ok=True)
		with open(config.log_location + 'log.txt','a+') as f:
			f.write((f"#{self.req_hash} by [{self.address_string()}] at [{self.log_date_time_string()}]|=> {message}\n"))



	def log_message(self, *args, error = False, warning = False, debug = False, write = True):
		"""Log an arbitrary message.

		This is used by all other logging functions.  Override
		it if you have specific logging wishes.

		The client ip and current date/time are prefixed to
		every message.

		"""

		message = ' '.join(map(str, args))

		message = ("# %s by [%s] at [%s] %s\n" %
						 (self.req_hash, self.address_string(),
						  self.log_date_time_string(),
						  message))
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
		self.directory = os.fspath(directory) # same as directory, but str, new in 3.6
		super().__init__(*args, **kwargs)
		self.query = Callable_dict()


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
				self.log_info(tools.text_box(e.__class__.__name__, e,"\nby ", self.address_string()))
			finally:
				f.close()

	def do_(self):
		'''incase of errored request'''
		self.send_error(HTTPStatus.BAD_REQUEST, "Bad request.")


	@staticmethod
	def on_req(type='', url='', hasQ=(), QV={}, fragent='', url_regex = '', func=null):
		'''called when request is received
		type: GET, POST, HEAD, ...
		url: url (must start with /)
		hasQ: if url has query
		QV: match query value
		fragent: fragent of request
		url_regex: url regex (must start with /) url regex, the url must start and end with this regex

		if query is tuple, it will only check existence of key
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

		if url=='' and url_regex=='':
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
		if url_regex:
			if not re.search("^"+url_regex+'$', self.url_path): return False
		elif url and url!=self.url_path: return False

		if isinstance(hasQ, str):
			hasQ = (hasQ,)

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
		self.range = None, None


		path = self.translate_path(self.path)
		# DIRECTORY DONT CONTAIN SLASH / AT END

		url_path, query, fragment = self.url_path, self.query, self.fragment
		spathsplit = self.url_path.split("/")


		try:
			for case, func in self.handlers['POST']:
				if self.test_req(*case):
					try:
						f = func(self, url_path=url_path, query=query, fragment=fragment, path=path, spathsplit=spathsplit)
					except PostError:
						traceback.print_exc()
						break # break if error is raised and send BAD_REQUEST (at end of loop)

					if f:
						try:
							self.copyfile(f, self.wfile)
						except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
							logger.info(tools.text_box(e.__class__.__name__, e,"\nby ", [self.address_string()]))
						finally:
							f.close()
					return



			return self.send_error(HTTPStatus.BAD_REQUEST, "Invalid request.")

		except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
			logger.info(tools.text_box(e.__class__.__name__, e,"\nby ", [self.address_string()]))
			return
		except Exception as e:
			traceback.print_exc()
			self.send_error(500, str(e))
			return


	def redirect(self, location):
		'''redirect to location'''
		self.send_response(HTTPStatus.FOUND)
		self.send_header("Location", location)
		self.end_headers()

	def return_txt(self, code, msg, content_type="text/html; charset=utf-8"):
		'''returns only the head to client
		and returns a file object to be used by copyfile'''
		self.log_debug(f'[RETURNED] {code} to client')
		if not isinstance(msg, bytes):
			encoded = msg.encode('utf-8', 'surrogateescape')
		else:
			encoded = msg

		f = io.BytesIO()
		f.write(encoded)
		f.seek(0)

		self.send_response(code)
		self.send_header("Content-type", content_type)
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return f

	def send_txt(self, code, msg, content_type="text/html; charset=utf-8"):
		'''sends the head and file to client'''
		f = self.return_txt(code, msg, content_type)
		if self.command == "HEAD":
			return # to avoid sending file on get request
		self.copyfile(f, self.wfile)
		f.close()

	def send_json(self, obj):
		"""send object as json
		obj: json-able object or json.dumps() string"""
		if not isinstance(obj, str):
			obj = json.dumps(obj, indent=1)
		f = self.return_txt(200, obj, content_type="application/json")
		if self.command == "HEAD":
			return # to avoid sending file on get request
		self.copyfile(f, self.wfile)
		f.close()

	def return_file(self, path, filename=None, download=False):
		f = None
		is_attachment = "attachment;" if (self.query("dl") or download) else ""

		first, last = 0, None

		try:
			ctype = self.guess_type(path)

			f = open(path, 'rb')
			fs = os.fstat(f.fileno())

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
							f.close()

							return None

			if self.use_range:
				first = self.range[0]
				if first is None:
					first = 0
				last = self.range[1]
				if last is None or last >= file_len:
					last = file_len - 1

				if first >= file_len: # PAUSE AND RESUME SUPPORT
					self.send_error(416, 'Requested Range Not Satisfiable')
					return None

				self.send_response(206)
				self.send_header('Content-Type', ctype)
				self.send_header('Accept-Ranges', 'bytes')


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


		except Exception:
			traceback.print_exc()

			# if f and not f.closed(): f.close()
			raise

	def send_file(self, path, filename=None, download=False):
		'''sends the head and file to client'''
		f = self.return_file(path, filename, download)
		if self.command == "HEAD":
			return # to avoid sending file on get request
		try:
			self.copyfile(f, self.wfile)
		finally:
			f.close()



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



		for case, func in self.handlers['HEAD']: # GET WILL Also BE HANDLED BY HEAD
			if self.test_req(*case):
				return func(self, url_path=url_path, query=query, fragment=fragment, path=path, spathsplit=spathsplit)

		return self.send_error(HTTPStatus.NOT_FOUND, "File not found")




	def get_displaypath(self, url_path):
		"""
		Helper to produce a display path for the directory listing.
		"""

		try:
			displaypath = urllib.parse.unquote(url_path, errors='surrogatepass')
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
			try:
				source.read(1)
			except:
				traceback.print_exc()
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



class PostError(Exception):
	pass




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

	def __init__(self, req:SimpleHTTPRequestHandler) -> None:
		self.req = req


	refresh = "<br><br><div class='pagination center' onclick='window.location.reload()'>Refresh &#128259;</div>"


	def get(self, show=F, strip=F, Timeout=20):
		"""
		show: print line
		strip: strip \r\n at end
		Timeout: if having network issue on any side, will keep trying to get content until Timeout (in seconds)
		"""
		req = self.req


		for _ in range(Timeout*2):
			line = req.rfile.readline()
			if line:
				break
			time.sleep(.5)
		else:
			raise ConnectionAbortedError
		self.num+=1
		if show:
			print(f"{self.num}: {line}")
		self.remainbytes -= len(line)

		if strip and line.endswith(b"\r\n"):
			line = line.rpartition(b"\r\n")[0]

		return line

	def pass_bound(self):
		line = self.get()
		if not self.boundary in line:
			self.req.log_error("Content NOT begin with boundary\n", [line, self.boundary])

	def get_name(self, line=None, ):
		if not line:
			line = self.get()
		try:
			return re.findall(r'Content-Disposition.*name="(.*?)"', line.decode())[0]
		except: return None

	def match_name(self, field_name:Union[None, str]=None):
		"""
		field_name: name of the field (str)
		* if None, skip checking field name
		* if `empty string`, field name must be empty too
		"""
		line = self.get()

		if field_name is not None and self.get_name(line)!=field_name:
			raise PostError(f"Invalid request: Expected {field_name} but got {self.get_name(line)}")

		return line


	def skip(self,):
		self.get()

	def start(self):
		'''reads upto line 0'''
		req = self.req
		content_type = req.headers['content-type']

		if not content_type:
			raise PostError("Content-Type header doesn't contain boundary")
		self.boundary = content_type.split("=")[1].encode()

		self.remainbytes = int(req.headers['content-length'])


		self.pass_bound()# LINE 0


	def get_part(self, verify_name:Union[None, bytes, str] =None, verify_msg:Union[None, bytes, str] =None, decode=F):
		'''read a form field
		ends at boundary
		verify_name: name of the field (str|bytes|None)
		verify_msg: message to verify (str|bytes)
		decode: decode the message
		* if None, skip checking field name
		* if `empty string`, field name must be empty too'''
		decoded = False

		if isinstance(verify_name, bytes):
			verify_name = verify_name.decode()

		field_name = self.match_name(verify_name) # LINE 1 (field name)
		# if not verified, raise PostError

		self.skip() # LINE 2 (blank line)

		line = b''
		while 1:
			_line = self.get() # from LINE 4 till boundary (form field value)
			if self.boundary in _line: # boundary
				break
			line += _line

		line = line.rpartition(b"\r\n")[0] # remove \r\n at end
		if decode:
			line = line.decode()
			decoded = True
		if verify_msg is not None:
			if not decoded:
				if isinstance(verify_msg, str):
					verify_msg = verify_msg.encode()

			if line != verify_msg:
				raise PostError(f"Invalid post request.\n Expected: {[verify_msg]}\n Got: {[line]}")

		# self.pass_bound() # LINE 5 (boundary)

		return field_name, line






def _get_best_family(*address):
	infos = socket.getaddrinfo(
		*address,
		type=socket.SOCK_STREAM,
		flags=socket.AI_PASSIVE
	)
	family, type, proto, canonname, sockaddr = next(iter(infos))
	return family, sockaddr

def get_ip(bind=None):
	IP = bind # or "127.0.0.1"
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
	if sys.version_info>=(3,8): # BACKWARD COMPATIBILITY
		ServerClass.address_family, addr = _get_best_family(bind, port)
	else:
		addr =(bind if bind!=None else '', port)

	device_ip = bind or "127.0.0.1"
	# bind can be None (=> 127.0.0.1) or a string (=> 127.0.0.DDD)

	HandlerClass.protocol_version = protocol
	httpd = ServerClass(addr, HandlerClass)
	host, port = httpd.socket.getsockname()[:2]
	url_host = f'[{host}]' if ':' in host else host
	hostname = socket.gethostname()
	local_ip = config.IP if config.IP else get_ip(device_ip)
	config.IP= local_ip


	on_network = local_ip!=(device_ip)

	logger.info(tools.text_box(
		f"Serving HTTP on {host} port {port} \n", #TODO: need to check since the output is "Serving HTTP on :: port 6969"
		f"(http://{url_host}:{port}/) ...\n", #TODO: need to check since the output is "(http://[::]:6969/) ..."
		f"Server is probably running on\n",
		(f"[over NETWORK] {config.address()}\n" if on_network else ""),
		f"[on DEVICE] http://localhost:{config.port} & http://127.0.0.1:{config.port}"
		, style="star", sep=""
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
									directory=config.ftp_dir)




def run(port = None, directory = None, bind = None, arg_parse= True, handler = SimpleHTTPRequestHandler):

	if arg_parse:
		args = config.parse_default_args(port=port, directory=directory, bind=bind)

		port = args.port
		directory = args.directory
		bind = args.bind



	logger.info(tools.text_box("Running pyroboxCore: ", config.MAIN_FILE, "Version: ", __version__))


	if directory == config.ftp_dir and not os.path.isdir(config.ftp_dir):
		logger.warning(config.ftp_dir, "not found!\nReseting directory to current directory")
		directory = "."

	handler_class = partial(handler,
								directory=directory)

	config.port = port
	if port > 65535 or port < 0:
		raise ValueError("Port must be between 0 and 65535")

	config.ftp_dir = directory

	if not config.reload:
		if sys.version_info>(3,8):
			test(
			HandlerClass=handler_class,
			ServerClass=DualStackServer,
			port=port,
			bind=bind,
			)
		else: # BACKWARD COMPATIBILITY
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
