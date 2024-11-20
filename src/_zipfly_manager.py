# -*- coding: utf-8 -*-
zf__version__ = '6.0.5'
# v

import io
import subprocess
import zipfile
import tempfile
import os
import shutil
import atexit
import random
import string
import time
import traceback
import threading
from collections import OrderedDict
import re



from ._fs_utils import get_dir_m_time, _get_tree_path_n_size, humanbytes
from ._exceptions import LimitExceed



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
	"""
	A class to handle the creation of zip archives using the ZipFly library.

	Attributes:
		mode (str): Mode for the zip file, default is 'w'.
		paths (list): List of file paths to include in the zip archive.
		chunksize (int): Size of chunks to read from files.
		compression (int): Compression method to use.
		allowZip64 (bool): Whether to allow ZIP64 extensions.
		compresslevel (int): Compression level.
		storesize (int): Size of all files in paths without compression.
		encode (str): Encoding to use for file names.
		ezs (int): Empty zip size in bytes.
	"""

	def __init__(self,
				 mode='w',
				 paths=None,
				 chunksize=0x8000,
				 compression=zipfile.ZIP_STORED,
				 allowZip64=True,
				 compresslevel=None,
				 storesize=0,
				 encode='utf-8'):
		"""
		Initializes the ZipFly class with the given parameters.

		Args:
			mode (str): Mode for the zip file, default is 'w'.
			paths (list): List of file paths to include in the zip archive.
			chunksize (int): Size of chunks to read from files.
			compression (int): Compression method to use.
			allowZip64 (bool): Whether to allow ZIP64 extensions.
			compresslevel (int): Compression level.
			storesize (int): Size of all files in paths without compression.
			encode (str): Encoding to use for file names.
		"""
		if paths is None:
			paths = []

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
		"""
		Generator to create a zip archive and yield chunks of data.

		Yields:
			tuple: A tuple containing the chunk of data and its size.
		"""
		stream = ZipflyStream()

		with zipfile.ZipFile(
				stream,
				mode=self.mode,
				compression=self.compression,
				allowZip64=self.allowZip64) as zf:

			for path in self.paths:
				if self.arcname not in path:
					path[self.arcname] = path[self.filesystem]

				if os.path.isdir(path[self.filesystem]):
					if os.listdir(path[self.filesystem]):
						continue  # not empty

					# Write empty directory:
					if path[self.arcname].endswith('\\'):
						path[self.arcname] = path[self.arcname][:-1] + '/'

					if not path[self.arcname].endswith('/'):
						path[self.arcname] += '/'

					if path[self.arcname].startswith('/') or path[self.arcname].startswith('\\'):
						path[self.arcname] = path[self.arcname][1:]

					z_info = zipfile.ZipInfo(path[self.arcname])
					z_info.compress_type = zipfile.ZIP_STORED

					zf.writestr(z_info, b'')
					yield stream.get(), self.ezs
					continue

				z_info = zipfile.ZipInfo.from_file(
					path[self.filesystem],
					path[self.arcname],
					strict_timestamps=False
				)

				with open(path[self.filesystem], 'rb') as e:
					with zf.open(z_info, mode=self.mode) as d:
						for chunk in iter(lambda: e.read(self.chunksize), b''):
							d.write(chunk)
							yield stream.get(), len(chunk)

		_chunk = stream.get()
		yield _chunk, len(_chunk)
		self._buffer_size = stream.size()

		# Flush and close this stream.
		stream.close()

	def get_size(self):
		"""
		Get the size of the buffer.

		Returns:
			int: Size of the buffer.
		"""
		return self._buffer_size




