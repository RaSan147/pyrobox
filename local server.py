# DEFAULT DIRECTORY TO LAUNCH SERVER
ftp_dir= 'G:\\'
# DEFAULT PORT TO LAUNCH SERVER
all_port= 6969
# UPLOAD PASSWORD SO THAT ANYONE RANDOM CAN'T UPLOAD
PASSWORD= "SECret".encode('utf-8')



# FEATURES
# ----------------------------------------------------------------
# PAUSE AND RESUME
# UPLOAD WITH PASSWORD
# VIDEO PLAYER
# DELETE FILE FROM REMOTE (RECYCLE BIN) # PERMANENTLY DELETE IS VULNERABLE
# RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]



# INSTALL REQUIRED PACKAGES
REQUEIREMENTS= ['send2trash',]

from subprocess import call
import sys

import pkg_resources as pkg_r

INSTALLED_PIP = [pkg.key for pkg in pkg_r.working_set]

reload = False

for i in REQUEIREMENTS:
	if i not in INSTALLED_PIP:
		call([sys.executable, "-m", "pip", "install", '--disable-pip-version-check', '--quiet', i])

from send2trash import send2trash




directory_explorer_header = '''
<!DOCTYPE HTML>

<html>
<meta http-equiv="Content-Type" content="text/html; charset=%s">

<title>%s</title>

<script>
function request_reload()
{
	fetch('/?reload?');
}
</script>




<style type="text/css">
body{
  position: relative;
  min-height: 100vh;
}

html, body, input, textarea, select, button {
	border-color: #736b5e;
	color: #e8e6e3;
	background-color: #181a1b;
}
* {
	scrollbar-color: #0f0f0f #454a4d;
}
a{
  line-height: 200%%;
  font-size: 20px;
  font-weight: 600;
  font-family: 'Gill Sans, Gill Sans MT, Calibri, Trebuchet MS, sans-serif';
  text-decoration: none;
  color: #40A4F7;
}

.link{
  color: #F00;
  background-color: #92929248;
}

.vid{
  color: #8A2BE2;
  font-weight: 300;
}

.file{
  font-weight: 300;
  color: #F02975;
}

/*video {
   override other styles to make responsive 
  width: 100%%	!important;
  height: auto   !important;
}*/

#footer {
  position: absolute;
  bottom: 0;
  width: 100%%;
  height: 2.5rem;			/* Footer height */
}
</style>
</head> '''

_js_script='''
<hr>\n<script>

const r_li = %s;


function go_link(typee, locate){
	// function to generate link for different types of actions
	return typee+"%%3F"+locate;}

// getting all the links in the directory
const linkd_li = document.getElementsByTagName('li');

for (let i = 0; i < linkd_li.length; i++) {
  // time to customize the links according to their formats

  const ele = linkd_li[i];

  if(ele.className== 'folder_'){
	// add DOWNLOAD FOLDER OPTION in it
	// TODO: add download folder option by zipping it
	// currently only shows folder size and its contents

	const dl = document.createElement('a');
	dl.innerHTML= '<span style="color: black; background-color: #40A4F7;"><b>〘↓〙</b></span>';
	dl.href = go_link('dl', r_li[i]);  // download folder link: parent/dl?folder_name
	dl.style.paddingLeft= '50px';

	ele.insertAdjacentElement("beforeend",dl);
  }

  if(ele.className== 'vid_'){
	// if its a video, add play button at the end
	// that will redirect to the video player
	// clicking main link will download the video instead

	const play = document.createElement('A');
	play.innerHTML= '<span style="color: black; background-color: #40A4F7;"><b>&nbsp▶&nbspPLAY&nbsp</b></span>';
	play.href = go_link('vid', r_li[i]);  // video player link: parent/vid?video_name
	play.style.paddingLeft= '50px';

	ele.insertAdjacentElement("beforeend",play);
  }

  if(true){
	  // recycling option for the files and folder
	  // files and folders are handled differently

	  if(ele.className== 'folder_'){
		  var xxx = "D";
	  }
	  else{
		  var xxx = "F";
	  }
	const del = document.createElement('a');
	del.innerHTML= '<span style="color: black; background-color: #40A4F7;"><b> ♻ </b></span>';
	del.href = go_link('recycle' + xxx, r_li[i]); // recycle link: parent/recycle*?file_or_folder_name
	del.style.paddingLeft= '50px';

	ele.insertAdjacentElement("beforeend",del);
  }
}


</script>

</body>
</html>
'''

# directory_explorer_body_1=



