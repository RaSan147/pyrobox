#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# REQUIREMENTS: msgpack, wcwidth, tabulate2
# pip install msgpack tabulate2


# THIS IS A HYBRID OF PICKLEDB AND MSGPACK and MY OWN CODES

# I'll JUST KEEP THE PICKLEDB LICENSE HERE
# Copyright 2019 Harrison Erd
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import io
import os
import signal
import atexit
import shutil
from collections.abc import Iterable
import time
import random
from tempfile import NamedTemporaryFile
from threading import Thread
import csv
import copy as datacopy

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

import traceback
from typing import Any, Generator, List, Union

try:
	from tabulate2 import tabulate # pip install tabulate2
	TABLE = True
except ImportError:
	logger.warning("tabulate not found, install it using `pip install tabulate2`\n * Printing table will not be in tabular format")
	# raise ImportError("tabulate not found, install it using `pip install tabulate2`")
	TABLE = False

try:
	import msgpack # pip install msgpack
	SAVE_LOAD = True
except ImportError:
	logger.warning("msgpack not found, install it using `pip install msgpack`\n * Save and Load will not work")
	SAVE_LOAD = False
	# raise ImportError("msgpack not found, install it using `pip install msgpack`")

__version__ = "0.1.0"

def load(location, auto_dump, sig=True):
	"""
	Return a pickledb object. location is the path to the json file.
	"""
	return PickleDB(location, auto_dump, sig)

class PickleDB(object):

	key_string_error = TypeError('Key/name must be a string!')

	def __init__(self, location="", auto_dump=True, sig=True):
		"""Creates a database object and loads the data from the location path.
		If the file does not exist it will be created on the first update.
		"""
		self.db = {}

		self.in_memory = False
		self.location = ""
		if location:
			self.load(location, auto_dump)
		else:
			self.in_memory = True

		self.dthread = None

		self.m_time = 0

		self.auto_dump = auto_dump

		self.sig = sig
		if sig:
			self.set_sigterm_handler()

	def __getitem__(self, item):
		"""
		Syntax sugar for get()
		"""
		return self.get(item, raiseErr=True)

	def __setitem__(self, key, value):
		"""
		Syntax sugar for set()
		"""
		return self.set(key, value)

	def __delitem__(self, key):
		"""
		Syntax sugar for rem()
		"""
		return self.rem(key)

	def __bool__(self):
		return bool(self.db)

	def __contains__(self, key):
		return key in self.db


	def __len__(self):
		"""Get a total number of keys, lists, and dicts inside the db"""
		return len(self.db)


	def set_sigterm_handler(self):
		"""
		Assigns sigterm_handler for graceful shutdown during dump()
		"""
		def sigterm_handler(*args, **kwargs):
			if self.dthread is not None:
				self.dthread.join()
		try:
			signal.signal(signal.SIGTERM, sigterm_handler)
			# ValueError: signal only works in main thread of the main interpreter
		except:
			atexit.register(sigterm_handler)

	def unlink(self):
		"""
		Unlink the db file (start using in-memory db)
		"""
		if self.in_memory:
			return
		self.location = ""
		self.in_memory = True
		return

	def delete_file(self):
		"""
		Delete the db file from the disk (uses in-memory db)
		"""
		if self.in_memory:
			return
		os.remove(self.location)
		self.location = ""
		self.in_memory = True
		return

	def rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""
		if self.in_memory or not rescan:
			return
		if os.path.exists(self.location):
			m_time = os.stat(self.location).st_mtime
			if m_time > self.m_time:
				self._loaddb()
				self.m_time = m_time

	def new(self):
		self.db = {}

	def _fix_location(self, location):
		location = os.path.expanduser(location)
		return location

	def set_location(self, location):
		self.location = self._fix_location(location)
		self.in_memory = False

	def load(self, location, auto_dump):
		"""
		Loads, reloads or Changes the path to the db file
		"""
		self.set_location(location)

		self.auto_dump = auto_dump
		if os.path.exists(location):
			self._loaddb()
		else:
			self.new()
		return True

	def _dump(self):
		"""
		Dump to a temporary file, and then move to the actual location
		"""
		if self.in_memory:
			return

		logger.info("--dumping--")
		with NamedTemporaryFile(mode='wb', delete=False) as f:
			try:
				msgpack.dump(self.db, f)
			except Exception as e:
				logger.error("Error while dumping to temp file: %s", e)
				logger.error("Location: %s", self.location)

				raise e
		if os.stat(f.name).st_size != 0:
			shutil.move(f.name, self.location)

		self.m_time = os.stat(self.location).st_mtime

	def dump(self):
		"""
		Force dump memory db to file
		"""

		if self.in_memory or not SAVE_LOAD:
			return

		self.dthread = Thread(target=self._dump)
		self.dthread.start()
		self.dthread.join()
		return True

	# save = PROXY OF SELF.DUMP()
	save = dump

	def _loaddb(self):
		"""
		Load or reload the json info from the file
		"""
		if not SAVE_LOAD:
			logger.warn("msgpack not found, install it using `pip install msgpack`\n * Only in-memory db will work")
			self.in_memory = True
			self.new()
			return
		try:
			with open(self.location, 'rb') as f:
				try:
					db = msgpack.load(f)
				except Exception as e:
					logger.error("Error while loading from file: %s", self.location)
					raise e
				self.db:dict = db
		except ValueError:
			if os.stat(self.location).st_size == 0:  # Error raised because file is empty
				self.new()
			else:
				raise  # File is not empty, avoid overwriting it

	def _autodumpdb(self, AD=True):
		"""
		Write/save the json dump into the file if auto_dump is enabled
		"""
		if self.auto_dump and AD:
			self.dump()


	def validate_key(self, key):
		"""Make sure key is a string
		msgpack is optimized for string keys, so we need to make sure"""

		if not isinstance(key, (str, bytes)):
			raise self.key_string_error

	def set(self, key, value, AD=True, rescan=True):
		"""
		Set the str value of a key
		"""
		self.rescan(rescan=rescan)
		self.validate_key(key)

		self.db[key] = value
		self._autodumpdb(AD=AD)
		return True


	def get(self, *keys, default=None, raiseErr=False, rescan=True):
		"""
		Get the value of a key or keys
		keys work as multidimensional

		keys: dimensional key sequence. if object is dict, key must be string (to fix JSON bug)

		default: act as the default, same as dict.get
		raiseErr: raise Error if key is not found, same as dict[unknown_key]
		"""
		key = keys[0]
		self.rescan(rescan=rescan)
		self.validate_key(key)
		obj = default

		try:
			obj = self.db[key]

			for key in keys[1:]:
				if isinstance(obj, dict):
					self.validate_key(key)
				obj = obj[key]

		except (KeyError, IndexError):
			if raiseErr:
				raise
			return default

		else:
			return obj


	def keys(self, rescan=True):
		"""
		Return a list of all keys in db
		"""
		self.rescan(rescan=rescan)
		return self.db.keys()

	def items(self, rescan=True):
		"""same as dict.items()"""
		self.rescan(rescan=rescan)
		return self.db.items()

	def values(self, rescan=True):
		"""same as dict.values()"""
		self.rescan(rescan=rescan)
		return self.db.values()

	def exists(self, key, rescan=True):
		"""
		Return True if key exists in db, return False if not
		"""
		self.rescan(rescan=rescan)
		return key in self.db

	def rem(self, key, AD=True, rescan=True):
		"""
		Delete a key
		"""
		self.rescan(rescan=rescan)
		if not key in self.db: # return False instead of an exception
			return False
		del self.db[key]
		self._autodumpdb(AD=AD)
		return True

	def append(self, key, more, AD=True, rescan=True):
		"""
		Add more to a key's value
		"""
		self.rescan(rescan=rescan)
		tmp = self.db[key]
		self.db[key] = tmp + more
		self._autodumpdb(AD=AD)
		return True

	def lcreate(self, name):
		"""
		Create a list, name must be str
		"""
		if isinstance(name, str):
			self.db[name] = []
			self._autodumpdb()
			return True
		else:
			raise self.key_string_error

	def ladd(self, name, value):
		"""
		Add a value to a list
		"""
		self.db[name].append(value)
		self._autodumpdb()
		return True

	def lextend(self, name, seq):
		"""
		Extend a list with a sequence
		"""
		self.db[name].extend(seq)
		self._autodumpdb()
		return True

	def lgetall(self, name):
		"""
		Return all values in a list
		"""
		return self.db[name]

	def lget(self, name, pos):
		"""
		Return one value in a list
		"""
		return self.db[name][pos]

	def lrange(self, name, start=None, end=None):
		"""
		Return range of values in a list
		"""
		return self.db[name][start:end]

	def lremlist(self, name):
		"""
		Remove a list and all of its values
		"""
		number = len(self.db[name])
		del self.db[name]
		self._autodumpdb()
		return number

	def lremvalue(self, name, value):
		"""
		Remove a value from a certain list
		"""
		self.db[name].remove(value)
		self._autodumpdb()
		return True

	def lpop(self, name, pos):
		"""
		Remove one value in a list
		"""
		value = self.db[name][pos]
		del self.db[name][pos]
		self._autodumpdb()
		return value

	def llen(self, name):
		"""
		Returns the length of the list
		"""
		return len(self.db[name])

	def lappend(self, name, pos, more):
		"""
		Add more to a value in a list
		"""
		tmp = self.db[name][pos]
		self.db[name][pos] = tmp + more
		self._autodumpdb()
		return True

	def lexists(self, name, value):
		"""
		Determine if a value  exists in a list
		"""
		return value in self.db[name]

	def dcreate(self, name):
		"""
		Create a dict, name must be str
		"""
		if isinstance(name, str):
			self.db[name] = {}
			self._autodumpdb()
			return True
		else:
			raise self.key_string_error

	def dadd(self, name, pair):
		"""
		Add a key-value pair to a dict, "pair" is a tuple
		"""
		self.db[name][pair[0]] = pair[1]
		self._autodumpdb()
		return True

	def dget(self, name, key):
		"""
		Return the value for a key in a dict
		"""
		return self.db[name][key]

	def dgetall(self, name):
		"""
		Return all key-value pairs from a dict
		"""
		return self.db[name]

	def drem(self, name):
		"""
		Remove a dict and all of its pairs
		"""
		del self.db[name]
		self._autodumpdb()
		return True

	def dpop(self, name, key):
		"""
		Remove one key-value pair in a dict
		"""
		value = self.db[name][key]
		del self.db[name][key]
		self._autodumpdb()
		return value

	def dkeys(self, name):
		"""
		Return all the keys for a dict
		"""
		return self.db[name].keys()

	def dvals(self, name):
		"""
		Return all the values for a dict
		"""
		return self.db[name].values()

	def dexists(self, name, key):
		"""
		Determine if a key exists or not in a dict
		"""
		return key in self.db[name]

	def dmerge(self, name1, name2):
		"""
		Merge two dicts together into name1
		"""
		first = self.db[name1]
		second = self.db[name2]
		first.update(second)
		self._autodumpdb()
		return True

	def deldb(self):
		"""
		Delete everything from the database
		"""
		self.db = {}
		self._autodumpdb()
		return True