def _scan_for_7z():
	"""
	Scans for the presence of the 7-Zip executable in common installation paths
	across different operating systems (Windows, macOS, Linux) and returns the
	first valid path found.
	The function checks the following locations:
	- Standard installation directories for Windows, macOS, and Linux.
	- Snap or Flatpak installation directories.
	- The current directory where the script is located.
	- If `7z` is available in the system PATH.
	Returns:
		str: The path to the 7-Zip executable if found, otherwise None.
	"""
	possible_paths = [
		# Windows paths
		r"C:\Program Files\7-Zip\7z.exe",
		r"C:\Program Files (x86)\7-Zip\7z.exe",

		# macOS paths
		"/usr/local/bin/7z",
		"/opt/local/bin/7z",

		# Linux paths
		"/usr/bin/7z",
		"/usr/local/bin/7z",

		# Snap or Flatpak installations
		"/snap/bin/7z",

		# Additional locations
		"7z",  # Checks if `7z` is available in PATH

		# If the installation copy is in the current directory
		os.path.join(os.path.dirname(__file__), "7z.exe"),
		# or the 7-Zip folder is in the current directory
		os.path.join(os.path.dirname(__file__), "7-Zip/7z.exe"),

		# if its in non-windows system
		os.path.join(os.path.dirname(__file__), "7z"),
		os.path.join(os.path.dirname(__file__), "7-Zip/7z"),
	]

	for path in possible_paths:
		if os.path.isfile(path) or (os.name != 'nt' and os.access(path, os.X_OK)):
			return path
	return None

class zip7z:
	"""
	A class to handle zipping files and folders using 7-Zip.

	Attributes:
		running_process (subprocess.Popen): The currently running subprocess for zipping.
		_7z_path (str): Path to the 7-Zip executable.
		progress (str): Progress percentage of the current zipping process.

	Methods:
		__init__():
			Initializes the zip7z class, scans for 7-Zip, and sets up necessary attributes.
		make_zip_with_7z_generator(file_or_folder, zip_name=None):
			Generates a zip archive using 7-Zip.
		stop():
			Stops the currently running zipping process.
		make_zip_with_7z(file_or_folder, zip_name=None, show_progress=True):
			Creates a zip archive using 7-Zip and optionally shows progress.
			Args:
				file_or_folder (str): The file or folder to zip.
				zip_name (str, optional): The name of the zip file. Defaults to None.
				show_progress (bool, optional): Whether to print progress to the console. Defaults to True.
	"""
	def __init__(self) -> None:
		self.running_process = None
		self._7z_path = _scan_for_7z()
		if not self._7z_path:
			raise NotImplementedError("7-Zip not found. Please install 7-Zip and try again.")

		self.progress = None

	def make_zip_with_7z_generator(self, file_or_folder, zip_name=None, zip_path=None):
		"""
		Generator to create a zip archive using 7-Zip and yield progress.

		Args:
			file_or_folder (str): Path to the file or folder to be archived.
			zip_name (str, optional): Name of the output zip file (with Extension). Defaults to the name of the file_or_folder
			zip_path (str, optional): Path to save the zip file. Defaults to the same directory as the file_or_folder.

		Yields:
			str: Progress percentage as a string. i.e. "10%"
		"""
		if self.running_process:
			raise ChildProcessError("Another process is already running. Please wait for it to finish.")

		if not os.path.exists(file_or_folder):
			raise FileNotFoundError(f"Folder not found: {file_or_folder}")

		zip_name = zip_name or os.path.basename(file_or_folder) + ".zip"
		zip_path = zip_path or os.path.dirname(file_or_folder)
		zip_file = os.path.join(zip_path, zip_name)

		# Delete the zip file if it exists
		if os.path.exists(zip_file):
			os.remove(zip_file)

		if not self._7z_path:
			raise NotImplementedError("7-Zip not found. Please install 7-Zip and try again.")

		cmd = [
			self._7z_path,
			"a",
			"-tzip",
			"-mx=0",
			"-bsp1",
			zip_file,
			f"{file_or_folder}/*" if os.path.isdir(file_or_folder) else file_or_folder
		]

		def process_thread():
			self.running_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


		t = threading.Thread(target=process_thread)
		t.start()

		while self.running_process:
			if self.running_process.stdout is None:
				break
			line = self.running_process.stdout.readline()
			prog = re.search(r"\d{1,3}%", line)
			if prog:
				self.progress = prog.group().strip()
				yield self.progress

			if not line and self.running_process.poll() is not None:
				break

		t.join()

	def stop(self):
		if self.running_process:
			self.running_process.kill()
			self.running_process = None

	def make_zip_with_7z(self, file_or_folder, zip_name=None, show_progress=True):
		for prog in self.make_zip_with_7z_generator(file_or_folder, zip_name):
			if show_progress:
				print("PROGRESS: ", prog)