"""HTTP server classes.

Note: BaseHTTPRequestHandler doesn't implement any HTTP request; see
SimpleHTTPRequestHandler for simple implementations of GET, HEAD and POST,
and CGIHTTPRequestHandler for CGI scripts.

It does, however, optionally implement HTTP/1.1 persistent connections,
as of version 0.3.

Notes on CGIHTTPRequestHandler
------------------------------

This class implements GET and POST requests to cgi-bin scripts.

If the os.fork() function is not present (e.g. on Windows),
subprocess.Popen() is used as a fallback, with slightly altered semantics.

In all cases, the implementation is intentionally naive -- all
requests are executed synchronously.

SECURITY WARNING: DON'T USE THIS CODE UNLESS YOU ARE INSIDE A FIREWALL
-- it may execute arbitrary Python code or external programs.

Note that status code 200 is sent prior to execution of a CGI script, so
scripts cannot send other status codes such as 302 (redirect).

XXX To do:

- log requests even later (to capture byte count)
- log user-agent header and other interesting goodies
- send error log to separate file
"""


# See also:
#
# HTTP Working Group										T. Berners-Lee
# INTERNET-DRAFT											R. T. Fielding
# <draft-ietf-http-v10-spec-00.txt>					 H. Frystyk Nielsen
# Expires September 8, 1995								  March 8, 1995
#
# URL: http://www.ics.uci.edu/pub/ietf/http/draft-ietf-http-v10-spec-00.txt
#
# and
#
# Network Working Group									  R. Fielding
# Request for Comments: 2616									   et al
# Obsoletes: 2068											  June 1999
# Category: Standards Track
#
# URL: http://www.faqs.org/rfcs/rfc2616.html

# Log files
# ---------
#
# Here's a quote from the NCSA httpd docs about log file format.
#
# | The logfile format is as follows. Each line consists of:
# |
# | host rfc931 authuser [DD/Mon/YYYY:hh:mm:ss] "request" ddd bbbb
# |
# |		host: Either the DNS name or the IP number of the remote client
# |		rfc931: Any information returned by identd for this person,
# |				- otherwise.
# |		authuser: If user sent a userid for authentication, the user name,
# |				  - otherwise.
# |		DD: Day
# |		Mon: Month (calendar name)
# |		YYYY: Year
# |		hh: hour (24-hour format, the machine's timezone)
# |		mm: minutes
# |		ss: seconds
# |		request: The first line of the HTTP request as sent by the client.
# |		ddd: the status code returned by the server, - if not available.
# |		bbbb: the total number of bytes sent,
# |			  *not including the HTTP/1.0 header*, - if not available
# |
# | You can determine the name of the file accessed through request.
#
# (Actually, the latter is only true if you know the server configuration
# at the time the request was made!)

__version__ = "0.6"

__all__ = [
	"HTTPServer", "ThreadingHTTPServer", "BaseHTTPRequestHandler",
	"SimpleHTTPRequestHandler", "CGIHTTPRequestHandler",
]

import copy
import datetime
import email.utils
import html
import http.client
import io
import mimetypes
import os
import posixpath
import select
import shutil
import socket # For gethostbyaddr()
import socketserver
import sys
import time
import urllib.parse
import contextlib
from functools import partial

from http import HTTPStatus

import re


