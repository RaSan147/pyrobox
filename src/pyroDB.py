#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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

from typing import Generator, Union

from tabulate import tabulate
import msgpack

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

	def rescan(self):
		"""
		Rescan the file for changes
		"""
		if self.in_memory:
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

	def load(self, location, auto_dump):
		"""
		Loads, reloads or Changes the path to the db file
		"""
		self.in_memory = False

		self.location = self._fix_location(location)

		self.auto_dump = auto_dump
		if os.path.exists(location):
			self._loaddb()
		else:
			self.new()
		return True

	def set_location(self, location):
		self.location = location
		self.in_memory = False

	def _dump(self):
		"""
		Dump to a temporary file, and then move to the actual location
		"""
		if self.in_memory:
			return

		logger.info("--dumping--")
		with NamedTemporaryFile(mode='wb', delete=False) as f:
			msgpack.dump(self.db, f)
		if os.stat(f.name).st_size != 0:
			shutil.move(f.name, self.location)

		self.m_time = os.stat(self.location).st_mtime

	def dump(self):
		"""
		Force dump memory db to file
		"""

		if self.in_memory:
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
		try:
			with open(self.location, 'rb') as f:
				db = msgpack.load(f)
				self.db:dict = db
		except ValueError:
			if os.stat(self.location).st_size == 0:  # Error raised because file is empty
				self.new()
			else:
				raise  # File is not empty, avoid overwriting it

	def _autodumpdb(self):
		"""
		Write/save the json dump into the file if auto_dump is enabled
		"""
		if self.auto_dump:
			self.dump()


	def validate_key(self, key):
		"""Make sure key is a string
		msgpack is optimized for string keys, so we need to make sure"""

		if not isinstance(key, (str, bytes)):
			raise self.key_string_error

	def set(self, key, value):
		"""
		Set the str value of a key
		"""
		self.rescan()
		self.validate_key(key)

		self.db[key] = value
		self._autodumpdb()
		return True


	def get(self, *keys, default=None, raiseErr=False):
		"""
		Get the value of a key or keys
		keys work as multidimensional

		keys: dimensional key sequence. if object is dict, key must be string (to fix JSON bug)

		default: act as the default, same as dict.get
		raiseErr: raise Error if key is not found, same as dict[unknown_key]
		"""
		key = keys[0]
		self.rescan()
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


	def keys(self):
		"""
		Return a list of all keys in db
		"""
		self.rescan()
		return self.db.keys()

	def items(self):
		"""same as dict.items()"""
		self.rescan()
		for i,j in self.db.items():
			yield i,j

	def exists(self, key):
		"""
		Return True if key exists in db, return False if not
		"""
		self.rescan()
		return key in self.db

	def rem(self, key):
		"""
		Delete a key
		"""
		self.rescan()
		if not key in self.db: # return False instead of an exception
			return False
		del self.db[key]
		self._autodumpdb()
		return True

	def append(self, key, more):
		"""
		Add more to a key's value
		"""
		self.rescan()
		tmp = self.db[key]
		self.db[key] = tmp + more
		self._autodumpdb()
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

	def rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""
		if rescan:
			self._pk.rescan()

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

	def extend(self, other: "PickleTable"):
		"""
		Extend the table with another table
		## args:
		- other: PickleTable object
		"""
		if other is None:
			return

		if not isinstance(other, type(self)):
			raise TypeError("Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(other).__name__))

		if sorted(self.column_names) != sorted(other.column_names):
			raise ValueError("Both tables must have same column names")

		for row in other:
			self._add_row(row)

		self.auto_dump()


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
		h = len(self._pk[self.column_names[0]]) if self.column_names else 0

		return h

	def __str__(self, limit=None):
		"""
		Return a string representation of the table
		- Default only first 50 rows are shown
		- use `limit` to override the number of rows
		"""
		self.rescan()
		limit = limit or self.str_limit
		x = tabulate(
			self[:min(self.height, limit)], 
			headers="keys", 
			tablefmt= "simple_grid",
			#"orgtbl",
			maxcolwidths=60
			)
		if self.height > limit:
			x += "\n..."

		return x

	def str(self, limit=None):
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

	def column(self, name) -> list:
		"""
		Return a copy list of all values in column
		"""
		self.rescan()
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

	def columns(self):
		"""
		Return a **copy list** of all columns in db
		"""
		self.rescan()
		return self._pk.db.copy()

	def columns_obj(self):
		"""
		Return a list of all columns in db
		"""
		self.rescan()
		return [_PickleTColumn(self, name, self.CC) for name in self._pk.db]

	@property
	def column_names(self):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self.rescan()
		return tuple(self._pk.db.keys())

	def keys(self):
		"""
		Return a list of all keys in db
		"""
		self.rescan()
		return self._pk.keys()

	def values(self):
		"""
		Return a list of all values in db
		"""
		self.rescan()
		return self._pk.values()

	def items(self):
		"""
		Return a list of all items in db
		"""
		self.rescan()
		return self._pk.items()

	def add_column(self, *names, exist_ok=False, AD=True):
		"""
		name: column name
		exist_ok: ignore if column already exists. Else raise KeyError
		AD: auto-dump
		"""
		self.rescan()
		def add(name):
			self._pk.validate_key(key=name)

			tsize = self.height
			if name in self.column_names:
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

		if isinstance(names[0], Iterable) and not isinstance(names[0], str) and not isinstance(names[0], bytes) and len(names) == 1:
			names = names[0]

		for name in names:
			add(name)


		self.auto_dump(AD=AD)

	add_columns = add_column # alias


	def del_column(self, name, AD=True):
		"""
		@ locked
		# name: column to delete
		# AD: auto dump
		"""
		self.rescan()
		self.lock(self._pk.db.pop)(name)
		if not self._pk.db: # has no keys
			self.height = 0

		# self.gen_CC()

		self.auto_dump(AD=AD)



	def row(self, row, _columns=()):
		"""
		returns a row dict by `row` index
		_column: specify columns you need, blank if you need all
		"""
		self.rescan()

		columns = _columns or self.column_names
		return {j: self._pk.db[j][row] for j in columns}

	def row_by_id(self, row_id, _columns=()):
		"""
		returns a row dict by `row_id`
		_column: specify columns you need, blank if you need all
		"""
		return self.row(self.ids.index(row_id), _columns=_columns)

	def row_obj(self, row):
		"""Return a row object `_PickleTRow` in db
		# row: row index
		"""
		return _PickleTRow(source=self,
			uid=self.ids[row],
			CC=self.CC)

	def row_obj_by_id(self, row_id):
		"""Return a row object `_PickleTRow` in db
		# row: row index
		"""
		return _PickleTRow(source=self,
			uid=row_id,
			CC=self.CC)

	def rows(self, start:int=0, end:int=None, sep:int=1):
		"""Return a list of all rows in db"""
		self.rescan()

		if end is None:
			end = self.height
		if end<0:
			end = self.height + end

		ids = self.ids[start:end:sep]

		for id in ids:
			yield self.row_by_id(id)

	def rows_obj(self, start:int=0, end:int=None, sep:int=1):
		"""Return a list of all rows in db"""
		if end is None:
			end = self.height
		if end<0:
			end = self.height + end


		ids = self.ids[start:end:sep]

		for id in ids:
			yield self.row_obj_by_id(id)

	def search_iter(self, kw, column=None , row=None, full_match=False, return_obj=True) -> Generator["_PickleTCell", None, None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the cell object in loop

		ie: for cell in db.search_iter("abc"):
			print(cell.value)
		"""
		self.rescan()

		if return_obj:
			ret = self.get_cell_obj
		else:
			ret = self.get_cell

		def check(item, is_in):
			if full_match or not isinstance(is_in, Iterable):
				return is_in == item

			return item in is_in


		if column and row:
			cell = self.get_cell(column, row)
			if check(kw, cell):
				yield ret(col=column, row=row)
			return None

		elif column:
			for r, i in enumerate(self.column(column)):
				if check(kw, i):
					yield ret(col=column, row=r)

			return None

		elif row:
			_row = self.row(row)
			for c, i in _row.items():
				if check(kw, i):
					yield ret(col=c, row=row)

			return None

		else:
			for col in self.column_names:
				for r, i in enumerate(self.column(col)):
					if check(kw, i):
						yield ret(col=col, row=r)


	def find_1st(self, kw, column=None , row=None, full_match=False, return_obj=True) -> Union["_PickleTCell", None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the 1st matched cell object
		"""
		if column and column not in self.column_names:
			raise KeyError("Invalid column name:", column)

		for cell in self.search_iter(kw, column=column , row=row, full_match=full_match, return_obj=return_obj):
			return cell
		
	def find_1st_row(self, kw, column=None , row=None, full_match=False, return_obj=True) -> Union["_PickleTRow", None]:
		"""
		search a keyword in a cell/row/column/entire sheet and return the 1st matched row object
		"""
		if column and column not in self.column_names:
			raise KeyError("Invalid column name:", column)

		for cell in self.search_iter(kw, column=column , row=row, full_match=full_match, return_obj=True):
			return cell.row_obj() if return_obj else cell.row






	def set_cell(self, col, row, val, AD=True, rescan=True):
		"""
		# col: column name
		# row: row index
		# val: value of cell
		# AD: auto dump
		"""
		self.rescan(rescan)

		self._pk.db[col][row] = val

		self.auto_dump(AD=AD)

	def set_cell_by_id(self, col, row_id, val, AD=True):
		"""
		# col: column name
		# row_id: unique row id
		# val: value of cell
		# AD: auto dump
		"""
		return self.set_cell(col=col, row=self.ids.index(row_id), val=val, AD=AD)

	def get_cell(self, col, row):
		"""
		get cell value
		"""
		self.rescan()

		return self._pk.db[col][row]

	def get_cell_by_id(self, col, row_id):
		return self.get_cell(col, self.ids.index(row_id))

	def get_cell_obj(self, col, row:int=-1, row_id:int=-1):
		"""
		return cell object
		# col: column name
		# row: row index (use euther row or row_id)
		# row_id: unique id of the row
		"""

		if row>-1:
			return _PickleTCell(self, column=col, row_id=self.ids[row], CC=self.CC)
		if row_id>-1:
			return _PickleTCell(self, column=col, row_id=self.ids[row], CC=self.CC)

		# in case row or row_id is invalid
		raise IndexError("Invalid row")


	def pop_row(self, index:int=-1, returns=True, AD=True):
		"""
		index: index of the row (not id), if not given, last row of the table is popped
		returns: whether return the popped row. (how pop should work)
		"""
		self.rescan()

		box = None
		if returns:
			box = self.row(index)

		for c in self.column_names:
			self._pk.db[c].pop(index)

		self.ids.pop(index)

		self.height -=1

		self.auto_dump(AD=AD)

		return box

	def del_row(self, row:int, AD=True):
		# Auto dumps (locked)
		self.lock(self.pop_row)(row, returns=False, AD=AD)



	def del_row_id(self, row_id:int, AD=True):
		"""
		row_id: unique id of the row
		AD: auto dump
		"""
		self.del_row(self.ids.index(row_id), AD=AD)

	def clear(self, AD=True):
		"""
		Delete all rows

		AD: auto dump
		"""
		self.rescan()

		for c in self.column_names:
			self._pk.db[c].clear()

		self.ids.clear()
		self.height = 0

		self.auto_dump(AD=AD)


	def copy(self, location=None, auto_dump=True, sig=True):
		"""
		Copy the table to a new location
		"""
		
		new = PickleTable(location, auto_dump=auto_dump, sig=sig)
		new.add_column(*self.column_names)
		new.__db__ = datacopy.deepcopy(self.__db__)
		new.height = self.height
		new.ids = self.ids.copy()

		return new




	def _add_row(self, row:Union[dict, "_PickleTRow"], position:int="last") -> "_PickleTRow":
		"""
		# row: row must be a dict or _PickleTRow containing column names and values
		"""
		self.rescan()


		if not self.ids:
			row_id = 0
		else:
			row_id = self.ids[-1] + 1


		if isinstance(position, int):
			for k in self.column_names:
				self._pk.db[k].insert(position, row.get(k))
			self.ids.insert(position, row_id)

		else:
			for k in self.column_names:
				self._pk.db[k].append(row.get(k))
			self.ids.append(row_id)


		#for k, v in row.items():
		#	self.set_cell(k, self.height, v, AD=False)

		self.height += 1

		return self.row_obj_by_id(row_id)


	def add_row(self, row:Union[dict, "_PickleTRow"], position="last", AD=True) -> "_PickleTRow":
		"""
		@ locked
		* row: row must be a dict|TableRow containing column names and values
		"""

		row_obj = self.lock(self._add_row)(row=row,position=position)

		self.auto_dump(AD=AD)

		return row_obj


	def insert_row(self, row:Union[dict, "_PickleTRow"], position:int, AD=True) -> "_PickleTRow":
		"""
		@ locked
		* row: row must be a dict|_PickleTRow containing column names and values
		"""

		return self.add_row(row=row, position=position, AD=AD)




	def add_row_as_list(self, row:list, position:int="last", AD=True) -> "_PickleTRow":
		"""
		@ locked
		* row: row must be a list containing values
		"""

		row_obj = self.lock(self._add_row)(row={k:v for k, v in zip(self.column_names, row)}, position=position)

		self.auto_dump(AD=AD)

		return row_obj


	def verify_source(self, CC):
		return CC == self.CC

	def raise_source(self, CC):
		if not self.verify_source(CC):
			raise KeyError("Database has been updated drastically. Row index will mismatch!")



	def dump(self):
		self._pk.dump()

	def auto_dump(self, AD=True):
		if AD:
			self._pk._autodumpdb()


	def to_csv(self, filename=None, write_header=True):
		"""
		Write the table to a csv file
		* filename: path to the file (if None, use current filename.csv) (if in memory, use "table.csv")
		* write_header: write column names as header
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
		with open(path, "w", newline='', encoding='utf8') as f:
			writer = csv.writer(f)
			if write_header:
				writer.writerow(self.column_names) # header
			for row in self.rows():
				writer.writerow([row[k] for k in self.column_names])

	def to_csv_str(self, write_header=True):
		"""
		Return the table as a csv string
		* write_header: write column names as header
		"""
		output = io.StringIO()
		writer = csv.writer(output)
		if write_header:
			writer.writerow(self.column_names)
		for row in self.rows():
			writer.writerow([row[k] for k in self.column_names])

		return output.getvalue()

	def load_csv(self, filename, header=True, ignore_none=False, AD=True):
		"""
		Load a csv file to the table
		* WILL OVERWRITE THE EXISTING DATA
		* header: 
			* if True, the first row will be considered as column names
			* if False, the columns will be named as "Unnamed-1", "Unnamed-2", ...
			* if "auto", the columns will be named as "A", "B", "C", ..., "Z", "AA", "AB", ...
		* ignore_none: ignore the None rows
		"""
		def add_row(row):
			if ignore_none and all(v is None for v in row):
				return

			self.add_row({k: v for k, v in zip(self.column_names, row)}, AD=False)
		with open(filename, 'r', encoding='utf8') as f:
			reader = csv.reader(f)
			if header is True:
				columns = next(reader)
				updated_columns = []
				for col in columns:
					if col is None:
						col = f"Unnamed-{len(updated_columns)+1}"
					updated_columns.append(col)
				self.add_column(updated_columns, exist_ok=True, AD=False)

			elif isinstance(header, str) and header.lower() == "auto":
				row = next(reader)
				columns = [_int_to_alpha(i) for i in range(len(row))]
				
				self.add_column(columns, exist_ok=True, AD=False)		
				add_row(row)
			else:
				columns = self.column_names

			for row in reader:
				add_row(row)

	def add(self, table:Union["PickleTable", dict], add_columns=False, AD=True):
		"""
		Add another table to this table
		"""
		if isinstance(table, dict) or isinstance(table, type(self)):
			keys = table.keys()
		else:
			raise TypeError("Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(table).__name__))

		if add_columns:
			self.add_column(*keys, exist_ok=True, AD=False)
		elif any(k not in self.column_names for k in keys):
			raise ValueError("Both tables must have same column names")

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
			self.extend(table)
				
		self.auto_dump(AD=AD)




class _PickleTCell:
	def __init__(self, source:PickleTable, column, row_id:int, CC):
		self.source = source
		self.id = row_id
		self.column_name = column
		self.CC = CC

	@property
	def value(self):
		self.source_check()

		return self.source.get_cell_by_id(self.column_name, self.id)

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
	def row(self):
		self.source_check()

		return self.source.ids.index(self.id)

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
		self.id = uid
		self.CC = CC

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
		return {k: self[k] for k in self.source.column_names}

	def get(self, name, default=None):
		if name not in self.source.column_names:
			return default

		return self[name]

	def get_cell_obj(self, name, default=None):
		if name not in self.source.column_names:
			return default

		return self.source.get_cell_obj(col=name, row_id=self.id)

	def __setitem__(self, name, value):
		# Auto dumps
		self.source.raise_source(self.CC)

		self.source.set_cell(name, self.source.ids.index(self.id), value)

	def __delitem__(self, name):
		# Auto dump
		self.source.raise_source(self.CC)

		self.source.set_cell(name, self.source.ids.index(self.id), None)

	def index(self):
		"""
		returns the current index of the row
		"""
		return self.source.ids.index(self.id)

	def update(self, new:Union[dict, "_PickleTRow"], ignore_extra=False, AD=True):
		"""
		Auto dumps
		"""

		for k, v in new.items():
			try:
				self.source.set_cell(k, self.source.ids.index(self.id), v, AD=False)
			except KeyError:
				if not ignore_extra:
					raise

		self.source.auto_dump(AD=AD)

	def __str__(self):
		return str({k:v for k, v in self.items()})

	def keys(self):
		return self.source.column_names

	def values(self):
		return [self[k] for k in self.keys()]

	def items_iter(self):
		for k in self.keys():
			yield (k, self[k])

	def items(self):
		return list(self.items_iter())

	def del_row(self):
		"""
		Delete the row
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		# Auto dumps
		self.source.raise_source(self.CC)

		self.source.del_row_id(self.id)

	def __eq__(self, other):
		try:
			for k in self.source.column_names:
				if self[k] != other[k]:
					return False
			return True
		except KeyError:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)
		


class _PickleTColumn(list):
	def __init__(self, source:PickleTable, name, CC):
		self.source = source
		self.name = name
		self.CC = CC

	def __getitem__(self, row:Union[int, slice]):
		"""
		row: the index of row (not id)
		"""
		# self.source.raise_source(self.CC)
		if isinstance(row, int):
			return self.source.get_cell(col=self.name, row=row)
		elif isinstance(row, slice):
			return [self.source.get_cell(col=self.name, row=i) for i in range(*row.indices(self.source.height))]
		else:
			raise TypeError("indices must be integers or slices, not {}".format(type(row).__name__))

	def __len__(self) -> int:
		return self.source.height

	def get(self, row:int, default=None):
		"""
		get the cell value from the column by row index
		"""
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self[row]

	def get_cell_obj(self, row:int, default=None):
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self.source.get_cell_obj(col=self.name, row=row)

	def __setitem__(self, row:int, value):
		"""
		@ Auto dumps
		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		"""

		# self.source.raise_source(self.CC)

		if isinstance(value, _PickleTCell):
			value = value.value

		self.source.set_cell(col=self.name, row=row, val=value)

	def __delitem__(self, row:int):
		"""
		@ Auto dump
		* row: index of row (not id)
		"""
		self.source.set_cell(self.name, row, None)

	def __iter__(self):
		return self.get_cells_obj()

	def get_cells_obj(self, start:int=0, end:int=None, sep:int=1):
		"""Return a list of all rows in db"""
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

	def remove(self, value, n_times=1):
		"""
		@ Auto dumps
		- This will remove the occurrences of the value in the column (from top to bottom)
		- n_times: number of occurrences to remove (0: all)
		"""
		for i in self:
			if i == value:
				i.clear()
				n_times -= 1
				if n_times==0:
					break



	def clear(self) -> None:
		"""
		@ Auto dumps
		# This will Set all cells in column to `None`
		"""

		self.source.raise_source(self.CC)
		self.source.rescan()

		for row in range(self.source.height):
			self.source.set_cell(col=self.name, row=row, val=None, AD=False, rescan=False)

		self.source.auto_dump()



	def __str__(self):
		return str(self.source.get_column(self.name))

	def del_column(self):
		"""
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		self.source.raise_source(self.CC)

		self.source.del_column(self.name)


	def apply(self, func):
		"""
		Apply a function to all cells in the column
		"""
		for i in range(self.source.height):
			self[i] = func(self[i])





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
		print(f"dump time: {tt-dt}s")

		dt = time.perf_counter()
		# col = tb.column_obj("x")
		# for i in range(10,20,2):
		# 	col.remove(i)

		tb.find_1st(20, column="x").set(1000)
		tt = time.perf_counter()
		print(f"remove time: {tt-dt}s")


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

		print(f"Assigned test in {et - st}s")
		# print(tb)
		dt = time.perf_counter()
		tb.dump()
		tt = time.perf_counter()
		print(f"dump time: {tt-dt}s")

		print("="*50)

		print("\n\n Search test")
		st = time.perf_counter()

		cells:list[_PickleTCell] = []

		for cell in tb.search_iter(kw="abc", column="m"):
			cells.append(cell.row_obj())

		et = time.perf_counter()

		print(f"Search 'abc' test in {et - st}s in {tb.height} rows")

		# for cell in cells:
		# 	print(cell.row_obj())
		print(tabulate(cells, headers="keys", tablefmt="simple_grid"))

		tb.to_csv("test.csv")


		print("="*50)
		print("\n\n Clear test")
		tb.clear()
		print("Columns:", tb.column_names)
		print("Height:", tb.height)
		print("Table:")
		print(tb)


		print("="*50)
		print("\n\n Add test")

		# test adding a dict
		try:
			tb.add([1,2,3])
			raise Exception("Must raise error")
		except TypeError as e:
			print(e) # must raise error
			print("TEST [ADD] (Raise Exception Invalid type): Passed")
		except Exception as e:
			print("TEST [ADD] (Raise Exception Invalid type): Failed")
			raise e
			

		try:
			tb.add({"x":[1,2,3], "Y":[4,5,6,7], "Z":[1,2,3]})
			raise Exception("Must raise error")
		except ValueError as e:
			print(e) # must raise error
			print("TEST [ADD dict] (Raise Exception extra column) (P): Passed")
		except Exception as e:
			print("TEST [ADD dict] (Raise Exception extra column) (F): Failed")
			raise e

		
		try:
			tb.add({"x":[1,2,3], "Y":[4,5,6,7]}, add_columns=True)
			print("TEST [ADD dict] (Add extra column): Passed")
		except Exception as e:
			print("TEST [ADD dict] (Add extra column): Failed")
			raise e

		try:
			tb.add({"x":"[1,2,3]", "Y":[4,5,6,7]}, add_columns=False)
			raise Exception("Must raise error")
		except TypeError as e:
			print(e)
			print("TEST [ADD dict] (Raise Exception Invalid type): Passed")
		except Exception as e:
			print("TEST [ADD dict] (Raise Exception Invalid type): Failed")
			raise e

		print(tb)


# if __name__ == "__main__":
	for i in range(1):
		try:
			os.remove("__test.pdb")
		except:
			pass
		test()
		os.remove("__test.pdb")
		print("\n\n\n" + "# "*25 + "\n")