class Callable_dict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __call__(self, *key):
		return all([i in self for i in key])


class FixSizeOrderedDict(OrderedDict, Callable_dict):
	def __init__(self, *args, max=0, **kwargs):
		self._max = max
		super().__init__(*args, **kwargs)

	def __setitem__(self, key, value):
		OrderedDict.__setitem__(self, key, value)
		if self._max > 0:
			if len(self) > self._max:
				self.popitem(False)



class ZIP_Manager:
	"""
	A class to manage the creation of zip archives using either ZipFly or 7-Zip.

	Attributes:
		zip_allowed (bool): Flag to allow or disallow zipping.
		size_limit (int): Maximum allowed size for the zip archive.
		zip_temp_dir (str): Temporary directory for storing zip files.
		zip_ids (Callable_dict): Dictionary to store zip IDs.
		zip_path_ids (Callable_dict): Dictionary to store path IDs.
		zip_in_progress (Callable_dict): Dictionary to track progress of zipping.
		zip_id_status (Callable_dict): Dictionary to store status of zip IDs.
		assigend_zid (Callable_dict): Dictionary to store assigned zip IDs.
		calculating (Callable_dict): Dictionary to track ongoing calculations.
		calculation_cache (FixSizeOrderedDict): Cache for storing calculation results.
	"""

	def __init__(self, zip_allowed, size_limit=-1, zip_temp_dir=None):
		self.zip_allowed = zip_allowed
		self.size_limit = size_limit

		self.zip_temp_dir = zip_temp_dir if zip_temp_dir else tempfile.TemporaryDirectory().name + '/zip_temp/'
		self.zip_ids = Callable_dict()
		self.zip_path_ids = Callable_dict()
		self.zip_in_progress = Callable_dict()
		self.zip_id_status = Callable_dict()

		self.assigend_zid = Callable_dict()
		self.calculating = Callable_dict()
		self.calculation_cache = FixSizeOrderedDict(max=100)

		self.cleanup()
		atexit.register(self.cleanup)

		self.init_dir()

	def init_dir(self):
		"""Initialize the temporary directory for zip files."""
		os.makedirs(self.zip_temp_dir, exist_ok=True)

	def cleanup(self):
		"""Clean up the temporary directory."""
		shutil.rmtree(self.zip_temp_dir, ignore_errors=True)

	def get_id(self, path, size=None):
		"""
		Get the ID of the folder. If calculating or archiving, return the ID of the folder.

		Args:
			path (str): Path to the folder.
			size (int, optional): Size of the folder. Defaults to None.

		Returns:
			str: ID of the folder.
		"""
		if self.calculating(path):
			return self.calculating[path]

		id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)) + '_' + str(time.time())
		id += '0' * (25 - len(id))

		self.calculating[path] = id

		source_m_time = get_dir_m_time(path)
		if size is None:
			try:
				fs = _get_tree_path_n_size(path, must_read=True, limit=self.size_limit, path_type="both", add_dirs=True)
			except LimitExceed as e:
				self.calculating.pop(path)  # make sure to remove calculating flag (MAJOR BUG)
				raise e

			source_size = sum(i[1] for i in fs)
			fm = [i[0] for i in fs]

			self.calculation_cache[id] = (source_size, fm, source_m_time)
		else:
			source_size = size

		self.calculating.pop(path)

		exist = 1

		prev_zid, prev_size, prev_m_time = 0, 0, 0
		if self.zip_path_ids(path):
			prev_zid, prev_size, prev_m_time = self.zip_path_ids[path]
		elif self.assigend_zid(path):
			prev_zid, prev_size, prev_m_time = self.assigend_zid[path]
		else:
			exist = 0

		if exist and prev_m_time == source_m_time and prev_size == source_size:
			return prev_zid

		self.assigend_zid[path] = (id, source_size, source_m_time)
		return id

	def zipfly_handler(self, paths, zid, source_size, zfile_name, err):
		"""
		Handles the creation of a zip archive using the ZipFly library.

		Args:
			paths (list): List of file paths to include in the zip archive.
			zid (str): Identifier for the zip operation.
			source_size (int): Total size of the source files to be archived.
			zfile_name (str): Name of the output zip file.
			err (function): Error handling function to be called in case of an exception.

		Returns:
			None
		"""
		zfly = ZipFly(paths=paths, chunksize=0x80000)

		archived_size = 0
		self.zip_id_status[zid] = "ARCHIVING"

		try:
			with open(zfile_name, "wb") as zf:
				for chunk, c_size in zfly.generator():
					zf.write(chunk)
					archived_size += c_size
					if source_size == 0:
						source_size += 1  # prevent division by 0
					self.zip_in_progress[zid] = (archived_size / source_size) * 100
		except Exception as e:
			traceback.print_exc()
			return err(e)

	def zip7z_handler(self, path, zid, source_size, zfile_name, err):
		"""
		Handles the creation of a zip archive using the 7-Zip library.

		Args:
			path (str): Path to the folder to be archived.
			zid (str): Identifier for the zip operation.
			source_size (int): Total size of the source files to be archived.
			zfile_name (str): Name of the output zip file.
			err (function): Error handling function to be called in case of an exception.

		Returns:
			None
		"""
		zip7z_obj = zip7z()

		self.zip_id_status[zid] = "ARCHIVING"

		try:
			for progress in zip7z_obj.make_zip_with_7z_generator(path, zfile_name):
				print([progress])
				self.zip_in_progress[zid] = int(progress[:-1])
		except Exception as e:
			traceback.print_exc()
			return err(e)

		self.zip_in_progress[zid] = 100

	def archive(self, path, zid, size=None):
		"""
		Archive the folder.

		Args:
			path (str): Path to archive.
			zid (str): ID of the folder.
			size (int, optional): Size of the folder. Defaults to None.

		Returns:
			str: ID of the zip operation.
		"""
		def err(msg):
			self.zip_in_progress.pop(zid, None)
			self.assigend_zid.pop(path, None)
			self.zip_id_status[zid] = "ERROR: " + msg
			return False

		if not self.zip_allowed:
			return err("ZIP FUNCTION DISABLED")

		# Run zipfly or 7z handler
		self.zip_in_progress[zid] = 0

		if not self.calculation_cache(zid):
			try:
				fs = _get_tree_path_n_size(path, must_read=True, path_type="both", limit=self.size_limit, add_dirs=True)
			except LimitExceed as e:
				return err(f"DIRECTORY SIZE LIMIT EXCEED [CURRENT LIMIT: {humanbytes(self.size_limit)}]")
			source_size = sum(i[1] for i in fs)
			fm = [i[0] for i in fs]
			source_m_time = get_dir_m_time(path)
		else:
			source_size, fm, source_m_time = self.calculation_cache[zid]
			self.calculation_cache.pop(zid)

		if len(fm) == 0:
			return err("FOLDER HAS NO FILES")

		dir_name = os.path.basename(path)
		zfile_name = os.path.join(self.zip_temp_dir, f"{dir_name}({zid}).zip")

		self.init_dir()

		paths = [{"fs": i, "n": j} for i, j in fm]

		try:
			self.zip7z_handler(path, zid, source_size, zfile_name, err)
		except NotImplementedError:
			self.zipfly_handler(paths, zid, source_size, zfile_name, err)
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
		"""
		Create a thread to archive the folder.

		Args:
			path (str): Path to archive.
			zid (str): ID of the folder.
			size (int, optional): Size of the folder. Defaults to None.

		Returns:
			threading.Thread: Thread object for the archive operation.
		"""
		return threading.Thread(target=self.archive, args=(path, zid, size))


if __name__ == "__main__":
	paths = [
		{
			'fs': 'te-st/'
		},
	]

	zfly = ZipFly(paths = paths)

	generator = zfly.generator()
	print (generator)
	# <generator object ZipFly.generator at 0x7f74d52bcc50>


	with open("large.zip", "wb") as f:
		for i in generator:
			f.write(i[0])