# DUMMY CLASS FOR TYPING
# class PickleTable(dict):
# 	pass

# class _PickleTCell:
# 	pass

# class _PickleTRow(dict):
# 	pass

# class _PickleTColumn(list):
# 	pass



def _int_to_alpha(n):
	"""
	Convert an integer to an excel column name
	"""
	n += 1
	string = ""
	while n > 0:
		n, remainder = divmod(n - 1, 26)
		string = chr(65 + remainder) + string
	return string

class PickleTable(dict):
	def __init__(self, file_path="", *args, **kwargs):
		"""
		args:
		- filename: path to the db file (default: `""` or in-memory db)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		"""
		self.CC = 0 # consider it as country code and every items are its people. they gets NID


		self.gen_CC()


		self.busy = False
		self._pk = PickleDB(file_path, *args, **kwargs)

		# make the super dict = self._pk.db



		self.height = self.get_height()

		self.ids = [h for h in range(self.height)]

		# DEFAULR LIMIT FOR STR conversion
		self.str_limit = 50

	def __bool__(self):
		"""
		return True if the table has rows
		"""
		return bool(self.height)

	def __len__(self):
		"""
		Return the number of rows
		"""
		return self.height

	def __getitem__(self, index:Union[int, slice, str]):
		"""
		## args
		- index: row index or slice or column name
		## returns
		- PickleTRow object if index is int
		- list of PickleTRow objects if index is slice
		- PickleTColumn object if index is string
		"""
		self.rescan()
		if isinstance(index, int):
			return self.row_obj(index)
		elif isinstance(index, slice):
			return [self.row_obj(i) for i in range(*index.indices(self.height))]
		elif isinstance(index, str):
			return self.column_obj(index)
		else:
			raise TypeError("indices must be integers or slices or string, not {}".format(type(index).__name__))


	def __iter__(self):
		"""
		Iterate over all rows.
		- returns: PickleTRow object
		"""
		return self.rows_obj()

	def dataFrame(self, copy=False):
		"""
		Return a pandas DataFrame object
		- copy: return a copy of the dataframe (deepcopy)(default: `False`)
		"""
		if copy:
			return datacopy.deepcopy(self._pk.db)
		return self._pk.db

	to_dataframe = dataFrame

	def to_list(self):
		"""
		Return a list of all rows
		"""
		self.rescan()
		return [list(self.column_names_func(rescan=False))] + [self.row_obj(i).to_list() for i in range(self.height)]

	def rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""
		self._pk.rescan(rescan=rescan)

	def unlink(self):
		"""
		Unlink the db file (start using in-memory db)
		"""
		self._pk.unlink()

	def delete_file(self):
		"""
		Delete the file from the disk
		"""
		self._pk.delete_file()


	def gen_CC(self):
		"""
		Generate a new Component Code (Each PickleTable has a unique CC)
		"""
		self.CC = hash(time.time() + random.random() + time.thread_time())

		return self.CC

	def get_height(self):
		"""
		Return the number of rows
		"""
		self.rescan()
		columns = self.column_names_func(rescan=False)
		h = len(self._pk.db[columns[0]]) if columns else 0

		return h

	def __str__(self, limit:int=None):
		"""
		Return a string representation of the table
		- Default only first 50 rows are shown
		- use `limit` to override the number of rows
		"""
		self.rescan()
		limit = limit or self.str_limit
		if not TABLE:
			x = ""
			x += "\t|\t".join(self.column_names_func(rescan=False))
			for i in range(min(self.height, limit)):
				x += "\n"
				x += "\t|\t".join(str(self.row(i).values()))

		else:
			x = tabulate(
				# self[:min(self.height, limit)],
				self.rows(start=0, end=min(self.height, limit)),
				headers="keys",
				tablefmt= "simple_grid",
				#"orgtbl",
				maxcolwidths=60
				)
		if self.height > limit:
			x += "\n..."

		return x

	def str(self, limit:int=None):
		"""
		Return a string representation of the table
		- Default only first 50 rows are shown
		- use `limit` to override the number of rows
		"""
		return self.__str__(limit=limit or self.height)

	def __db__(self):
		"""
		Return the db object
		"""
		return self._pk.db

	def set_location(self, location):
		"""
		Set the location of the db file
		- from now on, the table will use this file
		- if the file does not exist, it will be created on the first update
		### if the file exists, the data will be overwritten
		"""
		self._pk.set_location(location)

	@property
	def location(self):
		"""
		Return the location of the db file
		"""
		return self._pk.location


	def lock(self, func):
		"""
		Thread safety lock to avoid race condition
		"""

		def inner(*args, **kwargs):

			while self.busy:
				time.sleep(.001)

			self.busy = True

			box = func(*args, **kwargs)

			self.busy = False

			return box

		return inner

	def column(self, name, rescan=True) -> list:
		"""
		Return a copy list of all values in column
		"""
		self.rescan(rescan=rescan)
		return self._pk.db[name].copy()

	def get_column(self, name) -> list:
		"""
		Return the list pointer to the column (unsafe)
		"""
		return self._pk.db[name]

	def column_obj(self, name):
		"""
		Return a column object `_PickleTColumn` in db
		"""
		return _PickleTColumn(self, name, self.CC)

	def columns(self, rescan=True):
		"""
		Return a **copy list** of all columns in db
		"""
		self.rescan(rescan=rescan)
		return self._pk.db.copy()

	def columns_obj(self, rescan=True):
		"""
		Return a list of all columns in db
		"""
		self.rescan(rescan=rescan)
		return [_PickleTColumn(self, name, self.CC) for name in self._pk.db]

	def column_names_func(self, rescan=True):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self.rescan(rescan=rescan)
		return tuple(self._pk.db.keys())

	@property
	def column_names(self):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self.rescan()
		return tuple(self._pk.db.keys())

	def keys(self, rescan=True):
		"""
		Return a list of all keys in db
		"""
		return self._pk.keys(rescan=rescan)

	def values(self, rescan=True):
		"""
		Return a list of all values in db
		"""
		return self._pk.values(rescan=rescan)

	def items(self, rescan=True):
		"""
		Return a list of all items in db
		"""
		return self._pk.items(rescan=rescan)

	def add_column(self, *names, exist_ok=False, AD=True, rescan=True):
		"""
		name: column name
		exist_ok: ignore if column already exists. Else raise KeyError
		AD: auto-dump
		"""
		self.rescan(rescan=rescan)

		def add(name):
			self._pk.validate_key(key=name)

			tsize = self.height
			if name in self.column_names_func(rescan=False):
				if exist_ok :
					tsize = self.height - len(self._pk.db[name])
					if not tsize: # 0 cells to add
						return
				else:
					raise KeyError("Column Name already exists")
			else:
				self._pk.db[name] = []
				self.gen_CC() # major change


			self._pk.db[name].extend([None] * tsize)


		# if the 1st argument is a list, unpack it
		if isinstance(names[0], Iterable) and not isinstance(names[0], str) and not isinstance(names[0], bytes) and len(names) == 1:
			names = names[0]

		for name in names:
			add(name)


		self.auto_dump(AD=AD)

	add_columns = add_column # alias


	def del_column(self, name, AD=True, rescan=True):
		"""
		@ locked
		# name: column to delete
		# AD: auto dump
		"""
		self.rescan(rescan=rescan)
		self.lock(self._pk.db.pop)(name)
		if not self._pk.db: # has no keys
			self.height = 0

		# self.gen_CC()

		self.auto_dump(AD=AD)



	def row(self, row, _columns=(), rescan=True):
		"""
		returns a row dict by `row index`
		_column: specify columns you need, blank if you need all
		"""
		self.rescan(rescan=rescan)

		columns = _columns or self.column_names_func(rescan=False)
		return {j: self._pk.db[j][row] for j in columns}

	def row_by_id(self, row_id, _columns=(), rescan=True):
		"""
		returns a COPY row dict by `row_id`
		- _column: specify columns you need, blank if you need all
		"""
		return self.row(self.ids.index(row_id), _columns=_columns, rescan=rescan)

	def row_obj(self, row, loop_back=False):
		"""
		Return a row object `_PickleTRow` in db
		- row: row index
		"""
		if loop_back:
			row = row % self.height
		return _PickleTRow(source=self,
			uid=self.ids[row],
			CC=self.CC)

	def row_obj_by_id(self, row_id):
		"""Return a row object `_PickleTRow` in db
		- row: row index
		"""
		return _PickleTRow(source=self,
			uid=row_id,
			CC=self.CC)

	def rows(self, start:int=0, end:int=None, sep:int=1, loop_back=False, rescan=True) -> Generator[dict, None, None]:
		"""Return a list of all rows in db
		- start: start index (default: 0)
		- end: end index (default: None|end of the table)
		- sep: step size (default: 1)
		"""
		self.rescan(rescan=rescan)

		if sep == 0:
			raise ValueError("sep cannot be zero")

		if self.height==0:
			return []

		if end is None: # end of the table
			end = self.height
		while start<0: # negative indexing support
			start = self.height + start
		while end<0: # negative indexing support
			end = self.height + end
		if end > self.height or start > self.height:
			if loop_back: # loop back support (circular indexing)
				ids = []
				distance = end - start
				start = start % self.height

				for i in range(0, distance, sep):
					ids.append(self.ids[(start+i) % self.height])
			else:
				raise IndexError("start/end index out of range, [expected: 0 to", self.height, "] [got:", start, end, "]")

		else:
			ids = self.ids[start:end:sep]

		for id in ids:
			# already rescaned
			yield self.row_by_id(id, rescan=False)

	def rows_obj(self, start:int=0, end:int=None, sep:int=1, loop_back=False, rescan=True) -> Generator["_PickleTRow", None, None]:
		"""Return a list of all rows in db
		- start: start index (default: 0)
		- end: end index (default: None|end of the table)
		- sep: step size (default: 1)
		"""
		self.rescan(rescan=rescan)

		if sep == 0:
			raise ValueError("sep cannot be zero")

		if end is None: # end of the table
			end = self.height
		while start<0: # negative indexing support
			start = self.height + start
		while end<0: # negative indexing support
			end = self.height + end
		if end > self.height or start > self.height:
			if loop_back: # loop back support (circular indexing)
				ids = []
				distance = end - start
				start = start % self.height

				for i in range(0, distance, sep):
					ids.append(self.ids[(start+i) % self.height])
			else:
				raise IndexError("start/end index out of range, [expected: 0 to", self.height, "] [got:", start, end, "]")

		else:
			ids = self.ids[start:end:sep]

		for id in ids:
			yield self.row_obj_by_id(id)

	def search_iter(self, kw, column=None , row=None, full_match=False, return_obj=True, rescan=True) -> Generator["_PickleTCell", None, None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the cell object in loop
		- kw: keyword to search
		- column: column name
		- row: row index
		- full_match: search for full match (default: `False`)
		- return_obj: return cell object instead of value (default: `True`)
		- return: cell object

		ie:
		```python
		for cell in db.search_iter("abc"):
			print(cell.value)
		```
		"""
		self.rescan(rescan=rescan)

		if return_obj:
			ret = self.get_cell_obj
		else:
			ret = self.get_cell

		def check(item, is_in):
			if full_match or not isinstance(is_in, Iterable):
				return is_in == item

			return item in is_in


		if column and row:
			cell = self.get_cell(column, row, rescan=False)
			if check(kw, cell):
				yield ret(col=column, row=row)
			return None

		elif column:
			for r, i in enumerate(self.column(column, rescan=False)):
				if check(kw, i):
					yield ret(col=column, row=r)

			return None

		elif row:
			_row = self.row(row, rescan=False)
			for c, i in _row.items():
				if check(kw, i):
					yield ret(col=c, row=row)

			return None

		else:
			for col in self.column_names_func(rescan=False):
				for r, i in enumerate(self.column(col, rescan=False)):
					if check(kw, i):
						yield ret(col=col, row=r)

	def search_iter_row(self, kw, column=None , row=None, full_match=False, return_obj=True, rescan=True) -> Generator["_PickleTRow", None, None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the row object in loop
		- kw: keyword to search
		- column: column name
		- row: row index
		- full_match: search for full match (default: `False`)
		- return_obj: return cell object instead of value (default: `True`)
		- return: row object

		ie:
		```python
		for row in db.search_iter_row("abc"):
			print(row)
		```
		"""
		for cell in self.search_iter(kw, column=column , row=row, full_match=full_match, return_obj=True, rescan=rescan):
			row_ = cell.row_obj()
			if return_obj:
				yield row_
			else:
				yield row_.to_dict()

	def search(self, kw, column=None , row=None, full_match=False, return_obj=True, return_row=False, rescan=True) -> List[Union["_PickleTCell", "_PickleTRow"]]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the cell object in loop
		- kw: keyword to search
		- column: column name
		- row: row index
		- full_match: search for full match (default: `False`)
		- return_obj: return cell/row object instead of value (default: `True`)
		- return_row: return row object instead of cell object (default: `False`)
		- return: cell object

		ie:
		```python
		for cell in db.search("abc"):
			print(cell.value)
		```
		"""
		ret = []
		for cell in self.search_iter(kw, column=column , row=row, full_match=full_match, return_obj=True, rescan=rescan):
			if return_row:
				row_ = cell.row_obj()
				if return_obj:
					ret.append(row_)
				else:
					ret.append(row_.to_dict())

			else:
				ret.append(cell if return_obj else cell.value)

		return ret


	def find_1st(self, kw, column=None , row=None, full_match=False, return_obj=True, rescan=True) -> Union["_PickleTCell", None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the 1st matched cell object
		- kw: keyword to search
		- column: column name
		- row: row index
		- full_match: search for full match (default: `False`)
		- return_obj: return cell object instead of value (default: `True`)
		- return: cell object or None

		ie:
		```python
		cell = db.find_1st("abc")
		print(cell.value)
		```
		"""
		column_names = self.column_names
		if column and column not in column_names:
			raise KeyError("Invalid column name:", column, '\nAvailable columns:', column_names)

		for cell in self.search_iter(kw, column=column , row=row, full_match=full_match, return_obj=return_obj, rescan=rescan):
			return cell

	def find_1st_row(self, kw, column=None , row=None, full_match=False, return_obj=True, rescan=True) -> Union["_PickleTRow", None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the 1st matched row object

		- kw: keyword to search
		- column: column name
		- row: row index
		- full_match: search for full match (default: `False`)
		- return_obj: return cell object instead of value (default: `True`)
		- return: row object or None

		ie:
		```python
		row = db.find_1st_row("abc")
		print(row)
		```
		"""
		column_names = self.column_names
		if column and column not in column_names:
			raise KeyError("Invalid column name:", column, '\nAvailable columns:', column_names)

		for row in self.search_iter_row(kw, column=column , row=row, full_match=full_match, return_obj=return_obj, rescan=rescan):
			return row


	def set_cell(self, col, row, val, AD=True, rescan=True):
		"""
		set value of a cell
		- col: column name
		- row: row index
		- val: value of cell
		- AD: auto dump

		ie:
		```python
		db.set_cell("name", 0, "John")
		```
		"""
		self.rescan(rescan=rescan)

		self._pk.db[col][row] = val

		self.auto_dump(AD=AD)

	def set_cell_by_id(self, col, row_id, val, AD=True, rescan=True):
		"""
		set value of a cell
		- col: column name
		- row_id: unique id of the row
		- val: value of cell
		- AD: auto dump

		ie:
		```python
		db.set_cell_by_id("name", 0, "John")
		```
		"""
		return self.set_cell(col=col, row=self.ids.index(row_id), val=val, AD=AD, rescan=rescan)

	def get_cell(self, col, row, rescan=True):
		"""
		get cell value only (by row index)
		- col: column name
		- row: row index
		"""
		self.rescan(rescan=rescan)


		try:
			_col = self._pk.db[col]
		except KeyError:
			column_names = self.column_names_func(rescan=False)
			raise KeyError("Invalid column name:", col, "\nAvailable columns:", column_names)
		try:
			cell = _col[row]
		except IndexError:
			raise IndexError("Invalid row index:", row, "\nAvailable rows:", self.height)

		return cell

	def get_cell_by_id(self, col, row_id):
		"""
		get cell value only (by row_id)
		- col: column name
		- row_id: unique id of the row
		"""
		try:
			row = self.ids.index(row_id)
		except ValueError:
			raise ValueError("Invalid row id:", row_id)
		return self.get_cell(col, row)

	def get_cell_obj(self, col, row:int=-1, row_id:int=-1) -> "_PickleTCell":
		"""
		return cell object
		- col: column name
		- row: row index (either row or row_id must be given)
		- row_id: unique id of the row

		ie:
		```python
		cell = db.get_cell_obj("name", 0)
		```
		"""

		if row>-1:
			if row>=self.height:
				raise IndexError(f"Invalid row index. [expected: 0 to {self.height-1}] [got: {row}]")
			return _PickleTCell(self, column=col, row_id=self.ids[row], CC=self.CC)
		if row_id>-1:
			return _PickleTCell(self, column=col, row_id=row_id, CC=self.CC)

		# in case row or row_id is invalid
		raise IndexError("Invalid row")


	def pop_row(self, index:int=-1, returns=True, AD=True, rescan=True) -> Union[dict, None]:
		"""
		Pop a row from the table (last row by default)

		- index: index of the row (not id), if not given, last row of the table is popped
		- returns: whether return the popped row. (how pop should work)
		- AD: auto dump
		- return: row dict if returns is True

		ie:
		```python
		row = db.pop_row()
		print(row)
		```
		"""
		self.rescan(rescan=rescan)

		box = None
		if returns:
			box = self.row(index)

		for c in self.column_names_func(rescan=False):
			self._pk.db[c].pop(index)

		self.ids.pop(index)

		self.height -=1

		self.auto_dump(AD=AD)

		return box

	def del_row(self, row:int, AD=True):
		"""
		Delete a row from the table (by row index)
		- row: row index
		- AD: auto dump
		"""
		# Auto dumps (locked)
		self.lock(self.pop_row)(row, returns=False, AD=AD)



	def del_row_id(self, row_id:int, AD=True):
		"""
		Delete a row from the table (by row_id)
		- row_id: unique id of the row
		- AD: auto dump
		"""
		self.del_row(self.ids.index(row_id), AD=AD)

	def clear(self, AD=True, rescan=True):
		"""
		Delete all rows

		AD: auto dump
		"""
		self.rescan(rescan=rescan)

		for c in self.column_names_func(rescan=False):
			self._pk.db[c].clear()

		self.ids.clear()
		self.height = 0

		self.auto_dump(AD=AD)


	def copy(self, location=None, auto_dump=True, sig=True) -> "PickleTable":
		"""
		Copy the table to a new location/memory
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""

		new = PickleTable(location, auto_dump=auto_dump, sig=sig)
		new.add_column(*self.column_names)
		new._pk.db = datacopy.deepcopy(self.__db__())
		new.height = self.height
		new.ids = self.ids.copy()


		return new




	def _add_row(self, row:Union[dict, "_PickleTRow"], position:int="last", rescan=True) -> "_PickleTRow":
		"""
		@ unlocked
		Add a row to the table. (internal use, no auto dump)
		- row: row must be a dict or _PickleTRow containing column names and values
		- position: position to add the row (default: "last")
		- return: row object
		"""
		self.rescan(rescan=rescan)


		if not self.ids:
			row_id = 0
		else:
			row_id = self.ids[-1] + 1


		if isinstance(position, int):
			for k in self.column_names_func(rescan=False):
				self._pk.db[k].insert(position, row.get(k))
			self.ids.insert(position, row_id)

		else:
			for k in self.column_names_func(rescan=False):
				self._pk.db[k].append(row.get(k))
			self.ids.append(row_id)


		#for k, v in row.items():
		#	self.set_cell(k, self.height, v, AD=False)

		self.height += 1

		return self.row_obj_by_id(row_id)


	def add_row(self, row:Union[dict, "_PickleTRow"], position="last", AD=True) -> "_PickleTRow":
		"""
		@ locked
		- row: row must be a dict|_PickleTRow containing column names and values
		- position: position to add the row (default: "last")
		- AD: auto dump
		- return: row object

		ie:
		```python
		db.add_row({"name": "John", "age": 25})
		db.add_row(row_obj)
		```
		"""

		row_obj = self.lock(self._add_row)(row=row,position=position)

		self.auto_dump(AD=AD)

		return row_obj


	def insert_row(self, row:Union[dict, "_PickleTRow"], position:int="last", AD=True) -> "_PickleTRow":
		"""
		@ locked
		- row: row must be a dict|_PickleTRow containing column names and values
		- position: position to add the row (default: "last")
		- AD: auto dump
		- return: row object

		ie:
		```python
		db.insert_row({"name": "John", "age": 25}, position=0)
		db.insert_row(row_obj, position=0)
		```
		"""

		return self.add_row(row=row, position=position, AD=AD)




	def add_row_as_list(self, row:list, position:int="last", AD=True) -> "_PickleTRow":
		"""
		@ locked
		- row: row must be a list containing values. (order must match with column names)
		- position: position to add the row (default: "last")
		- AD: auto dump
		- return: row object

		ie:
		```python
		# db.column_names == ["name", "age"]
		db.add_row_as_list(["John", 25])
		"""

		row_obj = self.lock(self._add_row)(row={k:v for k, v in zip(self.column_names, row)}, position=position)

		self.auto_dump(AD=AD)

		return row_obj

	def sort(self, column=None, key=None, reverse=False, copy=False, AD=True, rescan=True):
		"""
		Sort the table by a key
		- column: column name to sort by
		- key: function to get the key for sorting
		- reverse: reverse the sorting
		- copy: return a copy of the table (default: `False`)
		- AD: auto dump
		"""
		self.rescan(rescan=rescan)

		if copy:
			if copy is True:
				copy = ''
			db = self.copy(location=copy, auto_dump=self._pk.auto_dump, sig=self._pk.sig)
		else:
			db = self

		# if key is None:
		# 	self.ids.sort(reverse=reverse)
		# else:
		# 	self.ids.sort(key=lambda x: self.get_cell(key, x), reverse=reverse)

		# self.auto_dump(AD=AD)

		# create a index array for sorting then apply to all columns and ids
		if column:
			def get_cell(row: "_PickleTRow"):
				return row[column]

		elif key:
			def get_cell(row: "_PickleTRow"):
				return key(row)

		else:
			def get_cell(row: "_PickleTRow"):
				return row.values()

		seq = range(db.height)
		seq = sorted(seq, key=lambda x: get_cell(db.row_obj(x)), reverse=reverse)

		# apply to all columns
		for col in self.column_names:
			db._pk.db[col] = [self._pk.db[col][i] for i in seq]

		db.ids = [self.ids[i] for i in seq]

		db.auto_dump(AD=AD)

		return db

	def remove_duplicates(self, columns=None, AD=True):
		"""
		Remove duplicate rows (keep the 1st occurrence)
		- columns: columns to check for duplicates (default: all columns) (if None, all columns are checked) (if string, only that column is checked) (if list, all the mentioned columns are checked)
		- AD: auto dump
		"""
		if columns is None:
			columns = self.column_names
		if isinstance(columns, str):
			columns = [columns]

		# print(columns)

		if not self or not columns:
			return

		def get_next(row: "_PickleTRow"):
			try:
				return row.next()
			except IndexError:
				return None

		row = self.row_obj(0)
		# while row is not None:
		# 	next = get_next(row)
		# 	while next is not None:
		# 		if any(next[col]!=row[col] for col in columns):
		# 			next = get_next(next)
		# 		else:
		# 			_next = get_next(next)
		# 			next.del_row()
		# 			next = _next

		# 	row = get_next(row)

		seen_rows = set()
		while row is not None:
			row_key = tuple(row[col] for col in columns)
			if row_key in seen_rows:
				next_row = get_next(row)
				row.del_row()
				row = next_row
			else:
				seen_rows.add(row_key)
				row = get_next(row)

		self.auto_dump(AD=AD)



	def verify_source(self, CC):
		"""
		Verify the source of the table derived objects (row, column, cell)
		- CC: the Component Code of the source (table) (all derived objects must have the same CC)
		"""
		return CC == self.CC

	def raise_source(self, CC):
		"""
		Raise error if the source is not verified/mismatched
		"""
		if not self.verify_source(CC):
			raise KeyError("Database has been updated drastically. Row index will mismatch!")



	def dump(self):
		"""
		Dump the table to the db file

		ignored if the table is in-memory
		"""
		self._pk.dump()

	def auto_dump(self, AD=True):
		"""
		Auto dump the table to the db file
		- ignored if the table is in-memory
		"""
		self._pk._autodumpdb(AD=AD)


	def to_csv(self, filename=None, write_header=True) -> str:
		"""
		Write the table to a csv file
		- filename: path to the file (if None, use current filename.csv) (if in memory and not provided, uses "table.csv")
		- write_header: write column names as header (1st row) (default: `True`)

		- return: path to the file
		"""
		if filename is None:
			# check filename
			path = self._pk.location
			if not path:
				path = "table.csv"
			else:
				path = os.path.splitext(path)[0] + ".csv"
		else:
			path = filename

		with open(path, "wb") as f:
			f.write(b'')


		with open(path, "w", newline='', encoding='utf8') as f:
			writer = csv.writer(f)

			columns = self.column_names
			if write_header:
				writer.writerow(columns) # header
			for row in self.rows():
				writer.writerow([row[k] for k in columns])


		return os.path.realpath(path)

	def to_csv_str(self, write_header=True) -> str:
		"""
		Return the table as a csv string
		- write_header: write column names as header (1st row) (default: `True`)
		"""
		output = io.StringIO()
		writer = csv.writer(output)

		columns = self.column_names
		if write_header:
			writer.writerow(columns) # header
		for row in self.rows():
			writer.writerow([row[k] for k in columns])

		return output.getvalue()

	def load_csv(self, filename, header=True, ignore_none=False, ignore_new_headers=False, on_file_not_found='error', AD=True):
		"""
		Load a csv file to the table
		- WILL OVERWRITE THE EXISTING DATA (To append, make a new table and extend)
		- header:
			* if True, the first row will be considered as column names
			* if False, the columns will be named as "Unnamed-1", "Unnamed-2", ...
			* if "auto", the columns will be named as "A", "B", "C", ..., "Z", "AA", "AB", ...
		- ignore_none: ignore the None rows
		- ignore_new_headers: ignore new headers if found `[when header=True]` (default: `False`)
		- on_file_not_found: action to take if the file is not found (default: `'error'`) [options: `error`|`ignore`|`warn`|`no_warning`]
			* if `error`, raise FileNotFoundError
			* if `ignore`, ignore the operation (no warning, **no clearing**)
			* if `no_warning`, ignore the operation, but **clears db**
			* if `warn`, print warning and ignore the operation, but **clears db**
		"""
		columns_names = self.column_names

		def add_row(row, columns):
			if ignore_none and all(v is None for v in row):
				return

			new_row = {k: v for k, v in zip(columns, row)}

			# print(new_row)

			self.add_row(new_row, AD=False)



		if not os.path.exists(filename):
			if on_file_not_found == 'error':
				raise FileNotFoundError(f"File not found: {filename}")
			elif on_file_not_found == 'ignore':
				return
			else:
				self.clear(AD=AD)
				if on_file_not_found == 'warn':
					print(f"File not found: {filename}")
				if on_file_not_found == 'no_warning':
					pass

				return

		self.clear(AD=False)

		with open(filename, 'r', encoding='utf8') as f:
			reader = csv.reader(f)
			if header is True:
				columns = next(reader)
				updated_columns = []
				n = len(self.column_names_func(rescan=False))
				for col in columns:
					if (col is None or col == ""):
						while f"Unnamed-{n}" in columns_names:
							n += 1
						col = f"Unnamed-{n}"
						n += 1

					if col in columns_names or col in updated_columns:
						if ignore_new_headers:
							continue
					updated_columns.append(col)

				columns = updated_columns

				# print(updated_columns)
				self.add_column(updated_columns, exist_ok=True, AD=False, rescan=False)

			elif isinstance(header, str) and header.lower() == "auto":
				row = next(reader)
				# columns = [_int_to_alpha(i) for i in range(len(row))]
				new_columns = []
				n = len(columns_names)

				for _ in range(len(row)):
					while _int_to_alpha(n) in columns_names:
						n += 1
					new_columns.append(_int_to_alpha(n))
					n += 1

				self.add_column(new_columns, exist_ok=True, AD=False, rescan=False)
				columns = new_columns

				add_row(row, columns)
			else:
				# count the columns, and name them as "Unnamed-1", "Unnamed-2", ...
				row = next(reader)
				col_count = len(row)

				new_columns = []
				n = len(columns_names)

				for _ in range(col_count):
					while f"Unnamed-{n}" in columns_names:
						n += 1
					new_columns.append(f"Unnamed-{n}")
					n += 1

				self.add_column(new_columns, exist_ok=True, AD=False, rescan=False)
				columns = new_columns

				add_row(row, columns)





			for row in reader:
				add_row(row, columns)

		self.auto_dump(AD=AD)


	def extend(self, other: "PickleTable", add_extra_columns=None, AD=True):
		"""
		Extend the table with another table
		- other: `PickleTable` object
		- add_extra_columns: add extra columns if not exists (default: `None`)
			- if `True`, add extra columns
			- if `False`, ignore extra columns
			- if `None`, raise error if columns mismatch (default)
		- AD: auto dump

		"""
		if other is None:
			return

		if not isinstance(other, type(self)):
			raise TypeError("Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(other).__name__))

		keys = other.column_names
		this_keys = self.column_names

		if add_extra_columns:
			self.add_column(*keys, exist_ok=True, AD=False)
		else:
			for key in keys:
				if key not in this_keys:
					if add_extra_columns is False:
						keys.remove(key)
					else:
						raise ValueError("Both tables must have same column names")


		for row in other:
			self._add_row({k: row[k] for k in keys})

		self.auto_dump(AD=AD)


	def add(self, table:Union["PickleTable", dict], add_extra_columns=None, AD=True):
		"""
		Add another table to this table
		- table: PickleTable object or dict
		- add_extra_columns: add extra columns if not exists (default: `None`-> raise error if columns mismatch)
			- if True, add extra columns
			- if False, ignore extra columns
			- if None, raise error if columns mismatch (default)
		- AD: auto dump
		"""
		if isinstance(table, dict) or isinstance(table, type(self)):
			keys = table.keys()
		else:
			raise TypeError("Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(table).__name__))

		this_keys = self.column_names
		if add_extra_columns:
			self.add_column(*keys, exist_ok=True, AD=False)
		else:
			for key in keys:
				if key not in this_keys:
					if add_extra_columns is False:
						keys.remove(key)
					else:
						raise ValueError(f"Columns mismatch: {this_keys} != {keys}")

		if isinstance(table, dict):
			max_height = 0
			for key, value in table.items():
				if not isinstance(value, (list, tuple)):
					raise TypeError(f"Value type must be a list/tuple. Got: {type(value).__name__} for key: {key}")

				max_height = max(max_height, len(value))

			for i in range(max_height):
				row = {k: table[k][i] if i<len(table[k]) else None for k in keys}
				self.add_row(row, AD=False)

		else:
			self.extend(table, )

		self.auto_dump(AD=AD)




class _PickleTCell:
	def __init__(self, source:PickleTable, column, row_id:int, CC):
		self.source = source
		self.id = row_id
		self.column_name = column
		self.CC = CC
		self.deleted = False

	@property
	def value(self):
		self.source_check()

		return self.source.get_cell_by_id(self.column_name, self.id)


	def is_deleted(self):
		"""
		return True if the cell is deleted, else False
		"""
		self.deleted = self.deleted or (self.id not in self.source.ids) or (self.column_name not in self.source.column_names)

		return self.deleted

	def raise_deleted(self):
		"""
		Raise error if the cell is deleted
		"""
		if self.is_deleted():
			raise ValueError(f"Cell has been deleted. Invalid cell object.\n(last known id: {self.id}, column: {self.column_name})")

	def __str__(self):
		return str({
			"value": self.value,
			"column": self.column_name,
			"row": self.row
		})

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.value == other.value

		return self.value==other

	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.value < other.value

		return self.value<other

	def __le__(self, other):
		return self.__eq__(other) or self.__lt__(other)

	def __gt__(self, other):
		if isinstance(other, self.__class__):
			return self.value > other.value

		return self.value>other

	def __ge__(self, other):
		return self.__eq__(other) or self.__gt__(other)

	def __contains__(self, item):
		return item in self.value

	def set(self, value, AD=True):
		"""
		Set the `value` of the cell
		"""
		self.source_check()

		self.source.set_cell_by_id(self.column_name, self.id, val=value, AD=AD)


	@property
	def row_index(self):
		self.source_check()

		return self.source.ids.index(self.id)

	@property
	def row(self):
		"""
		returns a COPY row dict of the cell
		"""
		return self.source.row_by_id(self.id)

	def row_obj(self) -> "_PickleTRow":
		"""
		returns the row object of the cell
		"""
		self.source_check()

		return self.source.row_obj_by_id(row_id=self.id)

	@property
	def column(self):
		"""Returns a copy of the column list"""
		return self.source.column(self.column_name)

	def column_obj(self):
		"""Returns the column object"""
		return self.source.column_obj(self.column_name)

	def source_check(self):
		self.source.raise_source(self.CC)

	def clear(self):
		"""Clear the cell value"""
		self.source_check()

		self.source.set_cell_by_id(self.column_name, self.id, None)


class _PickleTRow(dict):
	def __init__(self, source:PickleTable, uid, CC):
		self.source = source
		# self.id: unique id of the row
		self.id = uid
		self.CC = CC
		self.deleted = False

	def is_deleted(self):
		"""
		return True if the row is deleted, else False
		"""
		self.deleted = self.deleted or (self.id not in self.source.ids)

		return self.deleted

	def raise_deleted(self):
		"""
		Raise error if the row is deleted
		"""
		if self.is_deleted():
			raise ValueError(f"Row has been deleted. Invalid row object (last known id: {self.id})")

	def __getitem__(self, name):
		self.source.raise_source(self.CC)

		return self.source.get_cell_by_id(name, self.id)

	def __bool__(self):
		"""
		return True if the row has values
		"""
		return any(self.values())

	def to_dict(self):
		"""
		returns a copy of the row as dict
		"""
		self.raise_deleted()
		return {k: self[k] for k in self.source.column_names}

	def get(self, name, default=None, rescan=True):
		self.raise_deleted()
		if name not in self.source.column_names_func(rescan=rescan):
			return default

		return self[name]

	def get_cell_obj(self, name, default=None, rescan=True):
		self.raise_deleted()
		if name not in self.source.column_names_func(rescan=rescan):
			return default

		return self.source.get_cell_obj(col=name, row_id=self.id)

	def set_item(self, name, value, AD=True):
		"""
		* name: column name
		* value: accepts both raw value and _PickleTCell obj
		* AD: auto dump
		"""
		# Auto dumps
		self.raise_deleted()
		self.source.raise_source(self.CC)

		if isinstance(value, _PickleTCell):
			value = value.value

		self.source.set_cell_by_id(name, self.id, value, AD=AD)

	def __setitem__(self, name, value):
		"""@ Auto dumps
		* name: column name
		* value: accepts both raw value and _PickleTCell obj
		"""
		self.set_item(name, value, AD=True)

	def del_item(self, name, AD=True):
		"""
		* name: column name
		* AD: auto dump
		"""
		self.raise_deleted()
		self.source.raise_source(self.CC)

		self.source.set_cell_by_id(name, self.id, None, AD=AD)


	def __delitem__(self, name):
		# Auto dump
		self.del_item(name, AD=True)

	def __iter__(self):
		return self.items_iter()

	def index(self):
		"""
		returns the current index of the row
		"""
		self.raise_deleted()
		return self.source.ids.index(self.id)

	def update(self, new:Union[dict, "_PickleTRow"], ignore_extra=False, AD=True):
		"""
		Update the row with new values
		- new: dict of new values
		- ignore_extra: ignore extra keys in new dict
		- AD: Auto dumps
		"""
		self.raise_deleted()

		for k, v in new.items():
			try:
				self.source.set_cell(k, self.source.ids.index(self.id), v, AD=False)
			except KeyError:
				if not ignore_extra:
					raise

		self.source.auto_dump(AD=AD)

	def __str__(self):
		return "<PickleTable._PickleTRow object> " + str(self.to_dict())

	def __repr__(self):
		return str(self.to_dict())

	def keys(self):
		self.raise_deleted()
		return self.source.column_names

	def values(self):
		return [self[k] for k in self.keys()]

	def items_iter(self):
		for k in self.keys():
			yield (k, self[k])

	def items(self):
		return list(self.items_iter())

	def next(self, loop_back=False):
		"""
		returns the next row object
		"""
		pos = self.index()+1
		if loop_back:
			pos = pos%self.source.height
		return self.source.row_obj(pos)

	def del_row(self):
		"""
		Delete the row
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		# Auto dumps
		self.raise_deleted()
		self.source.raise_source(self.CC)

		self.source.del_row_id(self.id)

		self.deleted = False

	def to_list(self) -> list:
		"""
		returns the row as list
		"""
		self.raise_deleted()

		return [self[k] for k in self.source.column_names]

	def __eq__(self, other):
		self.raise_deleted()
		try:
			for k in self.source.column_names:
				if self[k] != other[k]:
					return False
			return True
		except KeyError:
			return False

	def __ne__(self, other):
		self.raise_deleted()
		return not self.__eq__(other)



class _PickleTColumn(list):
	def __init__(self, source:PickleTable, name, CC):
		self.source = source
		self.name = name
		self.CC = CC
		self.deleted = False

	def is_deleted(self):
		"""
		return True if the column is deleted, else False
		"""
		self.deleted = self.deleted or (self.name not in self.source.column_names_func(rescan=False))

		return self.deleted

	def raise_deleted(self):
		"""
		Raise error if the column is deleted
		"""
		if self.is_deleted():
			raise ValueError(f"Column has been deleted. Invalid column object (last known name: {self.name})")


	def __getitem__(self, row:Union[int, slice]):
		"""
		row: the index of row (not id)
		"""
		self.raise_deleted()

		if isinstance(row, int):
			return self.source.get_cell(col=self.name, row=row)
		elif isinstance(row, slice):
			return [self.source.get_cell(col=self.name, row=i) for i in range(*row.indices(self.source.height))]
		else:
			raise TypeError("indices must be integers or slices, not {}".format(type(row).__name__))

	def __len__(self) -> int:
		self.raise_deleted()
		return self.source.height

	def re__name(self, new_name, AD=True):
		"""
		Rename the column (dangerous operation, thats why its re__name) (Safer alternative coming soon, plan, use id like rows, need to update all relative objects)
		## (Warning: This will invalidate other relative objects)
		- new_name: new name of the column
		- AD: auto dump
		"""
		self.raise_deleted()
		self.source.raise_source(self.CC)

		self.source.add_column(new_name, exist_ok=True, AD=False)
		self.source._pk.db[new_name] = self.source._pk.db.pop(self.name)

		self.source.auto_dump(AD=AD)

		self.name = new_name

	def get(self, row:int, default=None):
		"""
		get the cell value from the column by row index
		"""
		self.raise_deleted()
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self[row]

	def get_cell_obj(self, row:int, default=None):
		self.raise_deleted()
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self.source.get_cell_obj(col=self.name, row=row)

	def set_item(self, row:int, value, AD=True):
		"""
		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		* AD: auto dump
		"""

		self.raise_deleted()
		# self.source.raise_source(self.CC)

		if isinstance(value, _PickleTCell):
			value = value.value

		self.source.set_cell(col=self.name, row=row, val=value, AD=AD)

	def __setitem__(self, row:int, value):
		"""
		@ Auto dumps
		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		"""

		# self.source.raise_source(self.CC)
		self.set_item(row, value, AD=True)

	def del_item(self, row:int, AD=True):
		"""
		* row: row index (not id)
		* AD: auto dump
		"""
		self.raise_deleted()
		self.source.set_cell(self.name, row, None, AD=AD)

	def __delitem__(self, row:int):
		"""
		@ Auto dump
		* row: index of row (not id)
		"""
		self.del_item(row, AD=True)

	def __iter__(self):
		return self.get_cells_obj()

	def to_list(self) -> list:
		"""
		returns the column as list
		"""
		self.raise_deleted()
		return [i.value for i in self]

	def source_list(self):
		"""
		returns the column list as a pointer
		"""
		self.raise_deleted()
		return self.source.get_column(self.name)

	def get_cells_obj(self, start:int=0, end:int=None, sep:int=1):
		"""Return a list of all rows in db"""
		self.raise_deleted()
		if end is None:
			end = self.source.height
		if end<0:
			end = self.source.height + end

		for i in range(start, end, sep):
			yield self.get_cell_obj(i)


	def append(self, *args, **kwargs):
		"""
		`append`, `extend`, `sort`, `reverse`, `pop`, `insert`, `remove` are not supported
		"""
		raise NotImplementedError("You can't manually do append, extend, sort, reverse, pop, insert, remove on a column. Use alternate methods instead")

	extend = append
	sort = append
	reverse = append
	pop = append
	insert = append

	def update(self, column:Union[list, "_PickleTColumn"], AD=True):
		"""
		@ Auto dumps
		- column: list of values to update
		"""
		self.raise_deleted()
		self.source.raise_source(self.CC)

		if isinstance(column, self.__class__):
			column = column.to_list()


		for i, v in enumerate(column):
			self.set_item(i, v, AD=False)

		self.source.auto_dump(AD=AD)

	def remove(self, value, n_times=1):
		"""
		@ Auto dumps
		- This will remove the occurrences of the value in the column (from top to bottom)
		- n_times: number of occurrences to remove (0: all)
		"""
		self.raise_deleted()
		for i in self:
			if i == value:
				i.clear()
				n_times -= 1
				if n_times==0:
					break



	def clear(self, AD=True, rescan=True) -> None:
		"""
		@ Auto dumps
		# This will Set all cells in column to `None`
		"""
		self.raise_deleted()

		self.source.raise_source(self.CC)
		self.source.rescan(rescan=rescan)

		for row in range(self.source.height):
			self.source.set_cell(col=self.name, row=row, val=None, AD=False, rescan=False)

		self.source.auto_dump(AD=AD)



	def __str__(self):
		self.raise_deleted()

		return "<PickleTable._PickleTColumn object> " + str(self.source.get_column(self.name))

	def __repr__(self):
		self.raise_deleted()

		return repr(self.source.get_column(self.name))

	def del_column(self):
		"""
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		self.raise_deleted()

		self.source.raise_source(self.CC)

		self.source.del_column(self.name)

		self.deleted = False


	def apply(self, func=None, row_func=False, copy=False, AD=True):
		"""
		Apply a function to all cells in the column
		Overwrites the existing values
		"""
		self.raise_deleted()
		ret = []
		if row_func:
			for i in range(self.source.height):
				if copy:
					ret.append(func(self.source.row_obj(i)))
				else:
					# self[i] = func(self.source.row_obj(i))
					self.set_item(i, func(self.source.row_obj(i)), AD=False)
		else:
			for i in range(self.source.height):
				if copy:
					ret.append(func(self[i]))
				else:
					# self[i] = func(self[i])
					self.set_item(i, func(self[i]), AD=False)

		self.source.auto_dump(AD=AD)

		if not copy:
			return self

		return ret





if __name__ == "__main__":

	import string
	def Lower_string(length): # define the function and pass the length as argument
		# Print the string in Lowercase
		result = ''.join((random.choice(string.ascii_lowercase) for x in range(length))) # run loop until the define length
		return result




	def test():
		st = time.perf_counter()
		tb = PickleTable("__test.pdb")
		tt = time.perf_counter()
		print(f"load time: {tt-st}s")

		print("Existing table height:", tb.height)

		tb.add_column("x", exist_ok=1, AD=False) # no dumps
		tb.add_column("Ysz", exist_ok=1, AD=False ) # no dumps
		tb.add_column("Y", exist_ok=1, AD=False) # no dumps

		print("adding")
		for n in range(int(100)):
			tb._add_row({"x":n, "Y":'🍎'})

			#print(n)

		tb.add_column("m", exist_ok=1, AD=False)  # no dumps

		print(tb["x"])
		dt = time.perf_counter()
		tb.dump()
		tt = time.perf_counter()
		print(f"⏱️ DUMP time: {tt-dt}s")

		dt = time.perf_counter()
		# col = tb.column_obj("x")
		# for i in range(10,20,2):
		# 	col.remove(i)

		tb.find_1st(20, column="x").set(1000)
		tt = time.perf_counter()
		print(f"⏱️ REMOVE time: {tt-dt}s")


		print(tb)
		#print("Total cells", tb.height * len(tb.column_names))

		et = time.perf_counter()
		print(f"Load and dump test in {et - st}s\n")

		print("="*50)

		print("\n Assign random string in first 1,000 rows test")
		print("="*50)

		tb.unlink()

		tb.clear()
		st = time.perf_counter()

		for _ in range(1000):
			tb.add_row(
				{
					"x": random.randint(1, 100),
					"m": Lower_string(100),
					"Y": "💪Hello🍎"
				}, AD=False)

		et = time.perf_counter()

		print(f"⏱️ Assigned test in {et - st}s")
		# print(tb)
		dt = time.perf_counter()
		tb.dump()
		tt = time.perf_counter()
		print(f"⏱️ DUMP time: {tt-dt}s")

		print("="*50)

		print("\n\n Search test")
		st = time.perf_counter()

		cells:list[_PickleTCell] = []

		for cell in tb.search_iter(kw="abc", column="m"):
			cells.append(cell.row_obj())

		et = time.perf_counter()

		print(f"⏱️🔍 Search 'abc' test in {et - st}s in {tb.height} rows")

		# for cell in cells:
		# 	print(cell.row_obj())
		print(tabulate(cells, headers="keys", tablefmt="simple_grid"))


		print("="*50)
		print("\n\n📝 TEST convert to CSV")
		st = time.perf_counter()
		tb.to_csv(f"test{st}.csv")
		et = time.perf_counter()
		print(f"⏱️ Convert to csv test in {et - st}s")
		os.remove(f"test{st}.csv")


		print("="*50)
		print("\n\n📝 TEST database clear")
		tb.clear()

		if tb.height != 0:
			raise Exception("❌ TEST [CLEAR]: Failed")

		print("✅ TEST [CLEAR]: Passed")


		print("="*50)
		print("\n\n📝 TEST after clear() meta values")
		print("Columns:", tb.column_names)
		print("Height:", tb.height)
		print("Table:")
		print(tb)

		if tb.height != 0:
			raise Exception("❌ TEST [CLEAR]: Failed")
		if not all(col in tb.column_names for col in ["x", "Y", "m"]):
			raise Exception("❌ TEST [CLEAR]: Failed (Columns mismatch)")

		print("✅ TEST [CLEAR]: Passed")


		print("="*50)
		print("\n\n📝 STR and REPR test")
		tb.clear()
		try:
			tb.add_row({"x":1, "Y":2, "Z":3})
			tb.add_row({"x":4, "Y":5, "Z":6})
			tb.add_row({"x":7, "Y":8, "Z":9})

			print("Row 1 STR:", tb.row_obj(0))
			print("Row 1 REPR:", repr(tb.row_obj(0)))

			print("Column Y STR:", tb.column_obj("Y"))
			print("Column Y REPR:", repr(tb.column_obj("Y")))

		except Exception as e:
			print("❌ TEST [STR and REPR]: Failed")
			raise e

		print("="*50)
		print("\n\n📝 Add test")

		# test adding a dict
		try:
			tb.add([1,2,3])
			raise Exception("❌ TEST [ADD] (Raise Exception Invalid type): Failed (Must raise error)")
		except TypeError as e:
			print(e) # must raise error
			print("✅ TEST [ADD] (Raise Exception Invalid type): Passed")
		except Exception as e:
			print("❌ TEST [ADD] (Raise Exception Invalid type): Failed")
			raise e


		try:
			tb.add({"x":[1,2,3], "Y":[4,5,6,7], "Z":[1,2,3]})
			raise Exception("❌ TEST [ADD dict] (Raise Exception extra column) (Must raise error)")
		except ValueError as e:
			print(e) # must raise error
			print("✅ TEST [ADD dict] (Raise Exception extra column) (P): Passed")
		except Exception as e:
			print("❌ TEST [ADD dict] (Raise Exception extra column) (F): Failed")
			raise e


		try:
			tb.add({"x":[1,2,3], "Y":[4,5,6,7]}, add_extra_columns=True)
			print("✅ TEST [ADD dict] (Add extra column): Passed")
		except Exception as e:
			print("❌ TEST [ADD dict] (Add extra column): Failed")
			raise e

		try:
			tb.add({"x":"[1,2,3]", "Y":[4,5,6,7]}, add_extra_columns=False)
			raise Exception("❌ TEST [ADD dict] (Raise Exception Invalid type): Failed (Must raise error)")
		except TypeError as e:
			print(e)
			print("✅ TEST [ADD dict] (Raise Exception Invalid type): Passed")
		except Exception as e:
			print("❌ TEST [ADD dict] (Raise Exception Invalid type): Failed")
			raise e

		print(tb)


		print("="*50)

		def _update_table(tb:PickleTable):
			tb.clear()

			tb.add_row({"x":7, "Y":8})
			tb.add_row({"x":3, "Y":4})
			tb.add_row({"x":1, "Y":2})
			tb.add_row({"x":5, "Y":6})


		print("\n\n📝 Sort test 1 (sort by x)")

		_update_table(tb)

		tb.sort("x")

		if tb.column("x") != [1, 3, 5, 7]:
			raise Exception("❌ TEST [SORT] (sort by x): Failed")

		print("✅ TEST [SORT] (sort by x): Passed")

		print("="*50)

		print("\n\n📝 Sort test 2 (sort by Y reverse)")
		_update_table(tb)

		tb.sort("Y", reverse=True)

		if tb.column("Y") != [8, 6, 4, 2]:
			raise Exception("❌ TEST [SORT] (sort by Y reverse): Failed")

		print("✅ TEST [SORT] (sort by Y reverse): Passed")

		print("="*50)

		print("\n\n📝 Sort test 3 (sort by key function) {x+y}")

		_update_table(tb)

		tb.sort(key=lambda x: x["x"]+x["Y"])


		tb.add_column("x+Y", exist_ok=True)

		print("📝 APPLYING COLUMN FUNCTION with row_func=True")
		try:
			tb["x+Y"].apply(func=lambda x: x["x"]+x["Y"], row_func=True)
			print("✅ TEST [APPLY] (row_func=True): Passed")
		except Exception as e:
			print("❌ TEST [APPLY] (row_func=True): Failed")
			raise e

		if tb.column("x+Y") != [3, 7, 11, 15]:
			raise Exception("❌ TEST [SORT] (sort by key function) {x+y}: Failed")

		print("✅ TEST [SORT] (sort by key function) {x+y}: Passed")

		print("="*50)

		print("\n\n📝 Sort test 4 (sort by key function) {x+y} (copy)")

		_update_table(tb)

		new_tb = tb.sort(key=lambda x: x["x"]+x["Y"], copy=True)

		if new_tb.column("x") != [1, 3, 5, 7]:
			raise Exception("❌ TEST [SORT] (sort by x): Failed")

		print("✅ TEST [SORT] (sort by x): Passed")

		print("="*50)

		print("\n\n📝 Remove duplicates test")

		tb.clear()

		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":2})
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":2})
		tb.add_row({"x":4, "Y":5})

		tb.remove_duplicates()

		if tb.height != 3:
			raise Exception("❌ TEST [REMOVE DUPLICATES]: Failed")

		print("✅ TEST [REMOVE DUPLICATES]: Passed")

		print("="*50)


		print("\n\n📝 Remove duplicates test [selective column]")

		tb.clear()

		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":2})
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":2})
		tb.add_row({"x":4, "Y":5})

		tb.remove_duplicates(columns="Y")

		if tb.height != 2:
			raise Exception("❌ TEST [REMOVE DUPLICATES]: Failed")

		print("✅ TEST [REMOVE DUPLICATES]: Passed")

		print("="*50)

		print("\n\n📝 Row deletion test")

		tb.clear()

		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":1, "Y":2})

		_tr = tb.row_obj(0)
		_tr.del_row()
		try:
			_tr["x"]
			raise Exception("❌ TEST [ROW DEL]: Failed")
		except ValueError as e:
			print("✅ TEST [ROW DEL]: Passed")
			print("Error message = ", e)

		print("="*50)

		print("\n\n📝 Column deletion test")

		tb.clear()

		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":1, "Y":2})

		_tc = tb.column_obj("x")
		_tc.del_column()
		try:
			_tc[0]
			raise Exception("❌ TEST [COL DEL]: Failed")
		except ValueError as e:
			print("✅ TEST [COL DEL]: Passed")
			print("Error message = ", e)

		tb.add_column("x", exist_ok=True) # bring back the column
		print("="*50)

		print("\n\n📝 Load csv test")

		tb.clear()

		print("Initial table")
		print(tb)
		print(tb.column_names)

		# make a csv file
		with open("test.csv", "w") as f:
			f.write("x,Y\n1,2\n3,4\n5,6\n")

		print("\t📝 Normal Load")
		try:
			tb.load_csv("test.csv")
		except Exception as e:
			print("❌ TEST [LOAD CSV]: Failed (Other error)")
			raise e
		if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD CSV]: Failed")

		print("\t✅ TEST [LOAD CSV][Normal Load]: Passed")

		print("\t📝 NoFile Load ['error']")
		# 1st error mode on file not found
		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="error")
			raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='error']: Failed")
		except FileNotFoundError as e:
			print("\t✅ TEST [LOAD CSV][NoFile Load]['error'][on_file_not_found='error']: Passed")
			print("\tError message = ", e)

		print("\t📝 NoFile Load ['ignore']")
		# 3rd error mode on file not found
		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="ignore")
			if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
				raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed")
			print("\t✅ TEST [LOAD CSV][NoFile Load]['ignore'][on_file_not_found='ignore']: Passed")

		except FileNotFoundError as e:
			print("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed (File not found)")
			raise e
		except Exception as e:
			print("\t❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed (Other error)")
			raise e



		print("\t📝 NoFile Load ['warn']")
		# 2nd error mode on file not found
		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="warn")
			if tb.height: # must be 0
				print(tb)
				raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='warn']: Failed")
			print("\t✅ TEST [LOAD CSV][NoFile Load]['warn'][on_file_not_found='warn']: Passed")

		except FileNotFoundError as e:
			print("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='warn']: Failed (File not found)")
			raise e
		except Exception as e:
			print("\t❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='warn']: Failed (Other error)")
			raise e


		print("\t📝 NoFile Load ['no_warning']")
		# 4th error mode on file not found
		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="no_warning")
			if tb.height: # must be 0
				raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='no_warning']: Failed")
			print("\t✅ TEST [LOAD CSV][NoFile Load]['no_warning'][on_file_not_found='no_warning']: Passed")

		except FileNotFoundError as e:
			print("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='no_warning']: Failed (File not found)")
			raise e
		except Exception as e:
			print("\t❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='no_warning']: Failed (Other error)")
			raise e

		os.remove("test.csv")


		print("\t📝 Header Load [header=True (use csv headers)]")
		# create a csv file with header
		with open("test.csv", "w") as f:
			f.write("x,Y\n1,2\n3,4\n5,6\n")

		tb.clear()
		tb.load_csv("test.csv", header=True)
		if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
			raise Exception("❌ TEST [LOAD CSV][Header Load][header=True]: Failed")

		print("\t✅ TEST [LOAD CSV][Header Load][header=True]: Passed")

		new_tb = PickleTable()
		print("\t📝 Header Load [header=True (use csv headers)] [new blank table]")
		new_tb.load_csv("test.csv", header=True)

		print(new_tb)


		print("\t📝 Header Load [header=False (use unnamed headers, Unnamed-1, Unnamed-2, ...)]")
		# create a csv file without header
		with open("test.csv", "w") as f:
			f.write("1,2\n3,4\n5,6\n")

		tb.clear()
		tb.load_csv("test.csv", header=False)

		print(tb)
		if tb.height != 3 or tb.column("Unnamed-5") != ['1', '3', '5']:
			raise Exception("❌TEST [LOAD CSV][Header Load][header=False]: Failed")

		print("\t✅ TEST [LOAD CSV][Header Load][header=False]: Passed")

		print('\t📝 Header Load [header="auto" (use auto headers, A, B, C, ...)]')

		tb.clear()

		tb.load_csv("test.csv", header="auto")

		print(tb)

		if tb.height != 3 or tb.column("H") != ['1', '3', '5']:
			raise Exception("❌ TEST [LOAD CSV][Header Load][header='auto']: Failed")

		print("\t✅ TEST [LOAD CSV][Header Load][header='auto']: Passed")

		os.remove("test.csv")

		print("="*50)














# if __name__ == "__main__":
	for i in range(1):
		try:
			os.remove("__test.pdb")
		except:
			pass
		test()
		os.remove("__test.pdb")
		print("\n\n\n" + "# "*25 + "\n")