def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from 
	limit (int): maximum folder size, if bigger returns "2big"
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	"""
	if return_list: r=[]
	total_size = 0
	start_path = start_path[:-1]
	
	for dirpath, dirnames, filenames in os.walk(start_path, onerror= print):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if return_list: r.append(fp if full_dir else f)
			
			if not os.path.islink(fp):
				total_size += os.path.getsize(fp)
			if limit!=None and total_size>limit:
				print('counted upto', total_size)
				if return_list: return '2big', False
				return '2big'
	if return_list: return total_size, r
	return total_size

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
	



# PAUSE AND RESUME FEATURE ----------------------------------------

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

	first, last = [x and int(x) for x in m.groups()]
	if last and last < first:
		raise ValueError('Invalid byte range %s' % byte_range)
	return first, last

#---------------------------x--------------------------------




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

	allow_reuse_address = 1	# Seems to make sense in testing environment

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

	The following explanation of HTTP serves to guide you through the
	code as well as to expose any misunderstandings I may have about
	HTTP (so you don't need to read the code to figure out I'm wrong
	:-).

	HTTP (HyperText Transfer Protocol) is an extensible protocol on
	top of a reliable stream transport (e.g. TCP/IP).  The protocol
	recognizes three parts to a request:

	1. One line identifying the request type and path
	2. An optional set of RFC-822-style headers
	3. An optional data part

	The headers and data are separated by a blank line.

	The first line of the request has the form

	<command> <path> <version>

	where <command> is a (case-sensitive) keyword such as GET or POST,
	<path> is a string containing path information for the request,
	and <version> should be the string "HTTP/1.0" or "HTTP/1.1".
	<path> is encoded using the URL encoding scheme (using %xx to signify
	the ASCII character with hex code xx).

	The specification specifies that lines are separated by CRLF but
	for compatibility with the widest range of clients recommends
	servers also handle LF.  Similarly, whitespace in the request line
	is treated sensibly (allowing multiple spaces between components
	and allowing trailing whitespace).

	Similarly, for output, lines ought to be separated by CRLF pairs
	but most clients grok LF characters just fine.

	If the first line of the request has the form

	<command> <path>

	(i.e. <version> is left out) then this is assumed to be an HTTP
	0.9 request; this form has no optional headers and data part and
	the reply consists of just the data.

	The reply form of the HTTP 1.x protocol again has three parts:

	1. One line giving the response code
	2. An optional set of RFC-822-style headers
	3. The data

	Again, the headers and data are separated by a blank line.

	The response code line has the form

	<version> <responsecode> <responsestring>

	where <version> is the protocol version ("HTTP/1.0" or "HTTP/1.1"),
	<responsecode> is a 3-digit response code indicating success or
	failure of the request, and <responsestring> is an optional
	human-readable string explaining what the response code means.

	This server parses the request and the headers, and then calls a
	function specific to the request type (<command>).  Specifically,
	a request SPAM will be handled by a method do_SPAM().  If no
	such method exists the server sends an error response to the
	client.  If it exists, it is called with no arguments:

	do_SPAM()

	Note that the request name is case sensitive (i.e. SPAM and spam
	are different requests).

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
		except socket.timeout as e:
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
						'latin-1', 'strict'))

	def send_header(self, keyword, value):
		"""Send a MIME header to the headers buffer."""
		if self.request_version != 'HTTP/0.9':
			if not hasattr(self, '_headers_buffer'):
				self._headers_buffer = []
			self._headers_buffer.append(
				("%s: %s\r\n" % (keyword, value)).encode('latin-1', 'strict'))

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

	def __init__(self, *args, directory=None, **kwargs):
		if directory is None:
			directory = os.getcwd()
		self.directory = directory
		super().__init__(*args, **kwargs)

	def do_GET(self):
		"""Serve a GET request."""
		f = self.send_head()
		if f:
			try:
				self.copyfile(f, self.wfile)
			finally:
				f.close()

	def do_HEAD(self):
		"""Serve a HEAD request."""
		f = self.send_head()
		if f:
			f.close()

	def do_POST(self):
		"""Serve a POST request."""
		self.range = None # bug fix

		r, info = self.deal_post_data()
		print((r, info, "by: ", self.client_address))
		f = io.BytesIO()
		f.write(b'<!DOCTYPE html>')
		f.write(b"<html>\n<title>Upload Result Page</title>\n")
		f.write(b"<body>\n<h2>Upload Result Page</h2>\n")
		f.write(b"<hr>\n")
		if r:
			f.write(b"<strong>Success:</strong>")
		else:
			f.write(b"<strong>Failed:</strong>")
		f.write(info.encode())
		f.write(("<br><a href=\"%s\">back</a>" % self.headers['referer']).encode())
		f.write(b"<hr><small>Powerd By: bones7456")

		length = f.tell()
		f.seek(0)
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.send_header("Content-Length", str(length))
		self.end_headers()
		if f:
			self.copyfile(f, self.wfile)
			f.close()
		
	def deal_post_data(self):
		content_type = self.headers['content-type']
		if not content_type:
			return (False, "Content-Type header doesn't contain boundary")
		boundary = content_type.split("=")[1].encode()
		remainbytes = int(self.headers['content-length'])
		line = self.rfile.readline()
		remainbytes -= len(line)
		if not boundary in line:
			return (False, "Content NOT begin with boundary")
		line = self.rfile.readline()
		remainbytes -= len(line)
		line = self.rfile.readline()
		remainbytes -= len(line)

		# PASSWORD SYSTEM

		password= self.rfile.readline()
		print('post password: ',  password)
		if password != PASSWORD + b'\r\n': # readline returns password with \r\n at end
			return (False, "Incorrect password") # won't even read what the random guy has to say and slap 'em


		remainbytes -= len(password)
		line = self.rfile.readline()
		remainbytes -= len(line)
		if not boundary in line:
			return (False, "Content NOT begin with boundary")
		line = self.rfile.readline()
		remainbytes -= len(line)
		fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
		if not fn:
			return (False, "Can't find out file name...")
		path = self.translate_path(self.path)
		fn = os.path.join(path, fn[0])
		line = self.rfile.readline()
		remainbytes -= len(line)
		line = self.rfile.readline()
		remainbytes -= len(line)
		try:
			out = open(fn, 'wb')
		except IOError:
			return (False, "Can't create file to write, do you have permission to write?")
				
		preline = self.rfile.readline()
		remainbytes -= len(preline)
		while remainbytes > 0:
			line = self.rfile.readline()
			remainbytes -= len(line)
			if boundary in line:
				preline = preline[0:-1]
				if preline.endswith(b'\r'):
					preline = preline[0:-1]
				out.write(preline)
				out.close()
				return (True, "File '%s' upload success!" % fn)
			else:
				out.write(preline)
				preline = line
		return (False, "Unexpect Ends of data.")



	def send_head(self):
		"""Common code for GET and HEAD commands.

		This sends the response code and MIME headers.

		Return value is either a file object (which has to be copied
		to the outputfile by the caller unless the command was HEAD,
		and must be closed by the caller under all circumstances), or
		None, in which case the caller has nothing further to do.

		"""

		global reload

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
		spathtemp= os.path.split(self.path)
		pathtemp= os.path.split(path)
		spathsplit = self.path.split('/')
		
		print('path',path, '\nself.path',self.path, '\nspathtemp',spathtemp, '\npathtemp',pathtemp, '\nspathsplit',spathsplit)

		if spathsplit[-1] == "?reload?":
			# RELOADS THE SERVER BY RE-READING THE FILE, BEST FOR TESTING REMOTELY. VULNERABLE
			reload = True
			
			httpd.server_close()
			httpd.shutdown()


		if spathsplit[-1].startswith("recycleF%3F"):
			# RECYCLES THE FILE
			print("==================== current path", path)
			xpath = path.replace("recycleF?", "", 1)
			print("Recycling", xpath)
			send2trash(xpath)

		if spathsplit[-2].startswith("recycleD%3F"):
			# RECYCLES THE DIRECTORY
			print("==================== current path", path)
			xpath = path.replace("recycleD?", "", 1)
			print("Recycling", xpath)
			send2trash(xpath[:-1])



		if self.path.endswith('/') and spathsplit[-2].startswith('dl%3F'):
			
			path= self.translate_path('/'.join(spathsplit[:-2])+'/'+spathsplit[-2][5:]+'/')
			print('init')
			total_size, r = get_dir_size(path, 8*1024*1024*1024, True)  # max size limit = 8GB
			# print(total_size)
			too_big= total_size=='2big'
			# print(too_big)
			print("Directory size: " + str(total_size))
			outp='<!DOCTYPE HTML><h1>The folder size is too big</h1>\
				' if too_big else "<!DOCTYPE HTML><pre style='font-size:20px; font-weight: 600;'><b>Directory size:</b> " + humanbytes(total_size)+'</pre><br><br>The directory has:\n<hr>'+ ("\n".join(['<u>'+i+'</u><br>' for i in r]))
			encoded = outp.encode('utf-8', 'surrogateescape')

			f = io.BytesIO()
			f.write(encoded)
			
			f.seek(0)
			self.send_response(HTTPStatus.OK)
			self.send_header("Content-type", "text/html; charset=%s" % 'utf-8')
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			return f


		if spathtemp[0].startswith('/drive%3E'):
			# SWITCH TO A DIFFERENT DRIVE ON WINDOWS
			# NOT WORKING YET

			if os.path.isdir(spathtemp[0][9:]+':\\'):
				self.path = spathtemp[0][9]+':\\'
				self.directory = self.path
				try: self.path += spathtemp[0][10:]
				except: pass
				self.path = spathtemp[1]
				path = self.translate_path(self.path)

				#print('path',path, '\nself.path',self.path)
				spathtemp= os.path.split(self.path)
				pathtemp= os.path.split(path)
	
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
				self.end_headers()
				return None
			for index in "index.html", "index.htm":
				index = os.path.join(path, index)
				if os.path.exists(index):
					path = index
					break
			else:
				return self.list_directory(path)
		ctype = self.guess_type(path)
		# check for trailing "/" which should return 404. See Issue17324
		# The test for this was added in test_httpserver.py
		# However, some OS platforms accept a trailingSlash as a filename
		# See discussion on python-dev and Issue34711 regarding
		# parseing and rejection of filenames with a trailing slash
		if path.endswith("/"):
			self.send_error(HTTPStatus.NOT_FOUND, "File not found")
			return None

		
		
		if spathsplit[-1].startswith('vid%3F') or os.path.exists(path):
			# SEND VIDEO PLAYER
			if spathsplit[-1].startswith('vid%3F') and self.guess_type(os.path.join(pathtemp[0],  spathsplit[-1][6:])).startswith('video/'):

				self.path= spathtemp[0] +'/'+ spathtemp[1][6:]
				path=os.path.join(pathtemp[0],  pathtemp[1][4:])
				
				r = []
				try:
					displaypath = urllib.parse.unquote(self.path,
													errors='surrogatepass')
				except UnicodeDecodeError:
					displaypath = urllib.parse.unquote(path)
				displaypath = html.escape(displaypath, quote=False)
				enc = sys.getfilesystemencoding()
				title = 'Directory listing for %s' % displaypath
				"""r.append('<!DOCTYPE HTML>')
				r.append('<html>\n<head>')
				r.append('<meta http-equiv="Content-Type" '
						'content="text/html; charset=%s">' % enc)
				r.append('<title>%s</title>\n</head>' % title)"""
				r.append(directory_explorer_header%(enc, title))
				r.append('<body>\n<h1>%s</h1>' % title)
				r.append('<hr>\n')

				if self.guess_type(os.path.join(pathtemp[0],  spathsplit[-1][6:])) not in ['video/mp4', 'video/ogg', 'video/webm']:
					r.append('<h2>It seems HTML player can\'t play this Video format, Try Downloading</h2>')
				else:
					r.append('''
<!-- stolen from http://plyr.io -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/RaSan147/httpserver_with_many_feat@main/video.css" />

<link rel="preload" as="font" crossorigin type="font/woff2" href="https://cdn.plyr.io/static/fonts/gordita-medium.woff2" />
<link rel="preload" as="font" crossorigin type="font/woff2" href="https://cdn.plyr.io/static/fonts/gordita-bold.woff2" />

<div id="container">
	<video controls crossorigin playsinline data-poster="https://i.imgur.com/jQZ5DoV.jpg" id="player">
	
	<source src="%s" type="%s"/>
	<a href="%s" download>Download</a>
	</video>

	
<script src="https://cdn.plyr.io/3.6.9/demo.js" crossorigin="anonymous"></script>
	</div><br>'''%(self.path, ctype, self.path))

				r.append('<br><a href="%s"><button>Download</button></a></li>'
					% self.path)


				r.append('\n<hr>\n</body>\n</html>\n')
				encoded = '\n'.join(r).encode(enc, 'surrogateescape')
				f = io.BytesIO()
				f.write(encoded)
				f.seek(0)
				self.send_response(HTTPStatus.OK)
				self.send_header("Content-type", "text/html; charset=%s" % enc)
				self.send_header("Content-Length", str(len(encoded)))
				self.end_headers()
				return f

			else:
				f = open(path, 'rb')
				try:
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
						self.send_header('Content-type', ctype)
						self.send_header('Accept-Ranges', 'bytes')

						
						if last is None or last >= file_len:
							last = file_len - 1
						response_length = last - first + 1

						self.send_header('Content-Range',
										'bytes %s-%s/%s' % (first, last, file_len))
						self.send_header('Content-Length', str(response_length))

						

					else:
						self.send_response(HTTPStatus.OK)
						self.send_header("Content-type", ctype)
						self.send_header("Content-Length", str(fs[6]))
					self.send_header("Last-Modified",
									self.date_time_string(fs.st_mtime))
					self.end_headers()
					return f
				except:
					f.close()
					raise
				
		else:
			self.send_error(HTTPStatus.NOT_FOUND, "File not found")
			return None

		

		

	def list_directory(self, path):
		"""Helper to produce a directory listing (absent index.html).

		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().

		"""
		try:
			list = os.listdir(path)
		except OSError:
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None
		list.sort(key=lambda a: a.lower())
		r = []
		try:
			displaypath = urllib.parse.unquote(self.path,
											   errors='surrogatepass')
		except UnicodeDecodeError:
			displaypath = urllib.parse.unquote(path)
		displaypath = html.escape(displaypath, quote=False)
		enc = sys.getfilesystemencoding()
		title = 'Directory listing for %s' % displaypath
		r.append(directory_explorer_header%(enc, title))
		'''r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
				 '"http://www.w3.org/TR/html4/strict.dtd">')
		r.append('<meta http-equiv="Content-Type" '
				 'content="text/html; charset=%s">' % enc)
		r.append('<title>%s</title>\n</head>' % title)'''
		r.append('<body>\n<h1>%s</h1>' % title)
		r.append('<hr>\n<ul id= "linkss">')
		r_li= []
		for name in list:
			fullname = os.path.join(path, name)
			displayname = linkname = name
			# Append / for directories or @ for symbolic links
			_is_dir_ = True
			if os.path.isdir(fullname):
				displayname = name + "/"
				linkname = name + "/"
			elif os.path.islink(fullname):
				displayname = name + "@"
			else:
				_is_dir_ =False
				__, ext = posixpath.splitext(fullname)
				if ext=='.html':
					r_li.append(urllib.parse.quote(linkname, errors='surrogatepass'))
					r.append('<li class="link_"><a class= "%s" href="%s">%s</a></li>'
					% ("link", urllib.parse.quote(linkname, errors='surrogatepass'),
					   html.escape(displayname, quote=False)))

				elif self.guess_type(linkname).startswith('video/'):
					r_li.append(urllib.parse.quote(linkname, errors='surrogatepass'))
					r.append('<li class= "vid_"><a class= "%s" href="%s">🎥%s</a></li>'
					% ("vid", urllib.parse.quote(linkname, errors='surrogatepass'),
					   html.escape(displayname, quote=False)))

				else:
					r_li.append(urllib.parse.quote(linkname, errors='surrogatepass'))
					r.append('<li class= "file_"><a class= "%s" href="%s">%s</a></li>'
					% ("file", urllib.parse.quote(linkname,
										  errors='surrogatepass'),
					   html.escape(displayname, quote=False)))
			if _is_dir_:
				r_li.append(urllib.parse.quote(linkname, errors='surrogatepass'))
				r.append('<li class="folder_"><a class="%s" href="%s">️📂%s</a></li>'
					% ('folder', urllib.parse.quote(linkname, errors='surrogatepass'),
					   html.escape(displayname, quote=False)))
			
			r

			
				# Note: a link to a directory displays with @ and links with /
		r.append('</ul>\n<hr>\n<button onclick = "request_reload()">reload</button><br>')

		r.append('''<h2>Upload file</h2><br><br><form enctype="multipart/form-data" method="post">
  <p>PassWord:&nbsp;&nbsp;</p><input name="txt" type="text" label="Password"><br>
  <p>Load File:&nbsp;&nbsp;</p><input name="file" type="file" label="File"><br><br>

  <input type="submit" value="\u2B71 upload" style="background-color: #555; height: 30px; width: 100px"></form>\n''')

		r.append(_js_script%str(r_li))
		# r.append('<script>function dl_(typee, locate){window.open(typee+"%3F"+locate,"_self");}</script></body>\n</html>\n')
		encoded = '\n'.join(r).encode(enc, 'surrogateescape')
		f = io.BytesIO()
		f.write(encoded)
		f.seek(0)
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-type", "text/html; charset=%s" % enc)
		self.send_header("Content-Length", str(len(encoded)))
		self.end_headers()
		return f

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
		return path

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
		else:
			return self.extensions_map['']

	if not mimetypes.inited:
		mimetypes.init() # try to read system mime.types
	extensions_map = mimetypes.types_map.copy()
	extensions_map.update({
		'': 'application/octet-stream', # Default
		'.py': 'text/plain',
		'.c': 'text/plain',
		'.h': 'text/plain',
		})


# Utilities for CGIHTTPRequestHandler

def _url_collapse_path(path):
	"""
	Given a URL path, remove extra '/'s and '.' path elements and collapse
	any '..' references and returns a collapsed path.

	Implements something akin to RFC-2396 5.2 step 6 to parse relative paths.
	The utility of this function is limited to is_cgi method and helps
	preventing some security attacks.

	Returns: The reconstituted URL, which will always start with a '/'.

	Raises: IndexError if too many '..' occur within the path.

	"""
	# Query component should not be involved.
	path, _, query = path.partition('?')
	path = urllib.parse.unquote(path)

	# Similar to os.path.split(os.path.normpath(path)) but specific to URL
	# path semantics rather than local operating system semantics.
	path_parts = path.split('/')
	head_parts = []
	for part in path_parts[:-1]:
		if part == '..':
			head_parts.pop() # IndexError if more '..' than prior parts
		elif part and part != '.':
			head_parts.append( part )
	if path_parts:
		tail_part = path_parts.pop()
		if tail_part:
			if tail_part == '..':
				head_parts.pop()
				tail_part = ''
			elif tail_part == '.':
				tail_part = ''
	else:
		tail_part = ''

	if query:
		tail_part = '?'.join((tail_part, query))

	splitpath = ('/' + '/'.join(head_parts), tail_part)
	collapsed_path = "/".join(splitpath)

	return collapsed_path



nobody = None

def nobody_uid():
	"""Internal routine to get nobody's uid"""
	global nobody
	if nobody:
		return nobody
	try:
		import pwd
	except ImportError:
		return -1
	try:
		nobody = pwd.getpwnam('nobody')[2]
	except KeyError:
		nobody = 1 + max(x[2] for x in pwd.getpwall())
	return nobody


