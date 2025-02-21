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
import json
import os
import signal
import atexit
import shutil
from collections.abc import Iterable
from concurrent.futures import Future
from queue import Queue
import sys
import time
import random
from tempfile import NamedTemporaryFile
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
	# Check if msgpack is installed

	# Check if GIL is enabled (Now available in msgpack-1.1.0-cp313-cp313t-win_amd64.whl)
	if not getattr(sys, '_is_gil_enabled', lambda: True)():
		os.environ["MSGPACK_PUREPYTHON"] = "1"
		# msgpack is not thread safe (yet)
		
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


class TaskExecutor:
	"""
	A thread-safe task execution queue that ensures tasks are executed sequentially 
	and allows retrieving return values or raising exceptions as if they were 
	executed normally.
	"""
	
	def __init__(self):
		"""Initialize the task queue and set the executor to idle."""
		self.__TASKS = Queue()  # Queue to store tasks
		self.busy = False       # Flag to indicate if a task is currently running
		self.active_future = None  # Future object of the currently running task

	def __next_task(self):
		"""
		Executes the next task in the queue.
		
		- Retrieves the next task from the queue.
		- Executes it and stores the result or raises an exception.
		- Marks the task as completed.
		- Calls itself recursively to process the next task (if any).
		"""
		if self.busy:
			return
		while not self.__TASKS.empty():
			self.busy = True  # Mark as busy

			# Retrieve the next task (function, args, kwargs, future object)
			func, args, kwargs, future = self.__TASKS.get(timeout=0.1)
			self.active_future = future

			try:
				# Execute the function and store the result
				result = func(*args, **kwargs)
				# future.put(result)  # Store result in future
				future.set_result(result)
			except Exception as e:
				# If an exception occurs, store it in the future
				# future.put(e)
				print(traceback.format_exc())
				future.set_exception(e)
			finally:
				# Mark the task as done in the queue
				self.__TASKS.task_done()
				
				# Mark executor as idle and trigger the next task
				self.busy = False
				self.active_future = None

	def lock(self, func, *args, **kwargs):
		"""
		Adds a function to the task queue and waits for its result.
		
		- If the function executes successfully, returns the result.
		- If the function raises an error, it propagates the exception.
		
		Args:
			func (callable): The function to execute.
			*args: Positional arguments for the function.
			**kwargs: Keyword arguments for the function.

		Returns:
			Any: The return value of the function.

		Raises:
			Exception: Any exception raised by the function.
		"""
		# future = Queue()  # Create a Future object to store result or exception
		future = Future()
		self.__TASKS.put((func, args, kwargs, future))  # Add task to queue
		self.__next_task()  # Start executing tasks if not already running

		# result = future.get()  # Wait for and return the function's result
		result = future.result()


		# if isinstance(result, Exception):
		# 	raise result

		return result


