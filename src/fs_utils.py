"""
fs_utils.py
---------------
File System Utilities

* Why using Queue and other stuffs instead of os.walk()?
	- os.walk() is slow, and accessing its stat is slow too.
* Why making functions with almost same functionality?
	-  imagine a function just returns all paths, another returns sizes. Using both of them together is using a bit inefficient.

* os.scandir() also caches the stat of the files, so it's faster than os.walk().

# GOT FASTER SOLUTIONS?
> Make a pull request or open an issue here: https://github.com/RaSan147/pyrobox
> Thanks for your help!
"""

import os
from queue import Queue
import re
import urllib.parse


from .exceptions import LimitExceed




def get_stat(path):
	"""
	Get the stat of a file.

	path: path to the file

	* can act as check_access(path) for files
	"""
	try:
		return os.stat(path)
	except Exception:
		return False
	

def check_access(path):
	"""
	Check if the user has access to the file.

	path: path to the file
	"""
	if not os.path.exists(path):
		return False
	
	if os.path.isfile(path):
		try:
			with open(path, "rb") as f:
				f.read(1)

				return True
		except Exception:
			return False
	else:
		# if folder, check if it's stat is accessible
		return bool(get_stat(path))



def walk_dir(path, yield_dir=False):
	"""
	Iterate through a directory and its subdirectories
	and `yield` the filePath object of each Files and Folders*.

	path: path to the directory
	yield_dir (bool): if True yields directories too (default: False)
	"""

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
			
			if yield_dir or not is_dir:
				yield entry

		dir.close()


# TODO: can be used in search feature
def get_tree(path, include_dir=True):
	"""
	returns a list of files in a directory and its subdirectories.
	[ [full path, relative path], ... ]

	path: path to the directory
	include_dir (bool): if True returns full path, else relative path
	"""
	home = path
	tree = []

	# Q = Queue()
	# Q.put(path)
	# while not Q.empty():
	# 	path = Q.get()

	# 	try:
	# 		dir = os.scandir(path)
	# 	except OSError:
	# 		continue
	# 	for entry in dir:
	# 		try:
	# 			is_dir = entry.is_dir(follow_symlinks=False)
	# 		except OSError as error:
	# 			continue
	# 		if is_dir:
	# 			Q.put(entry.path)

	# 		if include_dir or not is_dir:
	# 			tree.append([entry.path, entry.path.replace(home, "", 1)])

	# 	dir.close()

	for entry in walk_dir(path, yield_dir=include_dir):
		tree.append([entry.path, entry.path.replace(home, "", 1)])

	return tree



def _get_tree_count(path):
	count = 0

	# Q = Queue()
	# Q.put(path)
	# while not Q.empty():
	# 	path = Q.get()

	# 	try:
	# 		dir = os.scandir(path)
	# 	except OSError:
	# 		continue
	# 	for entry in dir:
	# 		try:
	# 			is_dir = entry.is_dir(follow_symlinks=False)
	# 		except OSError as error:
	# 			continue
	# 		if is_dir:
	# 			Q.put(entry.path)
	# 		else:
	# 			count += 1

	# 	dir.close()

	for entry in walk_dir(path):
		count += 1

	return count


def get_file_count(path):
	"""
	Get the number of files in a directory.
	"""
	return _get_tree_count(path)


def _get_tree_size(path, limit=None, must_read=False):
	"""
	returns the size of a directory and its subdirectories.
	
	path: path to the directory
	limit (int): if not None, raises LimitExceed if the size is greater than limit
	must_read (bool): if True, reads the first byte of each file to check if it's accessible
	"""
	r=[] #if return_list
	total = 0
	start_path = path

	for entry in walk_dir(path):
		try:
			total += entry.stat(follow_symlinks=False).st_size
		except OSError:
			continue

		if limit and total>limit:
			raise LimitExceed

		if must_read:
			try:
				with open(entry.path, "rb") as f:
					f.read(1)
			except Exception:
				continue

	return total

def _get_tree_path_n_size(path, limit=-1, must_read=False, path_type="full"):
	"""
	returns a list of files[size, path] in a directory and its subdirectories.
		[ [`path`, size], ... ]
		> path: `path_string` | `tuple(full_path, relative_path)`

	path: path to the directory
	path_type (str): "full" or "relative" or "both"
	"""
	r=[] #if return_list
	total = 0
	start_path = path

	for entry in walk_dir(path):
		try:
			size = entry.stat(follow_symlinks=False).st_size
		except OSError:
			continue
		total += size

		if limit>0 and total>limit:
			raise LimitExceed

		if must_read and not check_access(entry.path):
			continue


		if path_type == "full":
			r.append([entry.path, size])
		elif path_type == "relative":
			r.append([entry.path.replace(start_path, "", 1), size])
		elif path_type == "both":
			r.append([(entry.path, entry.path.replace(start_path, "", 1)), size])

	return r


def get_dir_size(start_path = '.', limit=None, must_read=False):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns `-1`
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	both (bool): if True returns a tuple of (total folder size, (full path, relative path))
	must_read (bool): if True only counts files that can be read
	"""

	return _get_tree_size(start_path, limit, must_read)


def _get_tree_count_n_size(path):
	"""
	Get the size of a directory and all its subdirectories.
	returns a tuple of (`total file count`, `total folder size`)

	path: path to the directory
	"""
	total = 0
	count = 0
	
	for entry in walk_dir(path):
		try:
			total += entry.stat(follow_symlinks=False).st_size
		except OSError:
			continue

		count += 1

	return count, total

def get_tree_count_n_size(start_path):
	"""
	Get the size of a directory and all its subdirectories.
	returns a tuple of (`total file count`, `total folder size`)

	path: path to the directory
	"""

	return _get_tree_count_n_size(start_path)


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
