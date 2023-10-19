import os
import posixpath
import importlib.util
from http import HTTPStatus
import urllib.parse
import html



from pyroboxCore import config, logger
from pyrobox_ServerHost import ServerHost as SH

from user_mgmt import User
import _page_templates as pt

from _fs_utils import get_titles, dir_navigator, fmbytes




def check_installed(pkg):
	return bool(importlib.util.find_spec(pkg))



try:
	import natsort
except Exception:
	config.disabled_func["natsort"] = True
	logger.warning("natsort module not found, natsort function disabled")

def humansorted(li):
	"""
	Sort a list of strings like a human would
	"""

	if not config.disabled_func["natsort"]:
		return natsort.humansorted(li)

	return sorted(li, key=lambda x: x.lower())

def scansort(li):
	"""
	Sort a list of os.scandir objects in File Explorer order
	"""

	if not config.disabled_func["natsort"]:
		return natsort.humansorted(li, key=lambda x:x.name)

	return sorted(li, key=lambda x: x.name.lower())

def listsort(li):
	"""
	Sort a list of strings in More Human way
	"""

	return humansorted(li)




#############################################
#                FILE HANDLER               #
#############################################



def list_directory_json(self:SH, path=None):
	"""
	Helper to produce a directory listing (JSON).
	Return json file of available files and folders
	"""
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

	return self.send_json(dir_dict)


def list_directory_html(self:SH, path, user:User):
	"""
	Helper to produce a directory listing (absent index.html).

	Return value is either a file object, or None (indicating an
	error).  In either case, the headers are sent, making the
	interface the same as for send_head().

	"""
	if user.NOPERMISSION or user.VIEW == False:
		return self.send_text("You don't have permission to see file list", 403)
	

	try:
		dir_list = scansort(os.scandir(path))
	except OSError:
		self.send_error(
			HTTPStatus.NOT_FOUND,
			"No permission to list directory")
		return None
	
	
	r_folders = [] # no js
	r_files = [] # no js
	
	
	LIST_STRING = '<li><a class= "%s" href="%s">%s</a></li><hr>'
	
	for file in dir_list:
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
				
			elif self.guess_type(linkname).startswith('video/'):
				r_files.append(LIST_STRING % ("vid", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

			elif self.guess_type(linkname).startswith('image/'):
				r_files.append(LIST_STRING % ("file", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

			else:
				r_files.append(LIST_STRING % ("file", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))

		if _is_dir_:
			r_folders.append(LIST_STRING % ("", urllib.parse.quote(linkname,
									errors='surrogatepass'),
									html.escape(displayname, quote=False)))


	NO_JS_LINKS = "\n".join(r_folders +	r_files)

	NO_JS_LINKS = " -->\n" + NO_JS_LINKS + "\n<!-- " # hack to hide the Template code

	UPLOAD_FORM = ""

	if user.UPLOAD and not user.READ_ONLY:
		UPLOAD_FORM = " -->\n" + pt.upload_form() + "\n<!-- " # hack to hide the Template code

	return self.html_main_page(user, PY_NO_JS_FILE_LIST=NO_JS_LINKS, PY_UPLOAD_FORM=UPLOAD_FORM)





def list_directory(self:SH, path, user:User):
	"""
	Helper to produce a directory listing (absent index.html).

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


	r.append(pt.directory_explorer_header().safe_substitute(PY_PAGE_TITLE=title,
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



	NO_JS_LINKS = "\n".join(r_folders +	r_files)

	NO_JS_LINKS = " -->\n" + NO_JS_LINKS + "\n<!-- " # hack to hide the Template code



	r.append("""</ul>
				</div>
				<!-- END CONTENT LIST (NO JS) -->
				<div id="js-content_list" class="jsonly"></div>
			""")

	r.append(pt.file_list_script().safe_substitute(PY_LINK_LIST=str(r_li),
										PY_FILE_LIST=str(f_li),
										PY_FILE_SIZE =str(s_li)))

	#if not (cli_args.no_upload or cli_args.read_only or cli_args.view_only):
	if user.UPLOAD and not user.READ_ONLY:
		r.append(pt.upload_form())
		pass



	encoded = '\n'.join(r).encode("utf-8", 'surrogateescape')

	return self.send_txt(encoded)

