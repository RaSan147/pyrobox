import os
import posixpath
from http import HTTPStatus
import urllib.parse
import html
from typing import Callable, Optional, Union

from pyrobox_ServerHost import ServerHost as SH, SimpleCookie

from user_mgmt import User
import _page_templates as pt

from _fs_utils import get_titles, fmbytes


class ListMaker:
	"""Directory listing + human sorting.

	Pass an optional ``sort_algorithm`` with the ``natsort.humansorted`` shape
	``fn(seq, key=None) -> list``. When omitted, :meth:`custom_sort` is used.
	"""

	def __init__(self, sort_algorithm: Optional[Callable] = None) -> None:
		self.sort_algorithm = sort_algorithm

	def set_sort_algorithm(self, fn: Optional[Callable] = None) -> None:
		"""Install a list sorter, or ``None`` to use :meth:`custom_sort`."""
		self.sort_algorithm = fn

	@staticmethod
	def custom_sort(item):
		if isinstance(item, str):
			out_parts = []
			parts = item.split()
			for n, part in enumerate(parts):
				part = part.lower()
				# If token looks like a dotted version (e.g. 1.2.3), keep as version tuple
				if "." in part and all(p.isdigit() for p in part.split(".")):
					parts[n] = tuple(int(p) for p in part.split("."))
				else:
					try:
						f = float(part)
						# prefer ints where possible
						parts[n] = int(f) if f.is_integer() else f
					except ValueError:
						part = part.replace(".", " . ")
						parts_ = part.split()
						for n_, part_ in enumerate(parts_):
							try:
								f2 = float(part_)
								parts_[n_] = int(f2) if f2.is_integer() else f2
							except ValueError:
								pass
						parts[n] = parts_

			for part in parts:
				if isinstance(part, list):
					out_parts.extend(part)
				else:
					out_parts.append(part)

			# Normalize numeric elements to tuples so comparisons never mix types.
			# Numeric/version parts become (0, tuple_of_numbers), text become (1, string)
			normalized = []
			for p in out_parts:
				if isinstance(p, tuple):
					# already a version tuple (of ints)
					normalized.append((0, tuple(p)))
				elif isinstance(p, (int, float)):
					# single numeric -> make a one-element numeric tuple
					if isinstance(p, float) and p.is_integer():
						p = int(p)
					normalized.append((0, (p,)))
				else:
					normalized.append((1, p))

			out = normalized
		else:
			out = [item]

		return out

	def humansorted(self, li):
		"""Sort a list of strings like a human would."""
		if self.sort_algorithm is not None:
			return self.sort_algorithm(li)
		return sorted(li, key=self.custom_sort)

	def scansort(self, li):
		"""Sort a list of os.scandir objects in File Explorer order."""
		if self.sort_algorithm is not None:
			return self.sort_algorithm(li, key=lambda x: x.name)
		return sorted(li, key=lambda x: self.custom_sort(x.name))

	def listsort(self, li):
		"""Sort a list of strings in a more human way."""
		return self.humansorted(li)

	#############################################
	#                FILE HANDLER               #
	#############################################

	def list_directory_json(self, handler: SH, path=None, user: User = None):
		"""
		Helper to produce a directory listing (JSON).
		Return json file of available files and folders
		"""
		if path is None:
			path = handler.translate_path(handler.path)

		try:
			dir_list = self.scansort(os.scandir(path))
		except OSError:
			handler.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None

		if user:
			dir_list = [
				file for file in dir_list
				if user.is_path_allowed(posixpath.join(handler.url_path, file.name))
			]

		dir_dict = []

		for file in dir_list:
			name = file.name
			displayname = linkname = name

			if file.is_dir():
				displayname = name + "/"
				linkname = name + "/"
			elif file.is_symlink():
				displayname = name + "@"

			dir_dict.append([
				urllib.parse.quote(linkname, errors='surrogatepass'),
				html.escape(displayname, quote=False),
			])

		return handler.send_json(dir_dict)

	def list_directory_html(
		self,
		handler: SH,
		path,
		user: User,
		cookie: Union[SimpleCookie, str] = None,
	):
		"""
		Helper to produce a directory listing (absent index.html).

		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().
		"""
		if user.NOPERMISSION or not user.VIEW:
			return handler.send_error(
				HTTPStatus.UNAUTHORIZED,
				"You don't have permission to see file list",
				cookie=cookie,
			)

		try:
			dir_list = self.scansort(os.scandir(path))
		except OSError:
			handler.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None

		if user:
			dir_list = [
				file for file in dir_list
				if user.is_path_allowed(posixpath.join(handler.url_path, file.name))
			]

		r_folders = []  # no js
		r_files = []  # no js

		LIST_STRING = '<li><a class= "%s" href="%s">%s</a></li><hr>'

		for file in dir_list:
			name = file.name

			displayname = linkname = name
			size = 0
			# Append / for directories or @ for symbolic links
			_is_dir_ = True
			if file.is_dir():
				displayname = name + "/"
				linkname = name + "/"
			elif file.is_symlink():
				displayname = name + "@"
			else:
				_is_dir_ = False
				size = fmbytes(file.stat().st_size)
				__, ext = posixpath.splitext(name)
				mime = handler.guess_type(linkname)
				if ext == '.html':
					r_files.append(LIST_STRING % (
						"link",
						urllib.parse.quote(linkname, errors='surrogatepass'),
						html.escape(displayname, quote=False),
					))

				elif mime.startswith(('video/', 'audio/')):
					r_files.append(LIST_STRING % (
						"vid",
						urllib.parse.quote(linkname, errors='surrogatepass'),
						html.escape(displayname, quote=False),
					))

				elif mime.startswith('image/'):
					r_files.append(LIST_STRING % (
						"file",
						urllib.parse.quote(linkname, errors='surrogatepass'),
						html.escape(displayname, quote=False),
					))

				else:
					r_files.append(LIST_STRING % (
						"file",
						urllib.parse.quote(linkname, errors='surrogatepass'),
						html.escape(displayname, quote=False),
					))

			if _is_dir_:
				r_folders.append(LIST_STRING % (
					"",
					urllib.parse.quote(linkname, errors='surrogatepass'),
					html.escape(displayname, quote=False),
				))

		NO_JS_LINKS = "\n".join(r_folders + r_files)

		NO_JS_LINKS = " -->\n" + NO_JS_LINKS + "\n<!-- "  # hack to hide the Template code

		UPLOAD_FORM = ""

		if user.UPLOAD and not user.READ_ONLY:
			UPLOAD_FORM = " -->\n" + pt.upload_form() + "\n<!-- "  # hack to hide the Template code

		return handler.html_main_page(
			user,
			PY_NO_JS_FILE_LIST=NO_JS_LINKS,
			PY_UPLOAD_FORM=UPLOAD_FORM,
			cookie=cookie,
		)

	def list_directory(
		self,
		handler: SH,
		path,
		user: User,
		cookie: Union[SimpleCookie, str] = None,
		escape_html=False,
	):
		"""
		Helper to produce a directory listing (absent index.html).

		Return value is either a file object, or None (indicating an
		error).  In either case, the headers are sent, making the
		interface the same as for send_head().

		path: path to the directory
		user: User object
		cookie: cookie object
		escape_html: whether to escape html or not (default: False, since it will be sent as json)
		"""
		try:
			dir_list = self.scansort(os.scandir(path))
		except OSError:
			handler.send_error(
				HTTPStatus.NOT_FOUND,
				"No permission to list directory")
			return None

		if user:
			dir_list = [
				file for file in dir_list
				if user.is_path_allowed(posixpath.join(handler.url_path, file.name))
			]

		displaypath = handler.get_displaypath(
			url_path=handler.url_path,
			escape_html=escape_html,
		)

		title = get_titles(displaypath)

		r_li = []  # type + file_link
		# f  : File
		# d  : Directory
		# v  : Video
		# a  : Audio
		# i  : Image
		# h  : HTML
		f_li = []  # file_names
		s_li = []  # size list
		rs_li = []  # raw size list (for sorting)
		mt_li = []  # modified time list (for sorting)

		for file in dir_list:
			name = file.name
			displayname = linkname = name

			if escape_html:
				displayname = html.escape(displayname, quote=False)
			size = 0
			raw_size = 0
			mtime = 0
			try:
				stat = file.stat()
				mtime = stat.st_mtime
			except OSError:
				pass

			# Append / for directories or @ for symbolic links
			_is_dir_ = True
			if file.is_dir():
				displayname = name + "/"
				linkname = name + "/"
			elif file.is_symlink():
				displayname = name + "@"
			else:
				_is_dir_ = False

				try:
					stat = file.stat()
					raw_size = stat.st_size
					size = fmbytes(raw_size)
				except OSError:
					raw_size = 0
					size = ""

				__, ext = posixpath.splitext(name)
				mime = handler.guess_type(linkname)
				if ext == '.html':
					r_li.append('h' + urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(displayname)

				elif mime.startswith('video/'):
					r_li.append('v' + urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(displayname)

				elif mime.startswith('audio/'):
					r_li.append('a' + urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(displayname)

				elif mime.startswith('image/'):
					r_li.append('i' + urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(displayname)

				else:
					r_li.append('f' + urllib.parse.quote(linkname, errors='surrogatepass'))
					f_li.append(displayname)
			if _is_dir_:
				r_li.append('d' + urllib.parse.quote(linkname, errors='surrogatepass'))
				f_li.append(displayname)

			s_li.append(size)
			rs_li.append(raw_size)
			mt_li.append(mtime)

		result = {
			"status": "success",
			"file_list": f_li,
			"size_list": s_li,
			"raw_size_list": rs_li,
			"mtime_list": mt_li,
			"type_list": r_li,
			"title": title,
		}

		return result