class PickleDB(object):

	key_string_error = TypeError('Key/name must be a string!')

	def __init__(self, location="", auto_dump=True, sig=True, *args, **kwargs):
		"""Creates a database object and loads the data from the location path.
		If the file does not exist it will be created on the first update.
		"""
		self.task_executor = TaskExecutor()


		self.db = {}

		self.in_memory = False
		self.location = ""
		if location:
			self.load(location, auto_dump)
		else:
			self.in_memory = True

		self.m_time = 0

		self.auto_dump = auto_dump

		self.sig = sig
		if sig:
			self.set_sigterm_handler()

		self._autodumpdb()

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

	
	def threadsafe_decorator(func):
		"""
		Decorator for thread safe functions
		"""
		# check if the func stack is already locked
		# if not, lock it, else return the function
		

		def wrapper(self:"PickleTable", *args, **kwargs):
			return self.task_executor.lock(func, self, *args, **kwargs)

		# def wrapper(self, *args, **kwargs):
		# 	return func(self, *args, **kwargs)
		return wrapper



	def set_sigterm_handler(self):
		"""
		Assigns sigterm_handler for graceful shutdown during dump()
		"""
		def sigterm_handler(*args, **kwargs):
			if self.task_executor.active_future:
				self.task_executor.active_future.result()
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

	@threadsafe_decorator
	def rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""

		if self.in_memory or not rescan:
			return
		if os.path.exists(self.location):
			m_time = os.stat(self.location).st_mtime
			# print("⏰", "OWN:", self.m_time, "NEW:", m_time)
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

	@threadsafe_decorator
	def dump(self, filepath=None):
		"""
		Dump to a temporary file, and then move to the actual location
		"""
		save_own = True
		if filepath and filepath != self.location:
			save_own = False

		savepath = filepath or self.location
		
		if not SAVE_LOAD or self.in_memory or savepath is None:
			return self.in_memory # return False if not saved

		db = self.db
		# make a copy of the db if not saving to own location
		if not save_own:
			db = datacopy.deepcopy(self.db)
			


		logger.info("--dumping--")
		with NamedTemporaryFile(mode='wb', delete=False) as f:
			try:
				msgpack.dump(db, f)
			except Exception as e:
				logger.error("Error while dumping to temp file: %s", e)
				logger.error("Location: %s, (to be moved to %s)", f.name, savepath)

				raise e

		if os.stat(f.name).st_size != 0:
			shutil.move(f.name, savepath)

		if save_own:
			self.m_time = os.stat(savepath).st_mtime

	# save = PROXY OF SELF.DUMP()
	save = dump

	def _loaddb(self):
		"""
		Load or reload the json info from the file
		"""
		if not SAVE_LOAD:
			logger.warning("msgpack not found, install it using `pip install msgpack`\n * Only in-memory db will work")
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
		"""Make sure key is a string|bytes
		msgpack is optimized for string|bytes keys, so we need to make sure"""

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
	def __init__(self, filepath="", *args, **kwargs):
		"""
		args:
		- filepath: path to the db file (default: `""` or in-memory db)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- always_rescan: always rescan the file for changes (default: `False`)
		"""
		self.CC = 0 # consider it as country code and every items are its people. they gets NID


		self.gen_CC()


		self._pk = PickleDB(location=filepath, *args, **kwargs)

		self.always_rescan = kwargs.get("always_rescan", False)

		# make the super dict = self._pk.db
		self.busy = False
		self.task_executor = TaskExecutor()



		self.height = self.get_height()

		self.ids = [h for h in range(self.height)]

		# DEFAULR LIMIT FOR STR conversion
		self.str_limit = 50

	def threadsafe_decorator(func):
		"""
		Decorator for thread safe functions
		"""
		def wrapper(self:"PickleTable", *args, **kwargs):
			return self.task_executor.lock(func, self, *args, **kwargs)
		return wrapper

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

	@threadsafe_decorator
	def to_list(self, rescan=True):
		"""
		Return a list of all rows
		"""
		self.rescan(rescan=rescan)
		col_names = list(self.column_names_func(rescan=False))
		return [col_names] + [
			[self._pk.db[col][i] for col in col_names]
			for i in range(self.height)
		]

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

	@threadsafe_decorator
	def get_height(self):
		"""
		Return the number of rows
		"""
		self.rescan()
		columns = self._column_names_func(rescan=False)
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
				x += "\t|\t".join([str(cell) if cell is not None else '' for cell in self.row(i, rescan=False).values()])

		else:				
			x = tabulate(
				# self[:min(self.height, limit)], 
				self.rows(start=0, end=min(self.height, limit), rescan=False),
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

	@threadsafe_decorator
	def column(self, name, rescan=True) -> list:
		"""
		Return a copy list of all values in column
		"""
		self.rescan(rescan=rescan)
		return self._pk.db[name].copy()
	
	@threadsafe_decorator
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

	@threadsafe_decorator
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

	def _column_names_func(self, rescan=True):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self.rescan(rescan=rescan)
		return tuple(self._pk.db.keys())

	@threadsafe_decorator
	def column_names_func(self, rescan=True):
		"""
		return a tuple (unmodifiable) of column names
		"""
		return self._column_names_func(rescan=rescan)

	@property
	@threadsafe_decorator
	def column_names(self):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self.rescan()
		return tuple(self._pk.db.keys())

	@threadsafe_decorator
	def keys(self, rescan=True):
		"""
		Return a list of all keys in db
		"""
		return self._pk.keys(rescan=rescan)

	@threadsafe_decorator
	def values(self, rescan=True):
		"""
		Return a list of all values in db
		"""
		return self._pk.values(rescan=rescan)

	@threadsafe_decorator
	def items(self, rescan=True):
		"""
		Return a list of all items in db
		"""
		return self._pk.items(rescan=rescan)

	def add_column(self, *names, exist_ok=False, AD=True, rescan=True):
		"""
		- name: name|_PickleTColumn or list of names|_PickleTColumn
		- exist_ok: 
		- - =False then raise KeyError if column already exists
		- - =True then `if name` ignore if column already exists. Else raise KeyError
		- - =True then`if _PickleTColumn` if column already exists, 
		- - - exist_ok=True:  ignore if column already exists. (Only checks/add for name, doesn't copy the column)
		- - - exist_ok="name": ignore if column already exists. (Only checks/add for name, doesn't copy the column)
		- - - exist_ok="overwrite": overwrite it (may add new rows in table if column size is higher)(may add None in column if column size is lower)
		- AD: auto-dump
		"""
		self.rescan(rescan=rescan)

		def add(data):
			if isinstance(data, _PickleTColumn):
				name = data.name
				self._pk.validate_key(key=name)

				col = data.to_list()

				tsize = self.height
				csize = len(col)
				diff = tsize - csize

				if name in self.column_names_func(rescan=False):
					if exist_ok == True or exist_ok == "name":
						pass
					elif exist_ok == "overwrite":
						if diff > 0:
							col.extend([None] * diff)
						elif diff < 0:
							# we need to add more rows
							for _ in range(abs(diff)):
								self.add_row({}, AD=False, rescan=False)

						self._pk.db[name] = col

					else:
						raise KeyError("Column Name already exists")

			else:
				name = data

				self._pk.validate_key(key=name)

				tsize = self.height
				if name in self._pk.db:
					if exist_ok==True:
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
		if (isinstance(names[0], Iterable) 
			and not isinstance(names[0], str) 
			and not isinstance(names[0], bytes) 
			and not isinstance(names[0], _PickleTColumn)
			and len(names) == 1
			):
			names = names[0]

		for name in names:
			add(name)


		self.auto_dump(AD=AD)

	add_columns = add_column # alias

	@threadsafe_decorator
	def del_column(self, name, AD=True, rescan=True):
		"""
		@ locked
		# name: column to delete
		# AD: auto dump
		"""
		self.rescan(rescan=rescan)
		self._pk.db.pop(name)
		if not self._pk.db: # has no keys
			self.height = 0

		# self.gen_CC()

		self.auto_dump(AD=AD)


	def _row(self, row, _columns=(), rescan=True):
		"""
		returns a row dict by `row index`

		- row: row index
		- _columns: specify columns you need, blank if you need all
		"""
		self.rescan(rescan=rescan)

		columns = _columns or self._column_names_func(rescan=False)
		try:
			return {j: self._pk.db[j][row] for j in columns}
		except IndexError:
			raise IndexError("Row index out of range, [expected: 0 to", self.height, "] [got:", row, "]")

	
	@threadsafe_decorator
	def row(self, row, _columns=(), rescan=True):
		"""
		@ locked

		returns a row dict by `row index`
		- row: row index
		- _columns: specify columns you need, blank if you need all
		"""
		return self._row(row, _columns=_columns, rescan=rescan)

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
		- loop_back: loop back support (circular indexing)
		"""
		if loop_back:
			row = row % self.height
		return _PickleTRow(source=self,
			uid=self.ids[row],
			CC=self.CC)

	def row_obj_by_id(self, row_id):
		"""Return a row object `_PickleTRow` in db
		- row_id: row id
		"""
		return _PickleTRow(source=self,
			uid=row_id,
			CC=self.CC)

	def rows(self, start:int=0, end:int=None, sep:int=1, loop_back=False, rescan=True) -> Generator[dict, None, None]:
		"""Return a list of all rows in db
		- start: start index (default: 0)
		- end: end index (default: None|end of the table)
		- sep: step size (default: 1)
		- loop_back: loop back support (circular indexing)

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
		- loop_back: loop back support (circular indexing)
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


	def _set_cell(self, col, row, val, AD=True, rescan=True) -> bool:
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

		return True

	@threadsafe_decorator
	def set_cell(self, col, row, val, AD=True, rescan=True) -> bool:
		"""
		@ locked

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
		return self._set_cell(col, row, val, AD=AD, rescan=rescan)

	def set_cell_by_id(self, col, row_id, val, AD=True, rescan=True) -> bool:
		"""
		set value of a cell
		- col: column name
		- row_id: unique id of the row
		- val: value of cell
		- AD: auto dump
		- rescan: rescan the db if changes are made

		ie:
		```python
		db.set_cell_by_id("name", 0, "John")
		```
		"""
		return self.set_cell(col=col, row=self.ids.index(row_id), val=val, AD=AD, rescan=rescan)

	def _get_cell(self, col, row, rescan=True):
		"""
		get cell value only (by row index)
		- col: column name
		- row: row index
		"""
		self.rescan(rescan=rescan)


		try:
			_col = self._pk.db[col]
		except KeyError:
			column_names = self._column_names_func(rescan=False)
			raise KeyError("Invalid column name:", col, "\nAvailable columns:", column_names)
		try:
			cell = _col[row]
		except IndexError:
			raise IndexError("Invalid row index:", row, "\nAvailable rows:", self.height)

		return cell

	@threadsafe_decorator
	def get_cell(self, col, row, rescan=True):
		"""
		@ locked

		get cell value only (by row index)
		- col: column name
		- row: row index
		"""
		return self._get_cell(col, row, rescan=rescan)

	def get_cell_by_id(self, col, row_id, rescan=True):
		"""
		get cell value only (by row_id)
		- col: column name
		- row_id: unique id of the row
		"""
		try:
			row = self.ids.index(row_id)
		except ValueError:
			raise ValueError("Invalid row id:", row_id)
		return self.get_cell(col, row, rescan=rescan)

	def get_cell_obj(self, col, row:int=-1, row_id:int=-1, rescan=True) -> "_PickleTCell":
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
		self.rescan(rescan=rescan)

		if row>-1:
			if row>=self.height:
				raise IndexError(f"Invalid row index. [expected: 0 to {self.height-1}] [got: {row}]")
			return _PickleTCell(self, column=col, row_id=self.ids[row], CC=self.CC)
		if row_id>-1:
			return _PickleTCell(self, column=col, row_id=row_id, CC=self.CC)

		# in case row or row_id is invalid
		raise IndexError("Invalid row")

	@threadsafe_decorator
	def pop_row(self, index:int=-1, returns=True, AD=True, rescan=True) -> Union[dict, None]:
		"""
		@ locked

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

		for c in self._column_names_func(rescan=False):
			self._pk.db[c].pop(index)

		self.ids.pop(index)

		self.height -=1

		self.auto_dump(AD=AD)

		return box

	def del_row(self, row:int, AD=True, rescan=True):
		"""
		Delete a row from the table (by row index)
		- row: row index
		- AD: auto dump
		"""
		# Auto dumps (locked)
		self.pop_row(row, returns=False, AD=AD, rescan=rescan)



	def del_row_id(self, row_id:int, AD=True):
		"""
		Delete a row from the table (by row_id)
		- row_id: unique id of the row
		- AD: auto dump
		"""
		self.del_row(self.ids.index(row_id), AD=AD)


	@threadsafe_decorator
	def clear(self, AD=True, rescan=True):
		"""
		@ locked

		Delete all rows
		- AD: auto dump
		"""
		self.rescan(rescan=rescan)

		for c in self._column_names_func(rescan=False):
			self._pk.db[c].clear()

		self.ids.clear()
		self.height = 0

		self.auto_dump(AD=AD)

		return self

	def blank_sheet(self, AD=True, rescan=True):
		"""
		Blank the sheet (clear all rows and columns)
		- AD: auto dump
		"""
		self.clear(AD=False, rescan=rescan)

		for c in self._column_names_func(rescan=False):
			self._pk.db.pop(c)

		self.auto_dump(AD=AD)

		return self

	def _copy(self, location=None, auto_dump=True, sig=True) -> "PickleTable":
		"""
		@ locked

		Copy the table to a new location/memory
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""
		
		new = PickleTable(location, auto_dump=auto_dump, sig=sig)
		new.add_column(*self._column_names_func())
		new._pk.db = datacopy.deepcopy(self.__db__())
		new.height = self.height
		new.ids = self.ids.copy()

		return new

	
	@threadsafe_decorator
	def copy(self, location=None, auto_dump=True, sig=True) -> "PickleTable":
		"""
		@ locked

		Copy the table to a new location/memory
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""
		return self._copy(location=location, auto_dump=auto_dump, sig=sig)



	@threadsafe_decorator
	def add_row(self, row:Union[dict, "_PickleTRow"], position:int=None, rescan=True, AD=True) -> "_PickleTRow":
		"""
		@ locked

		Add a row to the table. (internal use, no auto dump)
		- row: row must be a dict or _PickleTRow containing column names and values
		- position: position to add the row (default: `None`->`last`)
		- rescan: rescan the db if changes are made (default: `False`)
		- AD: auto dump (default: `False`)
		- return: row object
		"""
		self.rescan(rescan=rescan)


		if not self.ids:
			row_id = 0
		else:
			row_id = self.ids[-1] + 1

		column_names = self._column_names_func(rescan=False)

		position = position if position is not None else self.height

		self.ids.insert(position, row_id)
		for k in column_names:
			self._pk.db[k].insert(position, row.get(k))

		self.height += 1

		self.auto_dump(AD=AD)

		return self.row_obj_by_id(row_id)


	def insert_row(self, row:Union[dict, "_PickleTRow"], position:int=None, AD=True) -> "_PickleTRow":
		"""
		- row: row must be a dict|_PickleTRow containing column names and values
		- position: position to add the row (default: `None`->`last`)
		- AD: auto dump
		- return: row object

		ie:
		```python
		db.insert_row({"name": "John", "age": 25}, position=0)
		db.insert_row(row_obj, position=0)
		```
		"""

		return self.add_row(row=row, position=position, AD=AD)


	def add_row_as_list(self, row:list, position:int=None, AD=True, rescan=True) -> "_PickleTRow":
		"""
		- row: row must be a list containing values. (order must match with column names)
		- position: position to add the row (default: `None`->`last`)
		- AD: auto dump
		- return: row object

		ie:
		```python
		# db.column_names == ["name", "age"]
		db.add_row_as_list(["John", 25])
		"""
		row_obj = self.add_row(row={k:v for k, v in zip(self.column_names, row)}, position=position, rescan=rescan, AD=AD)

		return row_obj

	def add_rows(self, rows:List[Union[dict, "_PickleTRow"]], position:int=None, rescan=True, AD=True) -> List["_PickleTRow"]:
		"""
		- rows: list of rows (dict|_PickleTRow)
		- position: position to add the row (default: `None`->`last`)
		- AD: auto dump
		- return: list of row objects

		ie:
		```python
		db.add_rows([{"name": "John", "age": 25}, {"name": "Alice", "age": 30}])
		```
		"""
		self.rescan(rescan=rescan)
		ret = []
		for row in rows:
			ret.append(self.add_row(row=row, position=position, AD=False, rescan=False))

		self.auto_dump(AD=AD)
		return ret

	def add_rows_as_list(self, rows:List[list], position:int=None, AD=True, rescan=True) -> List["_PickleTRow"]:
		"""
		- rows: list of rows (list)
		- position: position to add the row (default: `None`->`last`)
		- AD: auto dump
		- return: list of row objects

		ie:
		```python
		# db.column_names == ["name", "age"]
		db.add_rows_as_list([["John", 25], ["Alice", 30]])
		```
		"""
		self.rescan(rescan=rescan)

		ret = []
		for row in rows:
			ret.append(self.add_row_as_list(row=row, position=position, AD=False, rescan=False))

		self.auto_dump(AD=AD)
		return ret

	@threadsafe_decorator
	def sort(self, column=None, key=None, reverse=False, copy=False, AD=True, rescan=True):
		"""
		Sort the table by a key
		- column: column name to sort by
		- key: function to get the key for sorting
		- reverse: reverse the sorting
		- copy: return a copy of the table, `can be` the `location` of `to save file` (default: `False`)
		- AD: auto dump
		"""
		self.rescan(rescan=rescan)

		if copy:
			if copy is True:
				copy = ''
			db = self._copy(location=copy, auto_dump=self._pk.auto_dump, sig=self._pk.sig)
		else:
			db = self

		# create a index array for sorting then apply to all columns and ids
		if column:
			def get_cell(row: dict):
				return row[column]

		elif key:
			def get_cell(row: dict):
				return key(row)

		else:
			def get_cell(row: dict):
				return row.values()

		seq = range(db.height)
		seq = sorted(seq, key=lambda x: get_cell(db._row(x)), reverse=reverse)

		# apply to all columns
		for col in self._column_names_func(rescan=False):
			db._pk.db[col] = [self._pk.db[col][i] for i in seq]

		db.ids = [self.ids[i] for i in seq]

		db.auto_dump(AD=AD)

		return db


	def remove_duplicates(self, columns=None, AD=True, rescan=True):
		"""
		Remove duplicate rows (keep the 1st occurrence)
		- columns: columns to check for duplicates (default: all columns) (if None, all columns are checked) (if string, only that column is checked) (if list, all the mentioned columns are checked)
		- AD: auto dump
		"""
		self.rescan(rescan=rescan)

		if columns is None:
			columns = self._column_names_func(rescan=False)
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



	def dump(self, filepath=None):
		"""
		Dump the table to the db file
		- ignored if the table is in-memory
		- filepath: path to the file (if None, use current filepath)
		"""
		self._pk.dump(filepath=filepath)

	def auto_dump(self, AD=True):
		"""
		Auto dump the table to the db file
		- ignored if the table is in-memory
		"""
		self._pk._autodumpdb(AD=AD)

	def to_json(self, filepath=None, indent=4, format=list) -> str:
		"""
		Write the table to a json file
		- filepath: path to the file (if None, use current filepath.json) (if in memory and not provided, uses "table.json")
		- indent: indentation level (default: 4 spaces)
		- format: format of the json file (default: list) [options: list|dict]
			- list: list of rows [{col1: val1, col2: val2, ...}, ...]
			- dict: dict of columns {col1: [val1, val2, ...], col2: [val1, val2, ...], ...}

		- return: path to the file
		"""
		if filepath is None:
			# check filepath
			path = self._pk.location
			if not path:
				path = "table.json"
			else:
				path = os.path.splitext(path)[0] + ".json"
		else:
			path = filepath


		# write to file
		with open(path, "w", encoding='utf8') as f:
			if format == dict or format == 'dict':
				json.dump(self.__db__(), f, indent=indent)
			elif format == list or format == 'list':
				json.dump(list(self.rows()), f, indent=indent)
			else:
				raise AttributeError("Invalid format. [expected: list|dict] [got:", format, "]")

		return os.path.realpath(path)

	def to_json_str(self, indent=4) -> str:
		"""
		Return the table as a json string
		"""
		return json.dumps(self.__db__(), indent=indent)

	def load_json(self, filepath=None, iostream=None, json_str=None, ignore_new_headers=False, on_file_not_found='error', keep_columns=True, AD=True):
		"""
		Load a json file to the table
		- WILL OVERWRITE THE EXISTING ROWS (To append, make a new table and extend)
		- filepath: path to the file
		- iostream: io stream object (use either filepath or iostream)
		- json_str: json string
		- ignore_new_headers: ignore new headers|columns if found `[when header=True]` (default: `False` and will add new headers)
		- on_file_not_found: action to take if the file is not found (default: `'error'`) [options: `error`|`ignore`|`warn`|`no_warning`]
			* if `error`, raise FileNotFoundError
			* if `ignore`, ignore the operation (no warning, **no clearing**)
			* if `no_warning`, ignore the operation, but **clears db**
			* if `warn`, print warning and ignore the operation, but **clears db**
		"""
		
		# if more than one source is provided
		sources = [i for i in [filepath, iostream, json_str] if i]
		if len(sources) > 1:
			raise AttributeError(f"Only one source is allowed. Got: {len(sources)}")

		# if no source is provided
		if not sources:
			raise AttributeError("No source provided")

		if json_str:
			# load it as io stream
			iostream = io.StringIO(json_str)

		if not ((filepath and os.path.isfile(filepath))	or (iostream and  isinstance(iostream, io.IOBase))):
			if on_file_not_found == 'error':
				raise FileNotFoundError(f"File not found: {filepath}")

			elif on_file_not_found == 'ignore':
				return
			else:
				self.clear(AD=AD, rescan=False)
				if on_file_not_found == 'warn':
					logger.warning(f"File not found: {filepath}. Cleared the table.")
				if on_file_not_found == 'no_warning':
					pass

				return

		if keep_columns:
			self.clear(AD=False, rescan=False)
		else:
			self.blank_sheet(AD=False, rescan=False)

		def load_as_io(f):
			return json.load(f)

		if iostream:
			data = load_as_io(iostream)
		else:
			with open(filepath, "r", encoding='utf8') as f:
				data = load_as_io(f)

		# print(data)

		if not data:
			return

		existing_columns = self.column_names_func(rescan=False)

		if isinstance(data, dict):
			# column names are keys
			self.add(table=data, 
				add_extra_columns=ignore_new_headers, 
				AD=AD
			)

		elif isinstance(data, list):
			# per row
			for row in data:
				if not ignore_new_headers:
					for col in row:
						if col not in existing_columns:
							self.add_column(col, exist_ok=True, AD=False, rescan=False)

				self.add_row(row, rescan=False, AD=False)

		self.auto_dump(AD=AD)


	def to_csv(self, filepath=None, write_header=True) -> str:
		"""
		Write the table to a csv file
		- filepath: path to the file (if None, use current filepath.csv) (if in memory and not provided, uses "table.csv")
		- write_header: write column names as header (1st row) (default: `True`)

		- return: path to the file
		"""
		if filepath is None:
			# check filepath
			path = self._pk.location
			if not path:
				path = "table.csv"
			else:
				path = os.path.splitext(path)[0] + ".csv"
		else:
			path = filepath

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

	def load_csv(self, filepath=None, iostream=None, csv_str=None,
	header=True, ignore_none=False, ignore_new_headers=False, on_file_not_found='error', AD=True):
		"""
		Load a csv file to the table
		- WILL OVERWRITE THE EXISTING DATA (To append, make a new table and extend)
		- filepath: path to the file
		- iostream: io stream object (use either filepath or iostream)
		- header: 
			* if True, the first row will be considered as column names
			* if False, the columns will be named as "Unnamed-1", "Unnamed-2", ...
			* if "auto", the columns will be named as "A", "B", "C", ..., "Z", "AA", "AB", ...
		- ignore_none: ignore the None rows
		- ignore_new_headers: ignore new headers if found `[when header=True]` (default: `False` and will add new headers)
		- on_file_not_found: action to take if the file is not found (default: `'error'`) [options: `error`|`ignore`|`warn`|`no_warning`]
			* if `error`, raise FileNotFoundError
			* if `ignore`, ignore the operation (no warning, **no clearing**)
			* if `no_warning`, ignore the operation, but **clears db**
			* if `warn`, print warning and ignore the operation, but **clears db**
		"""
		columns_names = self.column_names

		def add_row(row, columns):
			if ignore_none and all((v is None or v == '') for v in row):
				return

			new_row = {k: v for k, v in zip(columns, row)}
			
			self.add_row(new_row, AD=False, rescan=False)

		# if more than one source is provided
		sources = [i for i in [filepath, iostream, csv_str] if i]
		if len(sources) > 1:
			raise AttributeError(f"Only one source is allowed. Got: {len(sources)}")

		if not sources:
			raise AttributeError("No source provided")

		if csv_str:
			# load it as io stream
			iostream = io.StringIO(csv_str)


		if not ((filepath and os.path.isfile(filepath)) or (iostream and  isinstance(iostream, io.IOBase))):
			if on_file_not_found == 'error':
				raise FileNotFoundError(f"File not found: {filepath}")

			elif on_file_not_found == 'ignore':
				return
			else:
				self.clear(AD=AD, rescan=False)
				if on_file_not_found == 'warn':
					logger.warning(f"File not found: {filepath}. Cleared the table.")
				if on_file_not_found == 'no_warning':
					pass

				return

		self.clear(AD=False, rescan=False)


		def load_as_io(f):
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

					if not (col in columns_names):
						if ignore_new_headers:
							continue
						if col in updated_columns:
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
				
				add_row(row, columns) # add the first row
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

				add_row(row, columns) # add the first row





			for row in reader:
				add_row(row, columns)

		if filepath:
			with open(filepath, 'r', encoding='utf8') as f:
				load_as_io(f)
		elif iostream:
			load_as_io(iostream)


		self.auto_dump(AD=AD)

	
	def extend(self, other: "PickleTable", add_extra_columns=None, AD=True, rescan=True):
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

		self.rescan(rescan=rescan)

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
			self.add_row({k: row[k] for k in keys}, AD=False, rescan=False)

		self.auto_dump(AD=AD)


	def add(self, table:Union["PickleTable", dict], add_extra_columns=None, AD=True, rescan=True):
		"""
		Add another table to this table
		- table: PickleTable object or dict
		- add_extra_columns: add extra columns if not exists (default: `None`-> raise error if columns mismatch)
			- if True, add extra columns
			- if False, ignore extra columns
			- if None, raise error if columns mismatch (default)
		- AD: auto dump
		"""
		self.rescan(rescan=rescan)

		if isinstance(table, dict) or isinstance(table, type(self)):
			keys = table.keys()
		else:
			raise TypeError("Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(table).__name__))

		table_type = "dict" if isinstance(table, dict) else "PickleTable"
		if table_type == "PickleTable":
			table.rescan(rescan=rescan)

		this_keys = self.column_names
		if add_extra_columns:
			self.add_column(*keys, exist_ok=True, AD=False, rescan=False)
		else:
			for key in keys:
				if key not in this_keys:
					if add_extra_columns is False:
						keys.remove(key)
					else:
						raise ValueError(f"Columns mismatch: {this_keys} != {keys}")

		if isinstance(table, dict):
			max_height = 0
			for key, value in (table.items(rescan=False) if table_type=="PickleTable" else table.items()):
				if not isinstance(value, (list, tuple)):
					raise TypeError(f"Value type must be a list/tuple. Got: {type(value).__name__} for key: {key}")

				max_height = max(max_height, len(value))

			for i in range(max_height):
				if table_type == "dict":
					row = {k: table[k][i] if i<len(table[k]) else None for k in keys}
				else:
					row = {k: table.get_cell(k, i, rescan=False) for k in keys}
					
				self.add_row(row, AD=False, rescan=False)

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
		return self.get_value()

	def get_value(self, rescan=True):
		"""
		return the value of the cell
		"""
		self.raise_deleted()

		return self.source.get_cell_by_id(self.column_name, self.id, rescan=rescan)


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

	def set(self, value, AD=True, rescan=True):
		"""
		Set the `value` of the cell
		"""
		self.source_check()

		self.source.set_cell_by_id(self.column_name, self.id, val=value, AD=AD, rescan=rescan)


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

	def clear(self, AD=True, rescan=True):
		"""Clear the cell value"""
		self.source_check()

		self.source.set_cell_by_id(self.column_name, self.id, None, AD=AD, rescan=rescan)


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

		return self.source.get_cell_obj(col=name, row_id=self.id, rescan=rescan)

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
		# if not iterable
		if not hasattr(other, "__iter__"):
			return False

		try:
			for k in self.source.column_names:
				if self[k] != other[k]:
					return False
			return True
		except (KeyError, TypeError, IndexError):
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

	def get_cell_obj(self, row:int, default=None, rescan=True) -> "_PickleTCell":
		"""
		return the cell object of the column by row index
		"""

		self.raise_deleted()
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self.source.get_cell_obj(col=self.name, row=row, rescan=rescan)

	def _set_item(self, row:int, value, AD=True, rescan=True):
		"""
		@ Auto dumps

		[FASTER+UNSAFE] Set the cell value in the column by row index

		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		* AD: auto dump
		* rescan: rescan the db file if changed
		"""

		self.raise_deleted()
		# self.source.raise_source(self.CC)

		if isinstance(value, _PickleTCell):
			value = value.value

		self.source.set_cell(col=self.name, row=row, val=value, AD=AD, rescan=rescan)


	def set_item(self, row:int, value, AD=True, rescan=True) -> "_PickleTCell":
		"""
		@ Auto dumps

		Set the cell value in the column by row index

		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		* AD: auto dump
		* rescan: rescan the table after setting the value
		"""

		self.raise_deleted()
		# self.source.raise_source(self.CC)

		if isinstance(value, _PickleTCell):
			value = value.value

		# self.source.set_cell(col=self.name, row=row, val=value, AD=AD)
		cell:"_PickleTCell" = self.get_cell_obj(row, rescan=rescan)
		cell.set(value, AD=AD, rescan=False)

		return cell

	def __setitem__(self, row:int, value):
		"""
		@ Auto dumps
		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		"""

		# self.source.raise_source(self.CC)
		self.set_item(row, value, AD=True, rescan=True)

	def del_item(self, row:int, AD=True, rescan=True):
		"""
		@ Auto dumps


		Delete the cell value from the column by row index

		- row: row index (not id)
		- AD: auto dump
		"""
		self.raise_deleted()
		self.source.set_cell(self.name, row, None, AD=AD, rescan=rescan)

	def __delitem__(self, row:int):
		"""
		@ Auto dump
		* row: index of row (not id)
		"""
		self.del_item(row, AD=True, rescan=True)

	def __iter__(self):
		return self.get_cells_obj()

	def __contains__(self, item):
		self.raise_deleted()
		return item in self.iter_values()

	def iter_values(self, rescan=True) -> Generator:
		"""
		returns the values of the column
		"""
		self.raise_deleted()
		self.source.rescan(rescan=rescan)

		for i in self:
			yield i.get_value(rescan=False)

	def to_list(self, rescan=True) -> list:
		"""
		returns the column as list
		"""
		self.raise_deleted()
		return list(self.iter_values(rescan=rescan))

	def to_dict(self, rescan=True) -> dict:
		"""
		returns the column as dict
		"""
		self.raise_deleted()
		self.source.rescan(rescan=rescan)

		d = {i: v for i, v in enumerate(self.iter_values())}
		return d

	def source_list(self):
		"""
		returns the column list as a pointer
		"""
		self.raise_deleted()
		return self.source.get_column(self.name)

	def get_cells_obj(self, start:int=0, end:int=None, sep:int=1) -> Generator["_PickleTCell", None, None]:
		"""
		Return a list of all rows in db

		- start: start index (default: 0)
		- end: end index (default: None)
		- sep: step (default: 1)
		"""
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

	def update(self, column:Union[list, "_PickleTColumn"], AD=True, rescan=True):
		"""
		@ Auto dumps
		- column: list of values to update
		"""
		self.raise_deleted()
		self.source.raise_source(self.CC)

		if isinstance(column, self.__class__):
			column = column.to_list()

		self.source.rescan(rescan=rescan)
		for i, v in enumerate(column):
			self._set_item(i, v, AD=False, rescan=False)

		self.source.auto_dump(AD=AD)

	def remove(self, value, n_times=1, AD=True, rescan=True):
		"""
		@ Auto dumps
		- This will remove the occurrences of the value in the column (from top to bottom)
		- n_times: number of occurrences to remove (0: all)
		"""
		self.raise_deleted()

		self.source.rescan(rescan=rescan)
		for i in self:
			if i == value:
				i.clear(AD=False, rescan=False)
				n_times -= 1
				if n_times==0:
					break

		self.source.auto_dump(AD=AD)




	def clear(self, AD=True, rescan=True) -> None:
		"""
		@ Auto dumps
		# This will Set all cells in column to `None`
		"""
		self.raise_deleted()

		self.source.raise_source(self.CC)
		self.source.rescan(rescan=rescan)

		for row in range(self.source.height):
			self._set_item(row, None, AD=False, rescan=False)

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

		self.deleted = True


	def apply(self, func=None, row_func=False, copy=False, AD=True):
		"""
		Apply a function to all cells in the column
		Overwrites the existing values

		- func: function to apply
		- row_func: if True, apply the function to the row object instead of the cell value
		- copy: if True, return a copy of the column
		- AD: auto dump

		- returns: 
			* `list of values` if `copy=True`
			* `self` if `copy=False`
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
			tb.add_row({"x":n, "Y":'🍎'})

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
		print(f"⏱️ [IN-MEMORY] DUMP time: {tt-dt}s")

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
		if TABLE:
			print(tabulate(cells, headers="keys", tablefmt="simple_grid"))
		else:
			print(cells, sep="\n")


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


		
		print("="*50)
		print("\n\n📝 TEST convert to CSV")

		CSV_tb = PickleTable()
		CSV_tb.add_column("x", exist_ok=True)
		CSV_tb.add_column("Y", exist_ok=True)

		CSV_tb.add_row({"x":1, "Y":2})
		CSV_tb.add_row({"x":3, "Y":None})
		CSV_tb.add_row({"x":"5,5", "Y":6})

		st = time.perf_counter()
		CSV_tb.to_csv(f"test{st}.csv")
		et = time.perf_counter()
		print(f"⏱️ Convert to csv test in {et - st}s")

		with open(f"test{st}.csv", "r") as f:
			text = f.read()

		if text != """x,Y
1,2
3,
"5,5",6
""":
			raise Exception("❌ TEST [CONVERT TO CSV]: Failed (Data Mismatch)")
		os.remove(f"test{st}.csv")

		print("="*50)

		print("\n\n📝 Load csv test")

		tb.clear()

		print("Initial table")
		print(tb)
		print(tb.column_names)

		csv_test_data = """x,Y\n1,2\n3,4\n5,6\n"""
		csv_test_iostream = io.StringIO(csv_test_data)

		# make a csv file
		with open("test.csv", "w") as f:
			f.write(csv_test_data)

		print("\t📝 Normal Load [from File 📄 ]")
		try:
			tb.load_csv("test.csv")
		except Exception as e:
			print("❌ TEST [LOAD CSV][Normal Load][from File 📄 ]: Failed (Other error)")
			raise e
		if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD CSV][Normal Load][from File 📄 ]: Failed")

		print("\t✅ TEST [LOAD CSV][Normal Load][from File 📄 ]: Passed")

		print("\t📝 Normal Load [from CSV string 🧵 ]")
		tb.clear()

		tb.load_csv(csv_str=csv_test_data)

		if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD CSV][Normal Load][from CSV string 🧵 ]: Failed")

		print("\t✅ TEST [LOAD CSV][Normal Load][from CSV string 🧵 ]: Passed")

		print("\t📝 Normal Load [From IOstream 🪡 ]")
		tb.clear()

		tb.load_csv(iostream=csv_test_iostream)

		if tb.height != 3 or tb.column("x") != ['1', '3', '5']:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD CSV][Normal Load][From IOstream 🪡 ]: Failed")

		print("\t✅ TEST [LOAD CSV][Normal Load][From IOstream 🪡 ]: Passed")

		print("\t📝 Multiple source [filepath+csv_str]['error']")
		tb.clear()
		# 1st error mode on multiple source
		try:
			tb.load_csv(filepath="test.csv", csv_str=csv_test_data)
			raise Exception("❌ TEST [LOAD CSV][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD CSV][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD CSV][Multiple source]: Failed (Other error)")
			raise e

		
		print("\t📝 Multiple source [filepath+iostream]['error']")
		# 2nd error mode on multiple source
		tb.clear()
		try:
			tb.load_csv(filepath="test.csv", iostream=csv_test_iostream)
			raise Exception("❌ TEST [LOAD CSV][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD CSV][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD CSV][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 Multiple source [iostream+csv_str]['error']")
		# 3rd error mode on multiple source
		tb.clear()
		try:
			tb.load_csv(iostream=csv_test_iostream, csv_str=csv_test_data)
			raise Exception("❌ TEST [LOAD CSV][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD CSV][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD CSV][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 Multiple source [filepath+csv_str+iostream]['error']")
		# 4th error mode on multiple source
		tb.clear()
		try:
			tb.load_csv(filepath="test.csv", csv_str=csv_test_data, iostream=csv_test_iostream)
			raise Exception("❌ TEST [LOAD CSV][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD CSV][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD CSV][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 No source []['error']")
		# 5th error mode on no source
		tb.clear()
		try:
			tb.load_csv()
			raise Exception("❌ TEST [LOAD CSV][No source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD CSV][No source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD CSV][No source]: Failed (Other error)")
			raise e







		print("\t📝 NoFile Load ['error']")
		# 1st error mode on file not found
		tb.clear()
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":4})
		tb.add_row({"x":5, "Y":6})

		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="error")
			raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='error']: Failed")
		except FileNotFoundError as e:
			print("\t✅ TEST [LOAD CSV][NoFile Load]['error'][on_file_not_found='error']: Passed")
			print("\tError message = ", e)



		print("\t📝 NoFile Load ['warn']")
		# 2nd error mode on file not found [DB is cleared]
		tb.clear()
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":4})
		tb.add_row({"x":5, "Y":6})

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


		print("\t📝 NoFile Load ['ignore']")
		# 3rd error mode on file not found
		tb.clear()
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":4})
		tb.add_row({"x":5, "Y":6})

		try:
			tb.load_csv(f"test-{random.random()}.csv", on_file_not_found="ignore")
			if tb.height != 3 or tb.column("x") != [1, 3, 5]:
				print(tb.columns())
				raise Exception("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed")
			print("\t✅ TEST [LOAD CSV][NoFile Load]['ignore'][on_file_not_found='ignore']: Passed")

		except FileNotFoundError as e:
			print("❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed (File not found)")
			raise e
		except Exception as e:
			print("\t❌ TEST [LOAD CSV][NoFile Load][on_file_not_found='ignore']: Failed (Other error)")
			raise e

			
		print("\t📝 NoFile Load ['no_warning']")
		# 4th error mode on file not found
		tb.clear()
		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":4})
		tb.add_row({"x":5, "Y":6})

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

		# in CSV every value is string
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

		###############################################
		print("="*50)

		JSON_tb = PickleTable()
		JSON_tb.add_column("x", exist_ok=True)
		JSON_tb.add_column("Y", exist_ok=True)

		JSON_tb.add_row({"x":1, "Y":2})
		JSON_tb.add_row({"x":3, "Y":None})
		JSON_tb.add_row({"x":"5", "Y":6})

		print("\n\n📝 TEST convert to JSON [dict format]")

		st = time.perf_counter()
		JSON_tb.to_json(f"test{st}.json", format="dict")
		et = time.perf_counter()
		print(f"⏱️ Convert to JSON test in {et - st}s")

		with open(f"test{st}.json") as f:
			text = f.read()

		data = {
			"x": [
				1,
				3,
				"5"
			],
			"Y": [
				2,
				None,
				6
			]
		}
		if text != json.dumps(data, indent=4):
			raise Exception("❌ TEST [CONVERT TO JSON]: Failed (Data Mismatch)") 
		os.remove(f"test{st}.json")

		print("="*50)

		print("\n\n📝 TEST convert to JSON [list format]")

		st = time.perf_counter()
		JSON_tb.to_json(f"test{st}.json", format="list")
		et = time.perf_counter()
		print(f"⏱️ Convert to JSON test in {et - st}s")

		with open(f"test{st}.json") as f:
			text = f.read()

		data = [
			{
				"x": 1,
				"Y": 2
			},
			{
				"x": 3,
				"Y": None
			},
			{
				"x": "5",
				"Y": 6
			}
		]
		if text != json.dumps(data, indent=4):
			raise Exception("❌ TEST [CONVERT TO JSON]: Failed (Data Mismatch)")

		os.remove(f"test{st}.json")

		print("="*50)


		print("\n\n📝 Load JSON (dict) test")

		tb.clear()

		print("Initial table")
		print(tb)
		print(tb.column_names)

		json_dict_test_data = """{
			"x": [1, 3, 5],
			"Y": [2, 4, 6]
		}"""

		json_list_test_data = """[
			{"x":1, "Y":2},
			{"x":3, "Y":4},
			{"x":5, "Y":6}
		]"""

		json_dict_test_iostream = io.StringIO(json_dict_test_data)
		json_file = "test.json"
		# make a json file
		with open(json_file, "w") as f:
			f.write(json_dict_test_data)

		print("\t📝 Normal Load [from JSON dict 📄 ]")
		try:
			tb.load_json(json_file)
		except Exception as e:
			print("❌ TEST [LOAD JSON][Normal Load][from JSON dict 📄 ]: Failed (Other error)")
			raise e
		if tb.height != 3 or tb.column("x") != [1, 3, 5]:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD JSON][Normal Load][from JSON dict 📄 ]: Failed")

		print("\t✅ TEST [LOAD JSON][Normal Load][from JSON dict 📄 ]: Passed")

		print("\t📝 Normal Load [from JSON string 🧵 ]")
		tb.clear()

		tb.load_json(json_str=json_dict_test_data)

		if tb.height != 3 or tb.column("x") != [1, 3, 5]:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD JSON][Normal Load][from JSON string 🧵 ]: Failed")

		print("\t✅ TEST [LOAD JSON][Normal Load][from JSON string 🧵 ]: Passed")

		print("\t📝 Normal Load [From IOstream 🪡 ]")
		tb.clear()

		tb.load_json(iostream=json_dict_test_iostream)

		if tb.height != 3 or tb.column("x") != [1, 3, 5]:
			print(tb)
			print(tb.column("x"), tb.column('x')==[1, 3, 5])
			print(tb.height, tb.height==3)
			raise Exception("❌ TEST [LOAD JSON][Normal Load][From IOstream 🪡 ]: Failed")

		print("\t✅ TEST [LOAD JSON][Normal Load][From IOstream 🪡 ]: Passed")

		print("\t📝 Multiple source [filepath+json_str]['error']")
		# 1st error mode on multiple source
		tb.clear()

		try:
			tb.load_json(filepath=json_file, json_str=json_dict_test_data)
			raise Exception("❌ TEST [LOAD JSON][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD JSON][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD JSON][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 Multiple source [filepath+iostream]['error']")
		# 2nd error mode on multiple source
		tb.clear()
		try:
			tb.load_json(filepath=json_file, iostream=json_dict_test_iostream)
			raise Exception("❌ TEST [LOAD JSON][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD JSON][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD JSON][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 Multiple source [iostream+json_str]['error']")
		# 3rd error mode on multiple source
		tb.clear()
		try:
			tb.load_json(iostream=json_dict_test_iostream, json_str=json_dict_test_data)
			raise Exception("❌ TEST [LOAD JSON][Multiple source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD JSON][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD JSON][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 Multiple source [filepath+json_str+iostream]['error']")
		# 4th error mode on multiple source
		tb.clear()

		try:
			tb.load_json(filepath=json_file, json_str=json_dict_test_data, iostream=json_dict_test_iostream)
			raise Exception("❌ TEST [LOAD JSON][Multiple source]: Failed")

		except AttributeError as e:
			print("\t✅ TEST [LOAD JSON][Multiple source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD JSON][Multiple source]: Failed (Other error)")
			raise e

		print("\t📝 No source []['error']")
		# 5th error mode on no source
		tb.clear()

		try:
			tb.load_json()
			raise Exception("❌ TEST [LOAD JSON][No source]: Failed")
		except AttributeError as e:
			print("\t✅ TEST [LOAD JSON][No source]: Passed")
			print("\tError message = ", e)

		except Exception as e:
			print("\t❌ TEST [LOAD JSON][No source]: Failed (Other error)")
			raise e


		if os.path.exists(json_file):
			os.remove(json_file)
		if os.path.exists("test.csv"):
			os.remove("test.csv")


		print([tb.location])

		print("\t📝 _PickleTColumn -> list test")
		tb.clear()
		tb.add_column("x", exist_ok=True)
		tb.add_column("Y", exist_ok=True)

		tb.add_row({"x":1, "Y":2})
		tb.add_row({"x":3, "Y":4})
		tb.add_row({"x":5, "Y":6})

		col = tb.column_obj("x")
		if list(col) != [1, 3, 5]:
			raise Exception("❌ TEST [_PickleTColumn -> list]: Failed")
		if col[0] != 1:
			raise Exception("❌ TEST [_PickleTColumn -> list]: Failed")
		if col.to_list() != [1, 3, 5]:
			raise Exception("❌ TEST [_PickleTColumn -> list]: Failed")
		print("list(_PickleTColumn) = ", list(col))
		print("_PickleTColumn = ", col)
		print("_PickleTColumn.to_list() = ", col.to_list())
		print("\t✅ TEST [_PickleTColumn -> list]: Passed")

		print("\t📝 _PickleTColumn -> dict test")

		if col.to_dict() != {0: 1, 1: 3, 2: 5}:
			raise Exception("❌ TEST [_PickleTColumn -> dict]: Failed")

		print("_PickleTColumn.to_dict() = ", col.to_dict())
		print("\t✅ TEST [_PickleTColumn -> dict]: Passed")
		try:
			dict(col)
			raise Exception("❌ TEST [_PickleTColumn -> dict]: (Must raise error) on dict(_PickleTColumn))")
		except TypeError as e:
			print(e)
			print("\t✅ TEST [_PickleTColumn -> dict]: Passed (Raise Exception on dict(_PickleTColumn))")


		print("="*50)

		# PARALLEL TEST
		print("\n\n📝 Parallel test ::")


		def test_io_in_single_db(db: PickleTable, thread_id=None):
			"""Test I/O operations in a single database."""
			print("📝 Testing I/O operations in a single database")

			# Create a table

			for i in range(100):
				# Add some data
				row1 = db.add_row({"x": 1, "Y": 2}, rescan=False)
				row2 = db.add_row({"x": 3, "Y": 4}, rescan=False)
				row3 = db.add_row({"x": 5, "Y": 6}, rescan=False)

			row1_index = row1.index()
			row2_index = row2.index()
			row3_index = row3.index()

			# print(f"T {thread_id} :: {row1_index}, {row2_index}, {row3_index}, Max = {db.height}")

			# Save the database
			try:
				db.dump(f"table_{thread_id}.pdb")

				# Load the database
				new_db = PickleTable(f"table_{thread_id}.pdb")
				# print(f"T {thread_id} :: {new_db.height}")

				# Check the data
				if any([
					new_db.row(row1_index)["x"] != 1,
					new_db.row(row1_index)["Y"] != 2,
					new_db.row(row2_index)["x"] != 3,
					new_db.row(row2_index)["Y"] != 4,
					new_db.row(row3_index)["x"] != 5,
					new_db.row(row3_index)["Y"] != 6
				]):
					if thread_id is not None:
						ValueError(f"❌ [Thread {thread_id}] I/O operations in a single database failed [DATA MISMATCH]")
					raise ValueError("❌ I/O operations in a single database failed [DATA MISMATCH]")
			
			except Exception as e:
				if thread_id is not None:
					print(f"❌ [Thread {thread_id}] I/O operations in a single database failed")
				else:
					print("❌ I/O operations in a single database failed")
				raise e

			finally:
				if os.path.exists(f"table_{thread_id}.pdb"):
					os.remove(f"table_{thread_id}.pdb")

			if thread_id is not None:
				print(f"✅ [Thread {thread_id}] I/O operations in a single database passed")
			else:
				print("✅ I/O operations in a single database passed")

		
		def test_batch_io_in_single_db(db: PickleTable, thread_id=None):
			"""Test I/O operations in a single database."""
			print("📝 Testing I/O operations in a single database")

			# Create a table

			for i in range(100):
				# Add some data
				a, b, c, d, e, f = random.choices(range(100), k=6)
				rows = db.add_rows([
					{"x": a, "Y": b},
					{"x": c, "Y": d},
					{"x": e, "Y": f}
				])

			row1_index = rows[0].index()
			row2_index = rows[1].index()
			row3_index = rows[2].index()

# 			print(f"""🥳 
# T {thread_id} :: BATCH : 	{row1_index} == {rows[0]}
# T {thread_id} :: BATCH : 	{row2_index} == {rows[1]}
# T {thread_id} :: BATCH : 	{row3_index} == {rows[2]}
# T {thread_id} :: BATCH : 	Max = {db.height} :: {len(db['x'])}""")

			# Save the database
			try:
				db.dump(f"table_{thread_id}.pdb")

				# Load the database
				new_db = PickleTable(f"table_{thread_id}.pdb")

				# print(f"🥶 T {thread_id} :: BATCH : {new_db.height}")
				# Check the data
				if any([
					new_db.row(row1_index)["x"] != a,
					new_db.row(row1_index)["Y"] != b,
					new_db.row(row2_index)["x"] != c,
					new_db.row(row2_index)["Y"] != d,
					new_db.row(row3_index)["x"] != e,
					new_db.row(row3_index)["Y"] != f
				]):
					if thread_id is not None:
						raise ValueError(f"❌ [Thread {thread_id}] BATCH I/O operations in a single database failed [DATA MISMATCH]")
					raise ValueError("❌ BATCH I/O operations in a single database failed [DATA MISMATCH]")
			
			except Exception as e:
				if thread_id is not None:
					print(f"❌ [Thread {thread_id}] BATCH I/O operations in a single database failed")
				else:
					print("❌ BATCH I/O operations in a single database failed")
				raise e

			finally:
				if os.path.exists(f"table_{thread_id}.pdb"):
					os.remove(f"table_{thread_id}.pdb")

			if thread_id is not None:
				print(f"✅ [Thread {thread_id}] BATCH I/O operations in a single database passed")

			else:
				print("✅ BATCH I/O operations in a single database passed")


		def threading_request_test(threads_count=5):
			"""Test multithreading."""
			print("📝 Testing multithreading")
			# Create multiple threads for intense I/O
			threads = []

			import threading

			# Run the tests
			test_db = PickleTable("__test2.pdb")
			test_db.add_column("x", exist_ok=True)
			test_db.add_column("Y", exist_ok=True)

			start_time = time.perf_counter()
			for i in range(threads_count):  # Run 5 parallel tests
				t1 = threading.Thread(target=test_io_in_single_db, args=(test_db, i))
				threads.append(t1)
				t1.start()
			# Wait for all threads to finish
			for t in threads:
				t.join()

			end_time = time.perf_counter()
			print(f"\n\n⏱️ I/O operations in a single database test in {end_time - start_time}s")

			test_db.clear()

			start_time = time.perf_counter()
			for i in range(threads_count):
				t1 = threading.Thread(target=test_batch_io_in_single_db, args=(test_db, i))
				t1.start()
				threads.append(t1)
			# Wait for all threads to finish
			for t in threads:
				t.join()

			end_time = time.perf_counter()
			print(f"\n\n⏱️ BATCH I/O operations in a single database test in {end_time - start_time}s")

			# Clear the database
			if os.path.exists("__test2.pdb"):
				os.remove("__test2.pdb")

			print("🎉 All multithreaded tests completed successfully!")

		threading_request_test(threads_count=10)













if __name__ == "__main__":
	for i in range(1):
		try:
			os.remove("__test.pdb")
		except:
			pass
		test()

		if os.path.exists("__test.pdb"):
			os.remove("__test.pdb")
		print("\n\n\n" + "# "*25 + "\n")
