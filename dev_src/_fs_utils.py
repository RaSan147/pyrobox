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

from io import BufferedWriter
import os
from queue import Queue
import re
import time
import traceback
import urllib.parse
from UX_Tools import os_scan_walk_gen, xpath

from _exceptions import LimitExceed

if __name__ == "__main__":
	from pyrobox_ServerHost import ServerHost



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



def walk_dir(*path, yield_dir=False):
	"""
	Iterate through a directory and its subdirectories
	and `yield` the filePath object of each Files and Folders*.

	path: path to the directory
	yield_dir (bool): if True yields directories too (default: False)
	"""

	for f in os_scan_walk_gen(*path, allow_dir=yield_dir):
		yield f


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

	for entry in walk_dir(path, yield_dir=include_dir):
		tree.append([entry.path, entry.path.replace(home, "", 1)])

	return tree



def _get_tree_count(path):
	count = 0

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

		if must_read and not check_access(entry.path):
			continue

	return total

def _get_tree_path_n_size(path, limit=-1, must_read=False, path_type="full", add_dirs=False):
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

	for entry in walk_dir(path, yield_dir=add_dirs):
		size = 0
		if not entry.is_dir():
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


def humanbytes(B: int):
	'Return the given bytes as a human friendly KB, MB, GB, or TB string'
	B = int(B)
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

def reverse_humanbytes(human_str:str):
	"""
	Converts human readable size to bytes
	"""
	human_str = human_str.strip().lower()

	if human_str.endswith('bytes'):
		return int(human_str[:-5].strip())
	if human_str.endswith('byte'):
		return int(human_str[:-4].strip())

	if human_str.endswith('b'):
		human_str = human_str[:-1].strip()

	if human_str.endswith('k'):
		return int(float(human_str[:-1].strip()) * 1024)

	if human_str.endswith('m'):
		return int(float(human_str[:-1].strip()) * 1024**2)

	if human_str.endswith('g'):
		return int(float(human_str[:-1].strip()) * 1024**3)

	if human_str.endswith('t'):
		return int(float(human_str[:-1].strip()) * 1024**4)

	return int(human_str)


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
		return 'Viewing 🏠 HOME'
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
		# urls.append(urls[i-1] + urllib.parse.quote(dir, errors='surrogatepass' )+ '/' if not dir.endswith('/') else "")
		urls.append(urls[i-1] + dir + '/' if not dir.endswith('/') else "")
		names.append(dir)

	for i in range(len(names)):
		tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>"
		r.append(tag)

	return '<span class="dir_arrow">&#10151;</span>'.join(r)





def loc(*path, _os_name='Linux'):  # fc=0602 v
	"""to fix dir problem based on os

	args:
	-----
		x: directory
		os_name: Os name *Linux"""

	if _os_name == 'Windows':
		return xpath(*path, win=True)

	return xpath(*path, posix=True)



def writer(fname, mode, data, direc="", encoding='utf-8'):  # fc=0608 v
	"""Writing on a file

	why this monster?
	> to avoid race condition, folder not found etc

	args:
	-----
		fname: filename
		mode: write mode (w, wb, a, ab)
		data: data to write
		direc: directory of the file, empty for current dir *None
		func_code: (str) code of the running func *empty string
		encoding: if encoding needs to be specified (only str, not binary data) *utf-8
		timeout: how long to wait until free, 0 for unlimited, -1 for immediate or crash"""

	def write(location):
		if 'b' not in mode:
			with open(location, mode, encoding=encoding) as file:
				file.write(data)
		else:
			with open(location, mode) as file:
				file.write(data)

	_direc, fname = os.path.split(fname)
	direc = os.path.join(direc, _direc)

	if any(i in fname for i in ('|:*"><?')) or any(i in direc for i in ('|:*"><?')):
		# these characters are forbidden to use in file or folder Names
		raise ValueError("Invalid file or folder name")
	direc = loc(direc, 'Linux')

	# directory and file names are auto stripped by OS
	# or else shitty problems occurs

	direc = direc.strip()

	fname = fname.strip()

	location = xpath(direc, fname)

	"""
	if any(i in location for i in ('\\|:*"><?')):
		location = Datasys.trans_str(location, {'\\|:*><?': '-', '"': "'"})
	"""


	# creates the directory, then write the file
	try:
		os.makedirs(direc, exist_ok=True)
	except Exception as e:
		if e.__class__.__name__ == "PermissionError":
			_temp = ''
			_temp2 = direc.split('/')
			_temp3 = 0
			for _temp3 in range(len(_temp2)):
				_temp += _temp2[_temp3] + '/'
				if not os.path.isdir(_temp):
					break
			raise PermissionError(f"Failed to make directory on {_temp}") from e
		raise e


	write(location)


class UploadHandler:
	def __init__(self, uid):
		self.serial_io = Queue()
		# format [[temp_file_obj, mode, data?], ...]
		# if mode is 's' then data is [os_f_path, overwrite]
		# if mode is 'w' then data is the data to write
		self.active = True
		self.waited = 0
		self.done = False
		self.uid = uid
		self.error = False
		self.nap_time = 1

		self.stop_on_error = True

	def upload(self, temp_file, mode, data=None):
		"""
		* format `[[temp_file_obj, mode, data?], ...]`
		* if `mode` is `s` then data is [os_f_path, overwrite]
		* if `mode` is `w` then binary data is the data to write
		"""
		if not self.done:
			self.serial_io.put([temp_file, mode, data])

	def start(self, server):
		try:
			self._start(server)
		except Exception as e:
			traceback.print_exc()
			server.log_error("Upload Failed")
			self.kill()

	def err(self, error_msg):
		self.error = error_msg
		if self.stop_on_error:
			self.kill()

	def sleep(self):
		time.sleep(self.nap_time)



	def _start(self, server:"ServerHost"):
		while self.active or not self.serial_io.empty():
			if not self.serial_io.empty():
				self.waited = 0
				req_data = self.serial_io.get()
				file:BufferedWriter = req_data[0]
				mode = req_data[1]
				data = req_data[2]
				if mode == "w": # write
					file.write(data)
				if mode == "s": #save
					temp_fn = file.name
					if not file.closed:
						file.close()
						os_f_path, overwrite = data
						os_fn = os.path.basename(os_f_path)

						name, ext = os.path.splitext(os_f_path)
						n = 1
						while (not overwrite) and os.path.isfile(os_f_path):
							os_f_path = f"{name}({n}){ext}"
							n += 1


						try:
							if os.path.exists(os_f_path): # if overwrite is disabled then the previous part will handle the new filename.
								os.remove(os_f_path)
							os.rename(temp_fn, os_f_path)
						except Exception as e:
							server.log_error(f'Failed to replace {temp_fn} with {os_f_path} by {self.uid}')
							server.log_error(traceback.format_exc())
							self.err(f"Failed to upload {os_fn}")

							break

			else:
				self.waited += 1
				self.sleep()
				if self.waited > 100:
					self.active = False
					break

	def kill(self):
		self.active = False
		self.done = True

		for f in tuple(self.serial_io.queue):
			name = f[0].name
			if not f[0].closed:
				f[0].close()

			if os.path.exists(name):
				os.remove(name)

		self.serial_io.queue.clear()



