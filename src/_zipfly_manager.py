# -*- coding: utf-8 -*-
zf__version__ = '6.0.5'
# v

import io
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

from ._fs_utils import get_dir_size, get_dir_m_time, _get_tree_path_n_size
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


				if os.path.isdir(path[self.filesystem]):
					if os.listdir(path[self.filesystem]):
						continue # not empty
					print("empty")
					# Write empty directory:
					z_info = zipfile.ZipInfo(path[self.arcname] + '/')
					z_info.compress_type = zipfile.ZIP_STORED


					zf.writestr(z_info, b'')

					yield stream.get(), self.ezs
					continue
				z_info = zipfile.ZipInfo.from_file(
					path[self.filesystem],
					path[self.arcname],
					strict_timestamps=False
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
	def __init__(self, zip_allowed, size_limit=-1) -> None:
		self.zip_allowed = zip_allowed
		self.size_limit = size_limit


		self.zip_temp_dir = tempfile.gettempdir() + '/zip_temp/'
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
		os.makedirs(self.zip_temp_dir, exist_ok=True)


	def cleanup(self):
		shutil.rmtree(self.zip_temp_dir, ignore_errors=True)

	def get_id(self, path, size=None):
		"""
		get id of the folder
		if calculating or archiving, return id of the folder
		"""
		if self.calculating(path):
			return self.calculating[path]


		id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))+'_'+ str(time.time())
		id += '0'*(25-len(id))

		self.calculating[path] = id

		source_m_time = get_dir_m_time(path)
		if size is None:
			try:
				fs = _get_tree_path_n_size(path, must_read=True, limit=self.size_limit, path_type="both", add_dirs=True)
			except LimitExceed as e:
				self.calculating.pop(path) # make sure to remove calculating flag (MAJOR BUG)
				raise e

			source_size = sum(i[1] for i in fs)
			fm = [i[0] for i in fs]

			self.calculation_cache[id] = (source_size, fm, source_m_time)
		else:
			source_size = size


		self.calculating.pop(path)

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
		if not self.zip_allowed:
			return err("ZIP FUNTION DISABLED")




		# run zipfly
		self.zip_in_progress[zid] = 0

		if not self.calculation_cache(zid):
			try:
				fs = _get_tree_path_n_size(path, must_read=True, path_type="both", limit=self.size_limit, add_dirs=True)
			except LimitExceed as e:
				return err("DIRECTORY SIZE LIMIT EXCEED")
			source_size = sum(i[1] for i in fs)
			fm = [i[0] for i in fs]
			source_m_time = get_dir_m_time(path)

		else:
			source_size, fm, source_m_time = self.calculation_cache[zid]
			self.calculation_cache.pop(zid)

		if len(fm)==0:
			return err("FOLDER HAS NO FILES")


		dir_name = os.path.basename(path)



		zfile_name = os.path.join(self.zip_temp_dir, "{dir_name}({zid})".format(dir_name=dir_name, zid=zid) + ".zip")

		self.init_dir()

		paths = []
		for xx in fm:
			try:
				i, j = xx
			except:
				print(xx)
				traceback.print_exc()
				continue
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


if __name__ == "__main__":
	paths = [
		{
			'fs': 'test(hahah)'
		},
	]

	zfly = ZipFly(paths = paths)

	generator = zfly.generator()
	print (generator)
	# <generator object ZipFly.generator at 0x7f74d52bcc50>


	with open("large.zip", "wb") as f:
		for i in generator:
			f.write(i[0])