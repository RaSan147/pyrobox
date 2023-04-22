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