def executable(path):
	"""Test for executable file."""
	return os.access(path, os.X_OK)


class CGIHTTPRequestHandler(SimpleHTTPRequestHandler):

	"""Complete HTTP server with GET, HEAD and POST commands.

	GET and HEAD also support running CGI scripts.

	The POST command is *only* implemented for CGI scripts.

	"""

	# Determine platform specifics
	have_fork = hasattr(os, 'fork')

	# Make rfile unbuffered -- we need to read one line and then pass
	# the rest to a subprocess, so we can't use buffered input.
	rbufsize = 0

	def do_POST(self):
		"""Serve a POST request.

		This is only implemented for CGI scripts.

		"""

		if self.is_cgi():
			self.run_cgi()
		else:
			self.send_error(
				HTTPStatus.NOT_IMPLEMENTED,
				"Can only POST to CGI scripts")

	def send_head(self):
		"""Version of send_head that support CGI scripts"""
		if self.is_cgi():
			return self.run_cgi()
		else:
			return SimpleHTTPRequestHandler.send_head(self)

	def is_cgi(self):
		"""Test whether self.path corresponds to a CGI script.

		Returns True and updates the cgi_info attribute to the tuple
		(dir, rest) if self.path requires running a CGI script.
		Returns False otherwise.

		If any exception is raised, the caller should assume that
		self.path was rejected as invalid and act accordingly.

		The default implementation tests whether the normalized url
		path begins with one of the strings in self.cgi_directories
		(and the next character is a '/' or the end of the string).

		"""
		collapsed_path = _url_collapse_path(self.path)
		dir_sep = collapsed_path.find('/', 1)
		head, tail = collapsed_path[:dir_sep], collapsed_path[dir_sep+1:]
		if head in self.cgi_directories:
			self.cgi_info = head, tail
			return True
		return False


	cgi_directories = ['/cgi-bin', '/htbin']

	def is_executable(self, path):
		"""Test whether argument path is an executable file."""
		return executable(path)

	def is_python(self, path):
		"""Test whether argument path is a Python script."""
		head, tail = os.path.splitext(path)
		return tail.lower() in (".py", ".pyw")

	def run_cgi(self):
		"""Execute a CGI script."""
		dir, rest = self.cgi_info
		path = dir + '/' + rest
		i = path.find('/', len(dir)+1)
		while i >= 0:
			nextdir = path[:i]
			nextrest = path[i+1:]

			scriptdir = self.translate_path(nextdir)
			if os.path.isdir(scriptdir):
				dir, rest = nextdir, nextrest
				i = path.find('/', len(dir)+1)
			else:
				break

		# find an explicit query string, if present.
		rest, _, query = rest.partition('?')

		# dissect the part after the directory name into a script name &
		# a possible additional path, to be stored in PATH_INFO.
		i = rest.find('/')
		if i >= 0:
			script, rest = rest[:i], rest[i:]
		else:
			script, rest = rest, ''

		scriptname = dir + '/' + script
		scriptfile = self.translate_path(scriptname)
		if not os.path.exists(scriptfile):
			self.send_error(
				HTTPStatus.NOT_FOUND,
				"No such CGI script (%r)" % scriptname)
			return
		if not os.path.isfile(scriptfile):
			self.send_error(
				HTTPStatus.FORBIDDEN,
				"CGI script is not a plain file (%r)" % scriptname)
			return
		ispy = self.is_python(scriptname)
		if self.have_fork or not ispy:
			if not self.is_executable(scriptfile):
				self.send_error(
					HTTPStatus.FORBIDDEN,
					"CGI script is not executable (%r)" % scriptname)
				return

		# Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
		# XXX Much of the following could be prepared ahead of time!
		env = copy.deepcopy(os.environ)
		env['SERVER_SOFTWARE'] = self.version_string()
		env['SERVER_NAME'] = self.server.server_name
		env['GATEWAY_INTERFACE'] = 'CGI/1.1'
		env['SERVER_PROTOCOL'] = self.protocol_version
		env['SERVER_PORT'] = str(self.server.server_port)
		env['REQUEST_METHOD'] = self.command
		uqrest = urllib.parse.unquote(rest)
		env['PATH_INFO'] = uqrest
		env['PATH_TRANSLATED'] = self.translate_path(uqrest)
		env['SCRIPT_NAME'] = scriptname
		if query:
			env['QUERY_STRING'] = query
		env['REMOTE_ADDR'] = self.client_address[0]
		authorization = self.headers.get("authorization")
		if authorization:
			authorization = authorization.split()
			if len(authorization) == 2:
				import base64, binascii
				env['AUTH_TYPE'] = authorization[0]
				if authorization[0].lower() == "basic":
					try:
						authorization = authorization[1].encode('ascii')
						authorization = base64.decodebytes(authorization).\
										decode('ascii')
					except (binascii.Error, UnicodeError):
						pass
					else:
						authorization = authorization.split(':')
						if len(authorization) == 2:
							env['REMOTE_USER'] = authorization[0]
		# XXX REMOTE_IDENT
		if self.headers.get('content-type') is None:
			env['CONTENT_TYPE'] = self.headers.get_content_type()
		else:
			env['CONTENT_TYPE'] = self.headers['content-type']
		length = self.headers.get('content-length')
		if length:
			env['CONTENT_LENGTH'] = length
		referer = self.headers.get('referer')
		if referer:
			env['HTTP_REFERER'] = referer
		accept = []
		for line in self.headers.getallmatchingheaders('accept'):
			if line[:1] in "\t\n\r ":
				accept.append(line.strip())
			else:
				accept = accept + line[7:].split(',')
		env['HTTP_ACCEPT'] = ','.join(accept)
		ua = self.headers.get('user-agent')
		if ua:
			env['HTTP_USER_AGENT'] = ua
		co = filter(None, self.headers.get_all('cookie', []))
		cookie_str = ', '.join(co)
		if cookie_str:
			env['HTTP_COOKIE'] = cookie_str
		# XXX Other HTTP_* headers
		# Since we're setting the env in the parent, provide empty
		# values to override previously set values
		for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
				  'HTTP_USER_AGENT', 'HTTP_COOKIE', 'HTTP_REFERER'):
			env.setdefault(k, "")

		self.send_response(HTTPStatus.OK, "Script output follows")
		self.flush_headers()

		decoded_query = query.replace('+', ' ')

		if self.have_fork:
			# Unix -- fork as we should
			args = [script]
			if '=' not in decoded_query:
				args.append(decoded_query)
			nobody = nobody_uid()
			self.wfile.flush() # Always flush before forking
			pid = os.fork()
			if pid != 0:
				# Parent
				pid, sts = os.waitpid(pid, 0)
				# throw away additional data [see bug #427345]
				while select.select([self.rfile], [], [], 0)[0]:
					if not self.rfile.read(1):
						break
				if sts:
					self.log_error("CGI script exit status %#x", sts)
				return
			# Child
			try:
				try:
					os.setuid(nobody)
				except OSError:
					pass
				os.dup2(self.rfile.fileno(), 0)
				os.dup2(self.wfile.fileno(), 1)
				os.execve(scriptfile, args, env)
			except:
				self.server.handle_error(self.request, self.client_address)
				os._exit(127)

		else:
			# Non-Unix -- use subprocess
			import subprocess
			cmdline = [scriptfile]
			if self.is_python(scriptfile):
				interp = sys.executable
				if interp.lower().endswith("w.exe"):
					# On Windows, use python.exe, not pythonw.exe
					interp = interp[:-5] + interp[-4:]
				cmdline = [interp, '-u'] + cmdline
			if '=' not in query:
				cmdline.append(query)
			self.log_message("command: %s", subprocess.list2cmdline(cmdline))
			try:
				nbytes = int(length)
			except (TypeError, ValueError):
				nbytes = 0
			p = subprocess.Popen(cmdline,
								 stdin=subprocess.PIPE,
								 stdout=subprocess.PIPE,
								 stderr=subprocess.PIPE,
								 env = env
								 )
			if self.command.lower() == "post" and nbytes > 0:
				data = self.rfile.read(nbytes)
			else:
				data = None
			# throw away additional data [see bug #427345]
			while select.select([self.rfile._sock], [], [], 0)[0]:
				if not self.rfile._sock.recv(1):
					break
			stdout, stderr = p.communicate(data)
			self.wfile.write(stdout)
			if stderr:
				self.log_error('%s', stderr)
			p.stderr.close()
			p.stdout.close()
			status = p.returncode
			if status:
				self.log_error("CGI script exit status %#x", status)
			else:
				self.log_message("CGI script exited OK")


def _get_best_family(*address):
	infos = socket.getaddrinfo(
		*address,
		type=socket.SOCK_STREAM,
		flags=socket.AI_PASSIVE,
	)
	family, type, proto, canonname, sockaddr = next(iter(infos))
	return family, sockaddr


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
	print(
		f"Serving HTTP on {host} port {port} "
		f"(http://{url_host}:{port}/) ..."
	)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print("\nKeyboard interrupt received, exiting.")
		if not reload:
			sys.exit(0)
		
	except OSError:
		print("\nOSError received, exiting.")
		if not reload:
			sys.exit(0)


class DualStackServer(ThreadingHTTPServer): # UNSUPPORTED IN PYTHON 3.7
	def server_bind(self):
		# suppress exception when protocol is IPv4
		with contextlib.suppress(Exception):
			self.socket.setsockopt(
				socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
		return super().server_bind()

import pathlib
print(pathlib.Path(__file__))

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--cgi', action='store_true',
					   help='Run as CGI Server')
	parser.add_argument('--bind', '-b', metavar='ADDRESS',
						help='Specify alternate bind address '
							 '[default: all interfaces]')
	parser.add_argument('--directory', '-d', default=ftp_dir,
						help='Specify alternative directory '
						'[default:current directory]')
	parser.add_argument('port', action='store',
						default=all_port, type=int,
						nargs='?',
						help='Specify alternate port [default: 8000]')
	args = parser.parse_args()
	if args.cgi:
		handler_class = CGIHTTPRequestHandler
	else:
		handler_class = partial(SimpleHTTPRequestHandler,
								directory=args.directory)
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

if reload == True:
	import pathlib
	xxx = str(pathlib.Path(__file__))
	call([sys.executable, xxx, *sys.argv[1:]])
	sys.exit(0)