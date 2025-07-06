#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# REQUIREMENTS: msgpack, wcwidth, tabulate2
# pip install msgpack tabulate2


# THIS IS A HYBRID OF PICKLEDB AND MSGPACK and MY OWN CODES

# I'll JUST KEEP THE PICKLEDB LICENSE HERE
# Copyright 2025 Ratul Hasan <gh/RaSan147>
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
from types import FunctionType
import uuid
import threading
import datetime

import traceback
from typing import Any, Dict, Generator, List, Tuple, Union, Optional, Iterable
try:
	from typing import Literal
except ImportError:
	# For Python 3.7 and earlier
	try:
		from typing_extensions import Literal
	except ImportError:
		# Fallback to a simple string type
		class Literal:
			def __class_getitem__(cls, item): return type(item)

# import OrderedDict if python version is less than 3.7
if sys.version_info < (3, 7):
	from collections import OrderedDict  # type: ignore
else:
	OrderedDict = dict  # type: ignore

import re

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

try:
	try:
		from tabulate2 import tabulate  # pip install tabulate2
	except ImportError:
		from tabulate import tabulate
	TABLE = True
except ImportError:
	logger.warning(
		"tabulate not found, install it using `pip install tabulate2`\n * Printing table will not be in tabular format")
	# raise ImportError("tabulate not found, install it using `pip install tabulate2`")
	TABLE = False

try:
	# Check if msgpack is installed

	# Check if GIL is enabled (Now available in msgpack-1.1.0-cp313-cp313t-win_amd64.whl)
	if not getattr(sys, '_is_gil_enabled', lambda: True)():
		os.environ["MSGPACK_PUREPYTHON"] = "1"
		# msgpack is not thread safe (yet)

	import msgpack  # pip install msgpack
	SAVE_LOAD = True
except ImportError:
	logger.warning(
		"msgpack not found, install it using `pip install msgpack`\n * Save and Load will not work")
	SAVE_LOAD = False
	# raise ImportError("msgpack not found, install it using `pip install msgpack`")

__version__ = "0.2.0"


def load(location, auto_dump, sig=True):
	"""
	Return a PyroDB object. location is the path to the json file.
	"""
	return PyroDB(location, auto_dump, sig)


def as_is(*args, **kwargs):
	"""
	Does nothing — returns arguments as they are.
	- If only one positional argument is passed and no kwargs, returns that object.
	- If multiple args or kwargs, returns a tuple combining them.
	"""
	if len(args) == 1 and not kwargs:
		return args[0]
	return (*args, *kwargs.values())

# # Test cases
# print(as_is("hello", "world", 1, 2, 3, a=1, b=2, c=3))  # ('hello', 'world', 1, 2, 3, 1, 2, 3)
# print(as_is(4))  # 4


class DeletedObjectError(KeyError):
	"""
	Exception raised when trying to access a deleted object.
	"""

	def __init__(self, message):
		super().__init__(message)
		self.message = message

	def __str__(self):
		return f"DeletedObjectError: {self.message}"


class SourceNotFoundError(Exception):
	"""
	Exception raised when the source file is not found.
	"""

	def __init__(self, message):
		super().__init__(message)
		self.message = message

	def __str__(self):
		return f"SourceNotFoundError: {self.message}"

class IndexedDict:
	def __init__(self, initial=None):
		self.ids = []
		self.id_to_index = {}

		if initial:
			if isinstance(initial, dict):
				# Sort once, build in-place
				sorted_items = sorted(initial.items(), key=lambda x: x[1])
				self.ids = [k for k, _ in sorted_items]
				self._reindex(0)
			elif isinstance(initial, Iterable):
				self.ids = list(initial)
				self.id_to_index = {id_: i for i, id_ in enumerate(self.ids)}

	def _reindex(self, start=0):
		for i in range(start, len(self.ids)):
			self.id_to_index[self.ids[i]] = i

	def append(self, id_):
		if id_ in self.id_to_index:
			raise ValueError(f"ID '{id_}' already exists.")
		self.id_to_index[id_] = len(self.ids)
		self.ids.append(id_)

	def pop(self, index=-1):
		if index < 0:
			index += len(self.ids)
		if index < 0 or index >= len(self.ids):
			raise IndexError("Index out of range.")
		id_ = self.ids.pop(index)
		self.id_to_index.pop(id_)
		self._reindex(index)
		return id_

	def insert(self, index, id_):
		if id_ in self.id_to_index:
			raise ValueError(f"ID '{id_}' already exists.")
		self.ids.insert(index, id_)
		self._reindex(index)

	def delete(self, id_):
		if id_ not in self.id_to_index:
			raise KeyError(f"ID '{id_}' not found.")
		index = self.id_to_index.pop(id_)
		self.ids.pop(index)
		self._reindex(index)

	def get_index(self, id_):
		return self.id_to_index[id_]

	def get_id(self, index):
		return self.ids[index]

	def index(self, id_):
		return self.id_to_index[id_]

	def __iter__(self):
		for id_ in self.ids:
			yield id_

	def __len__(self):
		return len(self.ids)

	def __contains__(self, id_):
		return id_ in self.id_to_index

	def sort(self, key=None, reverse=False):
		self.ids.sort(key=key, reverse=reverse)
		self._reindex()

	def as_dict(self):
		return dict(self.id_to_index)

	def as_list(self):
		return self.ids

	def __repr__(self):
		return f"IndexedDict({self.as_dict()})"

	def __getitem__(self, index: Union[int, slice]):
		return self.ids[index]

	def copy(self):
		"""
		Return a shallow copy of the IndexedDict.
		"""
		return IndexedDict(self.ids)

	def clear(self):
		"""
		Clear the IndexedDict.
		"""
		self.ids.clear()
		self.id_to_index.clear()

import time
import threading
import time
import threading

class SnowflakeIDGenerator:
	def __init__(self, machine_id: int, epoch: int = None,
				 ts_bits: int = 41, machine_id_bits: int = 10, sequence_bits: int = 13):
		"""
		Initialize the Snowflake ID generator.

		Args:
			machine_id: Unique machine/process ID (0–(2^machine_id_bits - 1))
			epoch: Custom epoch in milliseconds (default: current time)
			ts_bits: Number of bits for timestamp (default: 41)
			machine_id_bits: Number of bits for machine ID (default: 10)
			sequence_bits: Number of bits for sequence number (default: 13)
		"""
		# Validate bit allocations
		if ts_bits + machine_id_bits + sequence_bits != 64:
			raise ValueError("Sum of ts_bits, machine_id_bits, and sequence_bits must be 64")

		self.ts_bits = ts_bits
		self.machine_id_bits = machine_id_bits
		self.sequence_bits = sequence_bits

		self.max_machine_id = (1 << machine_id_bits) - 1
		self.max_sequence = (1 << sequence_bits) - 1

		self.machine_id = machine_id & self.max_machine_id
		self.epoch = epoch or self._current_millis()

		self.lock = threading.Lock()
		self.last_timestamp = -1
		self.sequence = 0

	def _current_millis(self):
		return int(time.time() * 1000)

	def get_id(self):
		with self.lock:
			timestamp = self._current_millis() - self.epoch
			if timestamp < 0:
				raise ValueError("Current time is before the custom epoch")

			if timestamp == self.last_timestamp:
				self.sequence = (self.sequence + 1) & self.max_sequence
				if self.sequence == 0:
					while timestamp <= self.last_timestamp:
						timestamp = self._current_millis() - self.epoch
			else:
				self.sequence = 0
			self.last_timestamp = timestamp

			return (
				(timestamp & ((1 << self.ts_bits) - 1)) << (self.machine_id_bits + self.sequence_bits) | (self.machine_id << self.sequence_bits) | self.sequence
			)

	def decode_id(self, snowflake_id: int):
		"""Reverse an ID into components."""
		timestamp = (snowflake_id >> (self.machine_id_bits + self.sequence_bits)) + self.epoch
		machine_id = (snowflake_id >> self.sequence_bits) & self.max_machine_id
		sequence = snowflake_id & self.max_sequence
		return {
			"timestamp": timestamp,
			"machine_id": machine_id,
			"sequence": sequence
		}

import os
import time
import errno
import uuid
import json

# Platform-specific imports
if os.name == 'posix':
	import fcntl
elif os.name == 'nt':
	import msvcrt


class FileLock:
	"""File-based locking mechanism with timeout support"""
	def __init__(self, filename, timeout=10, delay=0.05):
		self.filename = filename
		self.timeout = timeout
		self.delay = delay
		self.fd = None
		self.is_locked = False

	def acquire(self):
		"""Acquire the lock, waiting if necessary"""
		start_time = time.time()
		while True:
			try:
				self.fd = os.open(self.filename, os.O_CREAT | os.O_RDWR | os.O_EXCL)
				self.is_locked = True
				break
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
				if (time.time() - start_time) >= self.timeout:
					raise TimeoutError(f"Timeout waiting for lock on {self.filename}")
				time.sleep(self.delay)

	def release(self):
		"""Release the lock"""
		if self.is_locked:
			os.close(self.fd)
			os.unlink(self.filename)
			self.is_locked = False
			self.fd = None

	def __enter__(self):
		self.acquire()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.release()
		if exc_type is not None:
			return False
		return True

class TaskExecutor:
	def __init__(self):
		self.__TASKS = Queue()
		self.busy = False
		self.active_future = None
		self.local = threading.local()

	def lock(self, func, *args, **kwargs):
		if hasattr(self.local, 'lock_depth') and self.local.lock_depth > 0:
			return func(*args, **kwargs)  # already in lock, run directly
		future = Future()
		self.__TASKS.put((func, args, kwargs, future))
		self.__next_task()
		return future.result()

	def __next_task(self):
		if self.busy: return
		while not self.__TASKS.empty():
			self.busy = True
			func, args, kwargs, future = self.__TASKS.get(timeout=0.1)
			self.active_future = future
			try:
				self.local.lock_depth = getattr(self.local, 'lock_depth', 0) + 1
				result = func(*args, **kwargs)
				future.set_result(result)
			except Exception as e:
				self.set_exception_with_traceback(future, e)
			finally:
				self.local.lock_depth -= 1
				self.__TASKS.task_done()
				self.busy = False
				self.active_future = None


	@staticmethod
	def set_exception_with_traceback(future, exception):
		"""
		Set an exception with traceback in the future object.

		Args:
				future (Future): The future object to set the exception on.
				exception (Exception): The exception to set.
		"""
		future.set_exception(exception)
		if exception.__traceback__ is None:
			exception.__traceback__ = traceback.extract_stack()


class PyroDB(object):

	key_string_error = TypeError('Key/name must be a string!')

	def __init__(self, location: Union[str, bytes]="", auto_dump=True, sig=True, auto_rescan=True, *args, **kwargs):
		"""Creates a database object and loads the data from the location path.
		If the file does not exist it will be created on the first update.
		"""
		self.task_executor = TaskExecutor()

		self.db = {}  # Initialize the database as an empty dictionary
		self.__db__ = {
			"__version__": __version__,
			"__type__": "PyroDB",
			"__db__": self.db,
		}

		self.in_memory = False
		self.location = ""
		if location:
			location_str = location if isinstance(location, str) else location.decode('utf-8')
			self.load(location_str, auto_dump)
		else:
			self.in_memory = True

		self.m_time = 0

		self.auto_dump = auto_dump
		self.auto_rescan = auto_rescan

		self.sig = sig
		if sig:
			self.set_sigterm_handler()

		self._autodumpdb()

	def __init__db__(self):
		"""
		Initialize the database object.
		This is a placeholder for any future initialization logic.
		"""
		self.__db__ = {
			"__version__": __version__,
			"__type__": "PyroDB",
			"__db__": self.db,
		}

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

	@staticmethod
	def threadsafe_decorator(func):
		"""
		Decorator for thread safe functions
		"""
		# check if the func stack is already locked
		# if not, lock it, else return the function

		def wrapper(self: "PyroTable", *args, **kwargs):
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
			return False

		if os.path.exists(self.location):
			m_time = os.stat(self.location).st_mtime
			# print("⏰", "OWN:", self.m_time, "NEW:", m_time)
			if m_time > self.m_time:
				self._loaddb()
				self.m_time = m_time

				return True

	def _auto_rescan(self, rescan=True):
		"""
		Automatically rescan the file for changes if auto_rescan is enabled.
		This is called before any operation that modifies the database.
		"""
		if self.auto_rescan and rescan and not self.in_memory:
			return self.rescan(rescan=rescan)
		return False

	def new(self):
		self.db = {}
		self.__init__db__()

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
		if os.path.isfile(self.location):
			self._loaddb()
		else:
			self.new()
		return True

	@threadsafe_decorator
	def dump(self, filepath=None):
		"""
		Dump to a temporary file, and then move to the actual location.
		If the data is in memory and a filepath is specified, it will be saved to that path.
		"""
		self.rescan()
		save_own = True
		if filepath and os.path.abspath(filepath) != os.path.abspath(self.location):
			save_own = False

		savepath = filepath or self.location

		# If saving is disabled, or data is in memory without a filepath, skip saving
		if not SAVE_LOAD or (self.in_memory and filepath is None) or savepath is None:
			return self.in_memory  # Return False or in_memory data if not saved

		db = self.__db__
		# Make a copy of the db if not saving to own location
		if not save_own:
			db = datacopy.deepcopy(self.__db__)

		logger.info("dumping to %s", savepath)

		# Use file lock during dump
		with FileLock(savepath + '.lock'):
			# Temporary file to dump the data
			with NamedTemporaryFile(mode='wb', delete=False) as f:
				try:
					msgpack.dump(db, f, default=PyroDB.___encode_datetime___)
				except Exception as e:
					logger.error('Error while dumping to temp file: %s', e)
					logger.error('Location: %s, (to be moved to %s)', f.name, savepath)
					raise e
			# Only move the file if it's not empty
			if os.stat(f.name).st_size != 0:
				shutil.move(f.name, savepath)
		
			# If saving to own location, update the modified time
			if save_own:
				self.m_time = os.stat(savepath).st_mtime


	
	# save = PROXY OF SELF.DUMP()
	save = dump

	def ___decode_datetime___(obj):
		if '__datetime__' in obj:
			if 'as_str' in obj:
				try:
					return datetime.datetime.strptime(obj['as_str'], "%Y%m%dT%H:%M:%S.%f%z")
				except ValueError:
					return datetime.datetime.strptime(obj['as_str'], "%Y%m%dT%H:%M:%S.%f")
		return obj

	def ___encode_datetime___(obj):
		if isinstance(obj, datetime.datetime):
			if obj.tzinfo is None:
				return {'__datetime__': True, 'as_str': obj.strftime("%Y%m%dT%H:%M:%S.%f")}
			else:
				return {'__datetime__': True, 'as_str': obj.strftime("%Y%m%dT%H:%M:%S.%f%z")}
		return obj


	def _loaddb(self):
		"""
		Load or reload the json info from the file
		"""
		if not SAVE_LOAD:
			logger.warning(
				"msgpack not found, install it using `pip install msgpack`\n * Only in-memory db will work")
			self.in_memory = True
			self.new()
			return
		try:
			with FileLock(self.location + '.lock'):
				with open(self.location, 'rb') as f:
					try:
						db: dict = msgpack.load(f, object_hook=PyroDB.___decode_datetime___)
					except Exception as e:
						logger.error(
							"Error while loading from file: %s", self.location)
						raise e

					if not isinstance(db, dict):
						raise ValueError(
							f"Expected a dict, got {type(db).__name__} from {self.location}")

				# OLD VERSION PATCH
				if not all(k in db for k in ["__version__", "__type__", "__db__"]):
					logger.warning(
						"Old database format detected. Migrating to new format.")
					# Migrate old format to new format
					db = {
						"__version__": __version__,
						"__type__": "PyroDB",
						"__db__": db
					}

				if "__version__" not in db or db["__version__"] != __version__:
					logger.warning(f"Database version mismatch. Expected: {__version__}, Found: {db.get('__version__', None)}")
					db["__old_version__"] = db.get("__version__", None)
					db["__version__"] = __version__
					# Optionally, you can handle version migration here if needed
				if "__type__" not in db or db["__type__"] != "PyroDB":
					logger.warning("Database type mismatch. Expected: 'PyroDB', Found: %s", db.get(
						"__type__", None))
					# Optionally, you can handle type migration here if needed

				self.db = db["__db__"]
				self.__init__db__()

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
		self._auto_rescan(rescan=rescan)
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
		self._auto_rescan(rescan=rescan)
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
		self._auto_rescan(rescan=rescan)
		return self.db.keys()

	def items(self, rescan=True):
		"""same as dict.items()"""
		self._auto_rescan(rescan=rescan)
		return self.db.items()

	def values(self, rescan=True):
		"""same as dict.values()"""
		self._auto_rescan(rescan=rescan)
		return self.db.values()

	def exists(self, key, rescan=True):
		"""
		Return True if key exists in db, return False if not
		"""
		self._auto_rescan(rescan=rescan)
		return key in self.db

	def rem(self, key, AD=True, rescan=True):
		"""
		Delete a key
		"""
		self._auto_rescan(rescan=rescan)
		if not key in self.db:  # return False instead of an exception
			return False
		del self.db[key]
		self._autodumpdb(AD=AD)
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


class PyroTable(dict):
	def __init__(self, filepath: Union[str, bytes]="", auto_dump=True, sig=True, always_rescan=False, *args, **kwargs):
		"""
		args:
		- filepath: path to the db file (default: `""` or in-memory db)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- always_rescan: always rescan the file for changes (default: `False`)
		"""
		self.task_executor = TaskExecutor()


		self.CC = self.gen_CC()  # consider it as country code and every items are its people. they gets NID

		self._pk = PyroDB(location=filepath, auto_dump=auto_dump, sig=sig, auto_rescan=True, *args, **kwargs)
		self.column_names_set = OrderedDict((k, None) for k in self._pk.db.keys())

		self.ids: IndexedDict = IndexedDict()


		self._pk.__db__["__epoch__"] = self._pk.__db__.get("__epoch__", None)
		self.id_generator = SnowflakeIDGenerator(
			machine_id=self.CC.int,
			epoch=self._pk.__db__["__epoch__"],
			ts_bits=41,
			machine_id_bits=8,
			sequence_bits=15
		)
		self._pk.__db__["__epoch__"] = self.id_generator.epoch


		self.height = self.get_height(rescan=False)


		self._pk.__db__["__id__"] = self._pk.__db__.get("__id__", None)
		if self._pk.__db__["__id__"] is None or len(self._pk.__db__["__id__"]) != self.height:
			# if __id__ is not set, generate a new one
			self.ids = self._gen_ids()
			self._pk.__db__["__id__"] = self.ids.ids
		self.refresh_ids(self._pk.__db__["__id__"])

		# make the super dict = self._pk.db


		# DEFAULR LIMIT FOR STR conversion
		self.str_limit = 50

	@staticmethod
	def threadsafe_decorator(func):
		"""
		Decorator for thread safe functions
		"""

		def wrapper(self: "PyroTable", *args, **kwargs):
			return self.task_executor.lock(func, self, *args, **kwargs)
		return wrapper

	# @threadsafe_decorator
	# def _generate_uuid(self) -> int:
	# 	"""
	# 	Generate a single UUID as an integer.
	# 	"""
	# 	uuid64 = uuid.uuid4().int >> 64

	# 	if len(self.ids) >= 2**64:
	# 		raise OverflowError("Cannot generate more than 2^64 unique IDs")

	# 	while uuid64 in self.ids:
	# 		uuid64 = uuid.uuid4().int >> 64
	# 	return uuid64

	@threadsafe_decorator
	def _generate_uuid(self) -> int:
		"""
		Generate a single UUID as an integer.
		Uses SnowflakeIDGenerator for unique ID generation.
		"""
		if len(self.ids) >= 2**64:
			raise OverflowError("Cannot generate more than 2^64 unique IDs")

		return self.id_generator.get_id()

	@threadsafe_decorator
	def _gen_ids(self) -> IndexedDict:
		"""
		Generate a list of unique IDs for the table rows.
		- Returns a list of UUIDs as integers.
		"""

		return IndexedDict((self._generate_uuid() for _ in range(self.height)))

	def refresh_ids(self, ids: Optional[Union[IndexedDict, list]] = None):
		if ids is None:
			# if ids is not provided, generate new ids
			self.ids = self._gen_ids()
		elif isinstance(ids, IndexedDict):
			# if ids is an IndexedDict, use it directly
			self.ids = ids
		elif isinstance(ids, list):
			# if ids is a list, convert it to IndexedDict
			self.ids = IndexedDict(ids)

		self._pk.__db__["__id__"] = self.ids.ids

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

	def __getitem__(self, index: Union[int, slice, str]):
		"""
		## args
		- index: row index or slice or column name
		## returns
		- PickleTRow object if index is int
		- list of PickleTRow objects if index is slice
		- PickleTColumn object if index is string
		"""
		self._auto_rescan()
		if isinstance(index, int):
			return self.row_obj(index)
		elif isinstance(index, slice):
			return [self.row_obj(i) for i in range(*index.indices(self.height))]
		elif isinstance(index, str):
			return self.column_obj(index)
		else:
			raise TypeError("indices must be integers or slices or string, not {}".format(
				type(index).__name__))

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
		self._auto_rescan(rescan=rescan)
		col_names = list(self._column_names_func(
			rescan=False))  # to preserve the order
		return [col_names] + [
			[self._pk.db[col][i] for col in col_names]
			for i in range(self.height)
		]

	def rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""
		updated = self._pk.rescan(rescan=rescan)
		if updated:
			self.height = self.get_height()
			self.refresh_ids(self._pk.__db__.get("__id__", None))
			self.column_names_set = OrderedDict((k, None) for k in self._pk.keys())
		return updated

	def _auto_rescan(self, rescan=True):
		"""
		Rescan the file for changes
		"""
		if self._pk.auto_rescan and rescan:
			return self.rescan(rescan=rescan)
		return False

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
		self.CC = uuid.uuid4()

		return self.CC

	@threadsafe_decorator
	def get_height(self, rescan=True):
		"""
		Return the number of rows
		"""
		self._auto_rescan(rescan=rescan)
		columns = self.column_names_set
		h = len(next(iter(self._pk.db.values()))) if columns else 0
		return h

	def __str__(self):
		"""
		Return a string representation of the table
		- if tabulate is installed, use it to format the table
		- else, use a simple string representation
		"""
		return self.to_str()

	def to_str(self, limit: int = 0):
		"""
		Return a string representation of the table

		Args:
		- limit: number of rows to show (default: 0->self.str_limit|50) [-1 for all rows]
		"""
		self._auto_rescan()
		if limit == -1:
			limit = self.height
		limit = limit or self.str_limit
		if not TABLE:
			x = ""
			x += "\t|\t".join(self.column_names_func(rescan=False))
			for i in range(min(self.height, limit)):
				x += "\n"
				x += "\t|\t".join([str(cell) if cell is not None else '' for cell in self.row(
					i, rescan=False).values()])

		else:
			x = tabulate(
				# self[:min(self.height, limit)],
				self.rows(start=0, end=min(
					self.height, limit), rescan=False),
				headers="keys",
				tablefmt="simple_grid",
				# "orgtbl",
				maxcolwidths=60
			)
		if self.height > limit:
			x += "\n..."

		return x

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
		self._auto_rescan(rescan=rescan)
		return datacopy.deepcopy(self._pk.db[name])

	@threadsafe_decorator
	def _get_column(self, name) -> list:
		"""
		Return the list pointer to the column (unsafe, not a copy)
		"""
		return self._pk.db[name]

	def get_column(self, name, rescan=True) -> list:
		"""
		Return a copy list of all values in column
		"""
		self._auto_rescan(rescan=rescan)
		return datacopy.deepcopy(self._get_column(name))

	def column_obj(self, name, rescan=True):
		"""
		Return a column object `_PickleTColumn` in db
		"""
		self._auto_rescan(rescan=rescan)
		existings = self.column_names_func(rescan=False)
		if name not in existings:
			raise KeyError(
				f"Column not Found, [Expected: {existings}][Got: {name}]")
		return _PyroTColumn(self, name, self.CC)

	@threadsafe_decorator
	def columns(self, rescan=True):
		"""
		Return a **copy list** of all columns in db
		"""
		self._auto_rescan(rescan=rescan)
		return self._pk.db.copy()

	def columns_obj(self, rescan=True):
		"""
		Return a list of all columns in db
		"""
		self._auto_rescan(rescan=rescan)
		return list(_PyroTColumn(self, name, self.CC) for name in self._pk.db)

	def _column_names_func(self, rescan=True):
		"""
		return a tuple (unmodifiable) of column names
		"""
		self._auto_rescan(rescan=rescan)
		return tuple(self._pk.db.keys())

	@threadsafe_decorator
	def column_names_func(self, rescan=True):
		"""
		return a tuple (unmodifiable) of column names
		"""
		return self._column_names_func(rescan=rescan)

	@property
	def column_names(self):
		"""
		return a tuple (unmodifiable) of column names
		"""
		return tuple(self.keys(rescan=False))

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
		@ locked

		Return a list of all items in db
		"""
		return self._pk.items(rescan=rescan)

	@threadsafe_decorator
	def add_column(self, *names, exist_ok=False, AD=True, rescan=True):
		"""
		@ locked

		Add a column to the table

		Args:
				name: name|_PickleTColumn or list of names|_PickleTColumn
				exist_ok:
						- =False then raise KeyError if column already exists
						- =True then `if name` ignore if column already exists. Else raise KeyError
						- =True then`if _PickleTColumn` if column already exists,
						- - exist_ok=True:  ignore if column already exists. (Only checks/add for name, doesn't copy the column)
						- - exist_ok="name": ignore if column already exists. (Only checks/add for name, doesn't copy the column)
						- - exist_ok="overwrite": overwrite it (may add new rows in table if column size is higher)(may add None in column if column size is lower)
				AD: auto-dump
		"""
		self._auto_rescan(rescan=rescan)

		def add(data):
			if isinstance(data, _PyroTColumn):
				name = data.name
				self._pk.validate_key(key=name)

				col = data.to_list()

				tsize = self.height
				csize = len(col)
				diff = tsize - csize

				if name in self.column_names_set:
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
					if exist_ok == True:
						tsize = self.height - len(self._pk.db[name])
						if not tsize:  # 0 cells to add
							return
					else:
						raise KeyError("Column Name already exists")
				else:
					self._pk.db[name] = []
					self.gen_CC()  # major change

				self._pk.db[name].extend([None] * tsize)

			# add to the column names
			self.column_names_set[name] = None  # add to the column names set

		# if the 1st argument is a list, unpack it
		if (isinstance(names[0], Iterable)
				and len(names) == 1
				and not isinstance(names[0], str)
				and not isinstance(names[0], bytes)
				and not isinstance(names[0], _PyroTColumn)
			):
			names = names[0]

		for name in names:
			add(name)

		self.auto_dump(AD=AD)

	add_columns = add_column  # alias

	@threadsafe_decorator
	def del_column(self, name, AD=True, rescan=True):
		"""
		@ locked

		Delete a column from the table

		Args:
				name: column to delete
				AD: auto dump
		"""
		self._auto_rescan(rescan=rescan)
		self._pk.db.pop(name)
		if not self._pk.db:  # has no keys
			self.height = 0

		self.column_names_set.pop(name)  # remove from column names set

		self.auto_dump(AD=AD)

	def _row(self, row, _columns=(), rescan=True):
		"""
		returns a row dict by `row index`

		Args:
				row: row index
				_columns: specify columns you need, blank if you need all
		"""
		self._auto_rescan(rescan=rescan)

		columns = _columns or self.column_names_set
		try:
			return {j: self._pk.db[j][row] for j in columns}
		except IndexError:
			raise IndexError(
				f"Row index out of range, [expected: 0 to {self.height}] [got: {row}]")

	@threadsafe_decorator
	def row(self, row, _columns=(), rescan=True):
		"""
		@ locked

		returns a row dict by `row index`

		Args:
				row: row index
				_columns: specify columns you need, blank if you need all
		"""
		return self._row(row, _columns=_columns, rescan=rescan)

	def row_by_id(self, row_id, _columns=(), rescan=True):
		"""
		returns a COPY row dict by `row_id`

		Args:
				row_id: row id
				_column: specify columns you need, blank if you need all
		"""
		return self.row(self.ids.index(row_id), _columns=_columns, rescan=rescan)

	def row_obj(self, row, loop_back=False) -> "_PyroTRow":
		"""
		Return a row object `_PickleTRow` in db

		Args:
				row: row index
				loop_back: loop back support (circular indexing)
		"""
		if loop_back:
			row = row % self.height
		return _PyroTRow(source=self,
						   uid=self.ids[row],
						   CC=self.CC)

	def row_obj_by_id(self, row_id: int) -> "_PyroTRow":
		"""Return a row object `_PickleTRow` in db
		- row_id: row id
		"""
		return _PyroTRow(source=self,
						   uid=row_id,
						   CC=self.CC)

	def rows(self, start=0, end=None, step=1, loop_back=False, rescan=True) -> Generator[dict, None, None]:
		"""Optimized row generator with minimal overhead."""
		if rescan:
			self.rescan()

		# Fast path for empty table
		if not self.height:
			return

		# Normalize indices (single place)
		if end is None:
			end = self.height
		elif end < 0:
			end = max(0, self.height + end)

		if start < 0:
			start = max(0, self.height + start)

		# Handle loop_back upfront
		if loop_back and (start >= self.height or end > self.height):
			start %= self.height
			end = start + (end - start)  # Maintain distance
			indices = [(start + i) % self.height for i in range(0, end - start, step)]
		else:
			# Boundary checks (fail fast)
			if not 0 <= start < end <= self.height:
				raise IndexError(f"Invalid range [{start}:{end}:{step}] for height {self.height}")
			indices = range(start, end, step)

		# Pre-fetch column names (hot loop optimization)
		columns = self.column_names_set
		db = self._pk.db  # Local variable for faster access

		# Generator with direct dict construction
		for i in indices:
			yield {col: db[col][i] for col in columns}

	def rows_obj(self, start: int = 0, end: int = None, sep: int = 1, loop_back=False, rescan=True) -> Generator["_PyroTRow", None, None]:
		"""Return a list of all rows in db
		- start: start index (default: 0)
		- end: end index (default: None|end of the table)
		- sep: step size (default: 1)
		- loop_back: loop back support (circular indexing)
		"""
		self._auto_rescan(rescan=rescan)

		if sep == 0:
			raise ValueError("sep cannot be zero")

		if end is None:  # end of the table
			end = self.height
		while start < 0:  # negative indexing support
			start = self.height + start
		while end < 0:  # negative indexing support
			end = self.height + end
		if end > self.height or start > self.height:
			if loop_back:  # loop back support (circular indexing)
				ids = []
				distance = end - start
				start = start % self.height

				for i in range(0, distance, sep):
					ids.append(self.ids[(start+i) % self.height])
			else:
				raise IndexError(
					"start/end index out of range, [expected: 0 to", self.height, "] [got:", start, end, "]")

		else:
			ids = self.ids[start:end:sep]

		for id in ids:
			yield self.row_obj_by_id(id)

	def rows_obj(self, start=0, end=None, step=1, loop_back=False, rescan=True) -> Generator['_PyroTRow', None, None]:
		"""Optimized row object generator with direct ID calculation."""
		if rescan:
			self.rescan()

		# Handle empty table case immediately
		if not self.height:
			return

		# Normalize indices once
		if end is None:
			end = self.height
		elif end < 0:
			end = max(0, self.height + end)

		if start < 0:
			start = max(0, self.height + start)

		# Calculate ID sequence directly without temporary lists
		if loop_back and (start >= self.height or end > self.height):
			# Circular access pattern
			for i in range(0, end - start, step):
				pos = (start + i) % self.height
				yield _PyroTRow(self, self.ids[pos], self.CC)
		else:
			# Standard linear access
			if not 0 <= start < end <= self.height:
				raise IndexError(f"Invalid range [{start}:{end}:{step}] for height {self.height}")

			for pos in range(start, end, step):
				yield _PyroTRow(self, self.ids[pos], self.CC)

	def search_iter(
			self,
			kw,
			column: Optional[str] = None,
			row: Optional[int] = None,
			full_match: bool = False,
			return_obj: bool = True,
			rescan: bool = True,
			case_sensitive: bool = False,
			regex: bool = False,
			is_function: bool = False
	) -> Generator["_PyroTCell", None, None]:
		"""
		Search for a keyword in cells, rows, columns, or the entire table, yielding matching cells.

		Args:
				kw: Keyword to search. Can be a value or a function if `is_function` is True.
				column: Optional column name to restrict search to.
				row: Optional row index to restrict search to.
				full_match: Require exact match (default: False).
				return_obj: Return cell objects instead of raw values (default: True).
				rescan: Refresh data before searching (default: True).
				case_sensitive: Case-sensitive string search (default: False).
				regex: Treat `kw` as a regex pattern (default: False).
				is_function: Whether `kw` is a callable function (default: False).

		Yields:
				Matching `_PickleTCell` objects or raw values depending on `return_obj`.

		Example:
				for cell in db.search_iter("abc"):
						print(cell.value)
		"""
		self._auto_rescan(rescan=rescan)

		# Normalize string keyword for case-insensitive search
		if not case_sensitive and isinstance(kw, str):
			kw = kw.lower()

		def check(target):
			"""Return True if `target` matches the search keyword/condition."""
			if target is None:
				return kw is None

			if isinstance(target, str) and not case_sensitive:
				target = target.lower()

			# Handle full match checks
			if full_match:
				if isinstance(kw, str) and isinstance(target, str):
					return bool(re.fullmatch(kw, target, flags=re.IGNORECASE if not case_sensitive else 0)) if regex else target == kw
				return target == kw

			# Handle regex partial match
			if regex and isinstance(kw, str) and isinstance(target, str):
				flags = 0 if case_sensitive else re.IGNORECASE
				return bool(re.search(kw, target, flags))

			# Partial string match
			if isinstance(kw, str) and isinstance(target, str):
				return kw in target

			# Default equality check
			return kw == target

		# Function-based search (custom logic)
		if is_function:
			if not callable(kw):
				raise TypeError("kw must be a function if is_function is True")
			check = kw  # Use the function directly as the check

		# Case 1: Search specific cell
		if column is not None and row is not None:
			cell_value = self.get_cell(column, row, rescan=False)
			if check(cell_value):
				yield self.get_cell_obj(column, row) if return_obj else cell_value
			return

		# Case 2: Column-wide search
		if column is not None:
			for r, cell_value in enumerate(self.column(column, rescan=False)):
				if check(cell_value):
					yield self.get_cell_obj(column, r) if return_obj else cell_value
			return

		# Case 3: Row-wide search
		if row is not None:
			row_data = self.row(row, rescan=False)
			for col, cell_value in row_data.items():
				if check(cell_value):
					yield self.get_cell_obj(col, row) if return_obj else cell_value
			return

		# Case 4: Full-table search
		for col in self.column_names_set:
			for r, cell_value in enumerate(self.column(col, rescan=False)):
				if check(cell_value):
					yield self.get_cell_obj(col, r) if return_obj else cell_value

	def _search_iter(
		self,
		kw,
		column=None,
		row=None,
		full_match=False,
		return_obj=True,
		rescan=True,
		case_sensitive=False,
		regex=False,
		is_function=False
	) -> Generator['_PyroTCell', None, None]:
		"""Optimized search iterator with reduced overhead."""
		if rescan:
			self.rescan()

		# Fast path for empty table
		if not self.height:
			return

		if isinstance(kw, str):
			# Pre-compile regex if needed
			if regex:
				flags = 0 if case_sensitive else re.IGNORECASE
				pattern = re.compile(kw, flags)

			# Normalize case if needed
			elif not case_sensitive:
				kw = kw.lower()

		# Prepare the check function
		if is_function:
			if not callable(kw):
				raise TypeError('kw must be callable when is_function=True')
			check = kw
		elif regex:
			def check(target):
				try:
					return bool(pattern.search(target))
				except Exception:
					return False
		elif full_match:
			def check(target):
				if target is None:
					return kw is None
				if isinstance(target, str) and not case_sensitive:
					target = target.lower()
				return target == kw
		else:
			def check(target):
				if target is None:
					return kw is None
				if isinstance(target, str) and not case_sensitive:
					target = target.lower()
				return kw in target if isinstance(kw, str) else kw == target

		# Optimized search paths
		if column is not None and row is not None:
			# Single cell check
			cell_value = self.get_cell(column, row, rescan=False)
			if check(cell_value):
				yield self.get_cell_obj(column, row) if return_obj else cell_value
			return

		# Get column names to search
		columns = [column] if column is not None else self.column_names_set
		db = self._pk.db  # Local reference for faster access

		if row is not None:
			# Single row check
			row_data = self.row(row, rescan=False)
			for col in columns:
				cell_value = row_data[col]
				if check(cell_value):
					yield self.get_cell_obj(col, row) if return_obj else cell_value
			return

		# Full table scan - most optimized path
		for col in columns:
			column_data = db[col]  # Get entire column once
			for row_idx, cell_value in enumerate(column_data):
				if check(cell_value):
					if return_obj:
						yield _PyroTCell(self, col, self.ids[row_idx], self.CC)
					else:
						yield cell_value

	def search_iter(
		self,
		kw,
		column: Optional[str] = None,
		row: Optional[int] = None,
		full_match: bool = False,
		return_obj: bool = True,
		rescan: bool = True,
		case_sensitive: bool = False,
		regex: bool = False,
		is_function: bool = False,
		limit: int = 0
	) -> Generator["_PyroTCell", None, None]:
		"""
		Search for a keyword in cells, rows, columns, or the entire table, yielding matching cells.

		Args:
				kw: Keyword to search. Can be a value or a function if `is_function` is True.
				column: Optional column name to restrict search to.
				row: Optional row index to restrict search to.
				full_match: Require exact match (default: False).
				return_obj: Return cell objects instead of raw values (default: True).
				rescan: Refresh data before searching (default: True).
				case_sensitive: Case-sensitive string search (default: False).
				regex: Treat `kw` as a regex pattern (default: False).
				is_function: Whether `kw` is a callable function (default: False).

		Yields:
				Matching `_PickleTCell` objects or raw values depending on `return_obj`.

		Example:
				for cell in db.search_iter("abc"):
						print(cell.value)
		"""

		n = 0  # Count of matches found
		for cell in self._search_iter(
				kw,
				column=column,
				row=row,
				full_match=full_match,
				return_obj=return_obj,
				rescan=rescan,
				case_sensitive=case_sensitive,
				regex=regex,
				is_function=is_function
		):
			yield cell
			n += 1
			if limit and n >= limit:
				break

	def search_iter_row(
			self,
			kw,
			column=None,
			row=None,
			full_match=False,
			return_obj=True,
			rescan=True,
			is_function=False,
			case_sensitive=False,
			regex=False,
			limit=0
	) -> Generator[Union["_PyroTRow", dict], None, None]:
		"""
		Search for a keyword and yield matching rows instead of individual cells.

		Args:
				kw: Keyword or function to search for.
				column: Optional column name.
				row: Optional row index.
				full_match: Require exact match (default: False).
				return_obj: Return row object instead of dict (default: True).
				rescan: Rescan before search (default: True).
				is_function: Whether `kw` is a callable function.
				case_sensitive: Case-sensitive string search (default: False).
				regex: Use regular expression search (default: False).

		Yields:
				Matching row objects or dictionaries.
		"""
		# Function-based row search
		if is_function:
			if not callable(kw):
				raise TypeError("kw must be a function if is_function is True")
			if column and row:
				raise ValueError(
					"If is_function is True, column and row must be None")

			self._auto_rescan(rescan=rescan)
			for n_row, _id in enumerate(self.ids):
				_row = self.row(n_row, rescan=False)
				if kw(_row):
					yield self.row_obj_by_id(_id) if return_obj else _row
			return

		# Fallback to cell-based search and yield corresponding row
		for cell in self.search_iter(
				kw, column=column, row=row, full_match=full_match,
				return_obj=True, rescan=rescan, case_sensitive=case_sensitive,
				regex=regex, is_function=is_function
		):
			row_ = cell.row_obj()
			yield row_.to_dict() if not return_obj else row_


	def _search_iter_row(self, kw, column=None, row=None, full_match=False, return_obj=True,
				   rescan=True, is_function=False, case_sensitive=False, regex=False,
				   limit=0) -> Generator[Union['_PyroTRow', dict], None, None]:
		"""Optimized row search iterator with minimal overhead."""
		if is_function:
			if not callable(kw):
				raise TypeError('kw must be callable when is_function=True')

			if rescan:
				self.rescan()

			# Fast path for function-based row searches
			for row_idx, row_id in enumerate(self.ids):
				row_data = self.row(row_idx, rescan=False)
				if kw(row_data):
					yield (self.row_obj_by_id(row_id) if return_obj
						else row_data)

			return

		# Delegate to search_iter for non-function cases
		cell_iter = self.search_iter(
			kw=kw,
			column=column,
			row=row,
			full_match=full_match,
			return_obj=True,  # Always get objects to find rows
			rescan=rescan,
			case_sensitive=case_sensitive,
			regex=regex,
			is_function=False
		)

		for cell in cell_iter:
			row_id = cell.id
			yield (cell.row_obj() if return_obj
				else self.row_by_id(row_id, rescan=False))


	def search_iter_row(
			self,
			kw,
			column=None,
			row=None,
			full_match=False,
			return_obj=True,
			rescan=True,
			is_function=False,
			case_sensitive=False,
			regex=False,
			limit=0
	) -> Generator[Union["_PyroTRow", dict], None, None]:
		"""
		Search for a keyword and yield matching rows instead of individual cells.

		Args:
				kw: Keyword or function to search for.
				column: Optional column name.
				row: Optional row index.
				full_match: Require exact match (default: False).
				return_obj: Return row object instead of dict (default: True).
				rescan: Rescan before search (default: True).
				is_function: Whether `kw` is a callable function.
				case_sensitive: Case-sensitive string search (default: False).
				regex: Use regular expression search (default: False).

		Yields:
				Matching row objects or dictionaries.
		"""
		n = 0  # Count of matches found
		for row_ in self._search_iter_row(
				kw,
				column=column,
				row=row,
				full_match=full_match,
				return_obj=return_obj,
				rescan=rescan,
				is_function=is_function,
				case_sensitive=case_sensitive,
				regex=regex,
				limit=limit
		):
			yield row_
			n += 1
			if limit and n >= limit:
				break
		# If limit is reached, stop iteration


	def search(
			self,
			kw,
			column=None,
			row=None,
			full_match=False,
			return_obj=True,
			return_row=False,
			rescan=True,
			is_function=False,
			case_sensitive=False,
			regex=False,
			limit=0
	) -> List[Union["_PyroTCell", "_PyroTRow", Any]]:
		"""
		Search for a keyword in a cell, row, column, or the entire table.

		Args:
				kw: Keyword to search (can be a value, string, or function if `is_function` is True).
				column: Column name to restrict search to (optional).
				row: Row index to restrict search to (optional).
				full_match: Require exact match instead of partial match (default: False).
				return_obj: If True, return object instances; otherwise, return raw values (default: True).
				return_row: If True, return the entire row containing the matched cell (default: False).
				rescan: Whether to refresh table data before searching (default: True).
				is_function: If True, treat `kw` as a function for filtering (default: False).
				case_sensitive: Whether string search is case-sensitive (default: False).
				regex: If True, treat `kw` as a regex pattern (default: False).

		Returns:
				A list of matched cell objects, values, or rows depending on flags.
		"""
		ret = []

		for cell in self.search_iter(
				kw,
				column=column,
				row=row,
				full_match=full_match,
				return_obj=True,  # Always get cell obj to fetch row if needed
				rescan=rescan,
				case_sensitive=case_sensitive,
				regex=regex,
				is_function=is_function,
				limit=limit
		):
			if return_row:
				row_ = cell.row_obj()
				ret.append(row_ if return_obj else row_.to_dict())
			else:
				ret.append(cell if return_obj else cell.value)

		return ret

	def find_1st(
			self,
			kw,
			column=None,
			row=None,
			full_match=False,
			return_obj=True,
			rescan=True,
			is_function=False,
			case_sensitive=False,
			regex=False
	) -> Union["_PyroTCell", Any, None]:
		"""
		Return the first matched cell for the given search.

		Args:
				kw: Keyword to search.
				column: Column name to restrict search to.
				row: Row index to restrict search to.
				full_match: Require exact match.
				return_obj: If True, return cell object; else return value.
				rescan: Whether to refresh the data.
				is_function: Treat `kw` as a callable to apply to each cell.
				case_sensitive: Case-sensitive matching for strings.
				regex: Use regex pattern for string matching.

		Returns:
				First matching cell (object or value), or None if not found.
		"""
		if column and column not in self.column_names_set:
			raise KeyError("Invalid column name:", column,
						   '\nAvailable columns:', list(self.column_names_set))

		for cell in self._search_iter(
				kw,
				column=column,
				row=row,
				full_match=full_match,
				return_obj=return_obj,
				rescan=rescan,
				case_sensitive=case_sensitive,
				regex=regex,
				is_function=is_function
		):
			return cell  # First match

		return None

	def find_1st_row(
			self,
			kw,
			column=None,
			row=None,
			full_match=False,
			return_obj=True,
			rescan=True,
			is_function=False,
			case_sensitive=False,
			regex=False
	) -> Union["_PyroTRow", Dict[Any, Any], None]:
		"""
		Return the first matched row for the given search.

		Args:
				kw: Keyword to search.
				column: Column name to restrict search to.
				row: Row index to restrict search to.
				full_match: Require exact match.
				return_obj: If True, return row object; else return row as dict.
				rescan: Whether to refresh the data.
				is_function: Treat `kw` as a callable to apply to each row.
				case_sensitive: Case-sensitive matching for strings.
				regex: Use regex pattern for string matching.

		Returns:
				First matching row (object or dict), or None if not found.
		"""
		if column and column not in self.column_names_set:
			raise KeyError("Invalid column name:", column,
						   '\nAvailable columns:', list(self.column_names_set))

		for row_ in self.search_iter_row(
				kw,
				column=column,
				row=row,
				full_match=full_match,
				return_obj=return_obj,
				rescan=rescan,
				is_function=is_function,
				case_sensitive=case_sensitive,
				regex=regex
		):
			return row_

		return None

	def _set_cell(self, col, row, val, AD=True, rescan=True) -> bool:
		"""
		[Thread Unsafe]
		Set the value of a cell in the database.

		Args:
			col (str): The column name where the value will be set.
			row (int): The row index of the cell.
			val (Any): The value to assign to the cell.
			AD (bool, optional): If True, automatically dump changes after setting the value. Defaults to True.
			rescan (bool, optional): If True, perform a rescan before setting the value. Defaults to True.

		Returns:
			bool: True if the operation was successful.

		Example:
		```python
		db.set_cell("name", 0, "John")
		```
		"""
		self._auto_rescan(rescan=rescan)

		try:
			self._pk.db[col][row] = val
		except KeyError:
			raise KeyError("Invalid column name:", col,
						   "\nAvailable columns:", list(self.column_names_set))
		except IndexError:
			raise IndexError("Invalid row index:", row,
							 "\nAvailable rows: (upto)", self.height)

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

	@threadsafe_decorator
	def batch_set_cells(self, updates: List[Tuple[str, int, Any]], AD=True, rescan=True):
		"""Set multiple cells with a single lock"""
		self._auto_rescan(rescan=rescan)
		for col, row, val in updates:
			self._set_cell(col, row, val, AD=False, rescan=False)
		self.auto_dump(AD=AD)

	def _get_cell(self, col, row, rescan=True):
		"""
		[Thread Unsafe]
		Retrieve the value of a cell from the specified column and row index.

		Args:
			col (str): The name of the column from which to retrieve the value.
			row (int): The index of the row from which to retrieve the value.
			rescan (bool, optional): Whether to rescan the data before retrieving the value. Defaults to True.

		Returns:
			Any: The value stored in the specified cell.

		Raises:
			KeyError: If the specified column name does not exist.
			IndexError: If the specified row index is out of range.
		"""
		self._auto_rescan(rescan=rescan)

		try:
			_col = self._pk.db[col]
		except KeyError:
			raise KeyError("Invalid column name:", col,
						   "\nAvailable columns:", list(self.column_names_set))
		try:
			cell = _col[row]
		except IndexError:
			raise IndexError("Invalid row index:", row,
							 "\nAvailable rows:", self.height)

		return cell

	@threadsafe_decorator
	def get_cell(self, col: str, row: int, rescan=True):
		"""
		Retrieve the value of a specific cell in the database by column name and row index.

		Parameters:
			col (str): The name of the column from which to retrieve the value.
			row (int): The index of the row from which to retrieve the value.
			rescan (bool, optional): Whether to rescan the data before retrieving the value. Defaults to True.

		Returns:
			Any: The value stored in the specified cell.

		Note:
			This method only retrieves the cell value and does not modify the database.
		"""
		return self._get_cell(col, row, rescan=rescan)

	def get_cell_by_id(self, col: str, row_id: int, rescan=True):
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

	def get_cell_obj(self, col: str, row: int = None, row_id: int = None, rescan=True) -> "_PyroTCell":
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
		self._auto_rescan(rescan=rescan)

		if not isinstance(col, str) or col not in self.column_names_set:
			raise KeyError("Invalid column name:", col,
						   '\nAvailable columns:', list(self.column_names_set))

		if row is None and row_id is None:
			raise ValueError("Either row or row_id must be given")

		if row is not None and row_id is not None:
			raise ValueError("Either row or row_id must be given, not both")

		if row is None:
			if not isinstance(row_id, int):
				raise TypeError("row_id must be an integer")
			if row_id not in self.ids:
				raise IndexError(f"Missing row_id. [got: {row_id}]")

		elif row_id is None:
			if not isinstance(row, int):
				raise TypeError("row must be an integer")

			if row >= self.height or row < -self.height:
				raise IndexError(
					f"Invalid row index. [expected: 0 to {self.height-1} | -{self.height}] [got: {row}]")
			if row < 0:
				row = self.height + row

			row_id = self.ids[row]

		return _PyroTCell(self, column=col, row_id=self.ids[row], CC=self.CC)

		# in case row or row_id is invalid
		raise IndexError("Invalid row")

	@threadsafe_decorator
	def pop_row(self, index: int = -1, returns=True, AD=True, rescan=True) -> Union[dict, None]:
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
		self._auto_rescan(rescan=rescan)

		box = None
		if returns:
			box = self.row(index)

		for c in self.column_names_set:
			self._pk.db[c].pop(index)

		self.ids.pop(index)

		self.height -= 1

		self.auto_dump(AD=AD)

		return box

	def del_row(self, row: int, AD=True, rescan=True):
		"""
		Delete a row from the table (by row index)
		- row: row index
		- AD: auto dump
		"""
		# Auto dumps (locked)
		self.pop_row(row, returns=False, AD=AD, rescan=rescan)

	def del_row_id(self, row_id: int, AD=True, rescan=True):
		"""
		Delete a row from the table (by row_id)
		- row_id: unique id of the row
		- AD: auto dump
		- rescan: rescan the db if changes are made
		"""
		self.del_row(self.ids.index(row_id), AD=AD, rescan=rescan)

	@threadsafe_decorator
	def clear(self, AD=True, rescan=True):
		"""
		@ locked

		Delete all rows
		- AD: auto dump
		"""
		self._auto_rescan(rescan=rescan)

		for c in self.column_names_set:
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

		for c in self.column_names_set:
			self._pk.db.pop(c)

		self.auto_dump(AD=AD)

		return self

	def _copy(self, location='', auto_dump=True, sig=True) -> "PyroTable":
		"""
		@ locked

		Copy the table to a new location/memory
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""

		new = PyroTable(location, auto_dump=auto_dump, sig=sig)
		new._pk.db = datacopy.deepcopy(self.__db__())
		new.height = self.height
		# new.ids = self.ids.copy()
		new.refresh_ids(self.ids.copy())
		new.column_names_set = self.column_names_set.copy()

		return new

	@threadsafe_decorator
	def copy(self, location='', auto_dump=True, sig=True) -> "PyroTable":
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
	def add_row(self, row: Union[dict, "_PyroTRow"], position: int = None, rescan=True, AD=True) -> "_PyroTRow":
		"""
		Add a row to the table (internal use, no auto dump).

		Parameters:
			row (Union[dict, "_PyroTRow"]): The row data to add, as a dictionary or _PyroTRow object, containing column names and values.
			position (int, optional): The position at which to insert the row. Defaults to None (appends to the end). Negative values count from the end.
			rescan (bool, optional): Whether to rescan the database if changes are made. Defaults to True.
			AD (bool, optional): Whether to auto dump after adding the row. Defaults to True.

		Returns:
			_PyroTRow: The row object corresponding to the newly added row.

		Raises:
			IndexError: If the specified position is out of the valid range [0, height].
		"""
		# self._auto_rescan(rescan=rescan)
		self.rescan()

		row_id = self._generate_uuid()  # generate a unique id for the row

		append = False
		# Handle position
		if position is None:
			append = True

		else:
			if position < 0:
				position = self.height + position

			# Clamp position to [0, height]
			if position < 0 or position > self.height:
				raise IndexError(
					f"Position out of range, [expected: 0 to {self.height}] [got: {position}]")
			elif position == self.height:
				append = True

		if append:
			self.ids.append(row_id)
			for k in self.column_names_set:
				self._pk.db[k].append(row.get(k))

		else:
			self.ids.insert(position, row_id)
			for k in self.column_names_set:
				self._pk.db[k].insert(position, row.get(k))

		self.height += 1

		self.auto_dump(AD=AD)

		return self.row_obj_by_id(row_id)

	def insert_row(self, row: Union[dict, "_PyroTRow"], position: int = None, AD=True) -> "_PyroTRow":
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

	def add_row_as_list(self, row: list, position: int = None, AD=True, rescan=True) -> "_PyroTRow":
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
		row_obj = self.add_row(row={k: v for k, v in zip(
			self.column_names_set, row)}, position=position, rescan=rescan, AD=AD)

		return row_obj

	def add_rows(self, rows: List[Union[dict, "_PyroTRow"]], position: int = None, rescan=True, AD=True) -> List["_PyroTRow"]:
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
		self._auto_rescan(rescan=rescan)
		ret = []
		for row in rows:
			row_obj = self.add_row(
				row=row, position=position, AD=False, rescan=False)
			ret.append(row_obj)

		self.auto_dump(AD=AD)
		return ret

	def add_rows_as_list(self, rows: List[list], position: int = None, AD=True, rescan=True) -> List["_PyroTRow"]:
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
		self._auto_rescan(rescan=rescan)

		ret = []
		for row in rows:
			row_obj = self.add_row_as_list(
				row=row, position=position, AD=False, rescan=False)
			# increment position for next row
			position = row_obj.index() + 1
			ret.append(row_obj)

		self.auto_dump(AD=AD)
		return ret

	@threadsafe_decorator
	def sort(self, column=None, key=None, reverse=False, row_object_key_arg=False, copy=False, AD=True, rescan=True):
		"""
		Sorts the database rows based on a specified column, key function, or all values.

		Parameters:
			column (str, list, tuple, optional): The column name or list/tuple of column names to sort by.
				If None, sorts by all values in each row.
			key (callable, optional): A function that takes a row (dict) and returns a value to sort by.
				If provided, overrides the column parameter.
			reverse (bool, optional): If True, sort in descending order. Defaults to False (ascending).
			case_sensitive (bool, optional): If True, string comparisons are case-sensitive. Defaults to False.
			copy (bool or str, optional): If True or a string, returns a copy of the database sorted.
				If a string, it is used as the location for the copy. If False, sorts in place.
			AD (bool, optional): If True, auto-dump is triggered after sorting. Defaults to True.
			rescan (bool, optional): If True, rescans the database before sorting. Defaults to True.

		Returns:
			db: The sorted database object (either a copy or self, depending on the 'copy' parameter).

		Raises:
			KeyError: If a specified column name does not exist in the database.

		Notes:
			- Sorting handles None, bool, numeric, and string types consistently.
			- For multiple columns, sorts by a tuple of their values.
			- If both 'column' and 'key' are None, sorts by all values in each row.

		Work Procedure:
		1. Rescans the database if `rescan` is True.
		2. If `copy` is True, creates a copy of the database.
		3. Defines a `type_sort_key` function to create consistent sort keys for different data types.
		4. Defines a `get_cell` function to retrieve the sort key for each row based on the specified column or key.
		5. Sorts the row indices based on the sort keys generated by `get_cell`.
		6. Reorders the database columns and IDs based on the sorted indices. (NOTE TO SELF: SO, LAST ID MAY NOT BE THE HIGHEST ID)
		7. Returns the sorted database (either a copy or self).
		"""
		self._auto_rescan(rescan=rescan)
		if copy:
			if copy is True:
				copy = ''
			db = self._copy(location=copy, auto_dump=self._pk.auto_dump, sig=self._pk.sig)
		else:
			db = self

		def type_sort_key(value):
			if value is None:
				return (0,)
			if isinstance(value, bool):
				return (1, value)
			if isinstance(value, (int, float)):
				return (2, value)
			if isinstance(value, str):
				return (3, value.lower())
			return (4, str(value))

		def function_sort_key(row: "_PyroTRow"):
			"""If key is a function, apply it to the row object"""
			try:
				return key(row)
			except Exception as e:
				TypeError(f"Error applying key function: {e}")

		def build_sort_key(row: Union[dict, "_PyroTRow"]):
			if column:
				if isinstance(column, (list, tuple)):
					return tuple(type_sort_key(row.get(col)) for col in column)
				if column not in row:
					raise KeyError(f"Invalid column name: {column}")
				return type_sort_key(row.get(column))
			return tuple(type_sort_key(v) for v in row.values())

		# Step 1: Build index and key pairs
		if key and isinstance(key, FunctionType):
			# If key is a function, use it to build sort keys
			index_and_key = [
				(i, function_sort_key(row))
				for i, row in enumerate(db.rows_obj(rescan=False)
				if row_object_key_arg
				else db.rows(rescan=False))
			]
		else:
			index_and_key = [
				(i, build_sort_key(row))
				for i, row in enumerate(db.rows_obj(rescan=False)
				if row_object_key_arg
				else db.rows(rescan=False))
			]


		# Step 2: Sort the index/key pair
		index_and_key.sort(key=lambda x: x[1], reverse=reverse)
		# Step 3: Extract sorted ids directly
		db.refresh_ids([db.ids[i] for (i, _) in index_and_key])

		# Step 4: In-place reorder each column
		for col in db.column_names_set:
			col_data = db._pk.db[col]
			db._pk.db[col][:] = [col_data[i] for (i, _ )in index_and_key]

		db.auto_dump(AD=AD)
		return db



	def remove_duplicates(self, columns=None, AD=True, rescan=True):
		"""
		Remove duplicate rows (keep the 1st occurrence)
		- columns: columns to check for duplicates (default: all columns) (if None, all columns are checked) (if string, only that column is checked) (if list, all the mentioned columns are checked)
		- AD: auto dump
		"""
		self._auto_rescan(rescan=rescan)

		if columns is None:
			columns = self.column_names_set
		if isinstance(columns, str):
			columns = [columns]

		# print(columns)

		if not self or not columns:
			return

		def get_next(row: "_PyroTRow"):
			try:
				return row.next()
			except IndexError:
				return None

		row = self.row_obj(0)

		seen_rows = set()
		while row is not None:
			row_key = tuple(row.get(col, rescan=False) for col in columns)
			if row_key in seen_rows:
				next_row = get_next(row)
				row.del_row(AD=False, rescan=False)
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
			raise SourceNotFoundError(
				"Database has been updated drastically. Row index/Columns will mismatch!")

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

	def to_json(self, filepath=None, indent=4, format: Literal['list', 'dict'] = 'list') -> str:
		"""
		Write the table to a json file
		- filepath: path to the file (if None, use current filepath.json) (if in memory and not provided, uses "table.json")
		- indent: indentation level (default: 4 spaces)
		- format: format of the json file (default: list) [options: `"list"|"dict"|list|dict`]
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
				raise AttributeError(
					"Invalid format. [expected: list|dict] [got:", format, "]")

		return os.path.realpath(path)

	def to_json_str(self, indent=4) -> str:
		"""
		Return the table as a json string
		"""
		return json.dumps(self.__db__(), indent=indent)

	def _load_json(self, filepath="", iostream=None, json_str=None, ignore_new_headers=False, on_file_not_found='error', keep_columns=True, AD=True):
		# if more than one source is provided
		sources = [i for i in [filepath, iostream, json_str] if i]
		if len(sources) > 1:
			raise AttributeError(
				f"Only one source is allowed. Got: {len(sources)}")

		# if no source is provided
		if not sources:
			raise AttributeError("No source provided")

		if json_str:
			# load it as io stream
			iostream = io.StringIO(json_str)

		if not ((filepath and os.path.isfile(filepath)) or (iostream and isinstance(iostream, io.IOBase))):
			if on_file_not_found == 'error':
				raise FileNotFoundError(f"File not found: {filepath}")

			elif on_file_not_found == 'ignore':
				return
			else:
				self.clear(AD=AD, rescan=False)
				if on_file_not_found == 'warn':
					logger.warning(
						f"File not found: {filepath}. Cleared the table.")
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

		if not data:
			return

		if isinstance(data, dict):
			# column names are keys
			self.add(table=data,
					 add_extra_columns=not ignore_new_headers,
					 AD=AD,
					 rescan=False,
					 )

		elif isinstance(data, list):
			# per row
			for row in data:
				if not ignore_new_headers:
					self.add_column(*row.keys(), exist_ok=True,
									AD=False, rescan=False)

				self.add_row(row, rescan=False, AD=False)

		self.auto_dump(AD=AD)

	@threadsafe_decorator
	def load_json(self, filepath="", iostream=None, json_str=None, ignore_new_headers=False, on_file_not_found='error', keep_columns=True, AD=True):
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
		- keep_columns: keep the existing columns (default: `True`) (if `False`, clears the table)
		- AD: auto dump
		"""
		with FileLock(filepath + '.lock'):
			self._load_json(filepath=filepath, iostream=iostream, json_str=json_str,
							ignore_new_headers=ignore_new_headers, on_file_not_found=on_file_not_found,
							keep_columns=keep_columns, AD=AD)

	@threadsafe_decorator
	def to_csv(self, filepath=None, write_header=True, rescan=True) -> str:
		"""
		Write the table to a csv file
		- filepath: path to the file (if None, use current filepath.csv) (if in memory and not provided, uses "table.csv")
		- write_header: write column names as header (1st row) (default: `True`)
		- AD: auto dump
		- rescan: rescan the db if changes are made

		- return: path to the file
		"""
		self._auto_rescan(rescan=rescan)

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

			columns = list(self.column_names_set)
			if write_header:
				writer.writerow(columns)  # header
			for row in self.rows(rescan=False):
				writer.writerow([row[k] for k in columns])

		return os.path.realpath(path)


	def to_csv_str(self, write_header=True) -> str:
		"""
		Return the table as a csv string
		- write_header: write column names as header (1st row) (default: `True`)
		"""
		output = io.StringIO()
		writer = csv.writer(output)

		columns = list(self.column_names_set)
		if write_header:
			writer.writerow(columns)  # header
		for row in self.rows():
			writer.writerow([row[k] for k in columns])

		return output.getvalue()

	def _load_csv(self, filepath=None, iostream=None, csv_str=None,
				 header: Union[bool, Literal["auto"]] = True, ignore_none=False, ignore_new_headers=False, on_file_not_found='error', AD=True):
		columns_names = self.column_names_set

		def add_row(row, columns):
			if ignore_none and all((v is None or v == '') for v in row):
				return

			new_row = {k: v for k, v in zip(columns, row)}

			self.add_row(new_row, AD=False, rescan=False)

		# if more than one source is provided
		sources = [i for i in [filepath, iostream, csv_str] if i]
		if len(sources) > 1:
			raise AttributeError(
				f"Only one source is allowed. Got: {len(sources)}")

		if not sources:
			raise AttributeError("No source provided")

		if csv_str:
			# load it as io stream
			iostream = io.StringIO(csv_str)

		if not ((filepath and os.path.isfile(filepath)) or (iostream and isinstance(iostream, io.IOBase))):
			if on_file_not_found == 'error':
				raise FileNotFoundError(f"File not found: {filepath}")

			elif on_file_not_found == 'ignore':
				return
			else:
				self.clear(AD=AD, rescan=False)
				if on_file_not_found == 'warn':
					logger.warning(
						f"File not found: {filepath}. Cleared the table.")
				if on_file_not_found == 'no_warning':
					pass

				return

		self.clear(AD=False, rescan=False)

		def fix_BOM(f: io.TextIOBase) -> io.TextIOBase:
			"""
			Checks if the file-like object f (assumed to be in text mode)
			starts with a UTF-8 BOM. If found, it removes it by repositioning
			the stream so that the BOM is skipped.
			"""
			# Read the first character; if it's not a BOM, rewind.
			first_char = f.read(1)
			if first_char != "\ufeff":
				f.seek(0)
			return f

		def load_as_io(f):
			f = fix_BOM(f)

			reader = csv.reader(f)
			if header is True:
				columns = next(reader)
				updated_columns = []
				n = len(self.column_names_set)

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
				self.add_column(updated_columns, exist_ok=True,
								AD=False, rescan=False)

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

				self.add_column(new_columns, exist_ok=True,
								AD=False, rescan=False)
				columns = new_columns

				add_row(row, columns)  # add the first row
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

				self.add_column(new_columns, exist_ok=True,
								AD=False, rescan=False)
				columns = new_columns

				add_row(row, columns)  # add the first row

			for row in reader:
				add_row(row, columns)

		if filepath:
			with open(filepath, 'r', encoding='utf8') as f:
				load_as_io(f)
		elif iostream:
			load_as_io(iostream)

		self.auto_dump(AD=AD)

	@threadsafe_decorator
	def load_csv(self, filepath=None, iostream=None, csv_str=None,
				 header: Union[bool, Literal["auto"]] = True, ignore_none=False, ignore_new_headers=False, on_file_not_found='error', AD=True):
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

		with FileLock(filepath + '.lock'):
			self._load_csv(filepath=filepath, iostream=iostream, csv_str=csv_str,
						  header=header, ignore_none=ignore_none,
						  ignore_new_headers=ignore_new_headers,
						  on_file_not_found=on_file_not_found, AD=AD)

	@staticmethod
	def from_json(filepath="", iostream=None, json_str=None, location="", auto_dump=True, sig=True) -> "PyroTable":
		"""
		Load a json file to a new table
		- filepath: path to the file
		- iostream: io stream object (use either filepath or iostream)
		- json_str: json string
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""

		db = PyroTable(location, auto_dump=auto_dump, sig=sig)
		db.load_json(filepath=filepath, iostream=iostream,
					 json_str=json_str, AD=False)

		return db

	@staticmethod
	def from_csv(filepath=None, iostream=None, csv_str=None, header=True, location='', auto_dump=True, sig=True) -> "PyroTable":
		"""
		Load a csv file to a new table
		- filepath: path to the file
		- iostream: io stream object (use either filepath or iostream)
		- csv_str: csv string
		- header:
				* if True, the first row will be considered as column names
				* if False, the columns will be named as "Unnamed-1", "Unnamed-2", ...
				* if "auto", the columns will be named as "A", "B", "C", ..., "Z", "AA", "AB", ...
		- location: new location of the table (default: `None`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""
		db = PyroTable(location, auto_dump=auto_dump, sig=sig)
		db.load_csv(filepath=filepath, iostream=iostream,
					csv_str=csv_str, header=header, AD=False)

		return db

	@staticmethod
	def from_rows(rows: List[dict], location='', auto_dump=True, sig=True) -> "PyroTable":
		"""
		Load a list of rows to a new table
		- rows: list of rows (dict)
		- location: new location of the table (default: `""`->`in-memory`)
		- auto_dump: auto dump on change (default: `True`)
		- sig: Add signal handler for graceful shutdown (default: `True`)
		- return: new PickleTable object
		"""
		db = PyroTable(location, auto_dump=auto_dump, sig=sig)

		# get all columns
		columns = set()
		for row in rows:
			columns.update(row.keys())

		db.add_column(columns, exist_ok=True, AD=False, rescan=False)

		db.add_rows(rows)

		return db

	def extend(self, other: "PyroTable", add_extra_columns=None, AD=True, rescan=True):
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
			raise TypeError(
				"Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(other).__name__))

		self._auto_rescan(rescan=rescan)

		keys = list(other.column_names)
		this_keys = self.column_names

		if add_extra_columns:
			self.add_column(*keys, exist_ok=True, AD=False, rescan=False)
		else:
			for key in keys:
				if key not in this_keys:
					if add_extra_columns is False:
						keys.remove(key)
					else:
						raise ValueError(
							"Both tables must have same column names"
						)

		for row in other:
			self.add_row({k: row[k] for k in keys}, AD=False, rescan=False)

		self.auto_dump(AD=AD)

	def add(self, table: Union["PyroTable", dict], add_extra_columns=None, AD=True, rescan=True):
		"""
		Add another table to this table
		- table: PickleTable object or dict
		- add_extra_columns: add extra columns if not exists (default: `None`-> raise error if columns mismatch)
				- if True, add extra columns
				- if False, ignore extra columns
				- if None, raise error if columns mismatch (default)
		- AD: auto dump
		"""
		self._auto_rescan(rescan=rescan)

		if isinstance(table, dict) or isinstance(table, type(self)):
			keys = list(table.keys())
		else:
			raise TypeError(
				"Unsupported operand type(s) for +: 'PickleTable' and '{}'".format(type(table).__name__))

		table_type = "PickleTable" if isinstance(table, type(self)) else "dict"
		if table_type == "PickleTable":
			table._auto_rescan(rescan=rescan)

		if table_type == "PickleTable":
			return self.extend(table, add_extra_columns=add_extra_columns, AD=False, rescan=False)

		this_keys = self.column_names
		if add_extra_columns:
			self.add_column(*keys, exist_ok=True, AD=False, rescan=False)
		else:
			for key in keys:
				if key not in this_keys:
					if add_extra_columns is False:
						keys.remove(key)
					else:
						raise ValueError(
							f"Columns mismatch: {this_keys} != {keys}")

		max_height = 0
		for key, value in table.items():
			if not isinstance(value, (list, tuple)):
				raise TypeError(
					f"Value type must be a list/tuple. Got: {type(value).__name__} for key: {key}")

			max_height = max(max_height, len(value))

		for i in range(max_height):
			if table_type == "dict":
				row = {k: table[k][i] if i < len(
					table[k]) else None for k in keys}

			self.add_row(row, AD=False, rescan=False)

		self.auto_dump(AD=AD)


class _PyroTCell:
	def __init__(self, source: PyroTable, column, row_id: int, CC):
		self.source = source
		self.id = row_id
		self.column_name = column
		self.CC = CC
		self.deleted = False

	@property
	def value(self) -> Any:
		return self.get_value()

	def get_value(self, rescan=True):
		"""
		return the value of the cell
		"""
		self.source_check()

		return self.source.get_cell_by_id(self.column_name, self.id, rescan=rescan)

	def is_deleted(self):
		"""
		return True if the cell is deleted, else False
		"""
		self.deleted = self.deleted or (self.id not in self.source.ids) or (
			self.column_name not in self.source.column_names_set)

		return self.deleted

	def raise_deleted(self):
		"""
		Raise error if the cell is deleted
		"""
		if self.is_deleted():
			raise DeletedObjectError(
				f"Cell has been deleted. Invalid cell object.\n(last known id: {self.id}, column: {self.column_name})")

	def source_check(self, checked=False):
		"""
		Raise error if the source is not verified/mismatched
		"""
		if checked:
			return True
		self.source.raise_source(self.CC)
		self.raise_deleted()

		return True

	def __str__(self):
		return str({
			"value": self.value,
			"column": self.column_name,
			"row": self.row
		})

	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return self.value == other.value

		return self.value == other

	def __ne__(self, other):
		return not self.__eq__(other)

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return self.value < other.value

		return self.value < other

	def __le__(self, other):
		return self.__eq__(other) or self.__lt__(other)

	def __gt__(self, other):
		if isinstance(other, self.__class__):
			return self.value > other.value

		return self.value > other

	def __ge__(self, other):
		return self.__eq__(other) or self.__gt__(other)

	def __contains__(self, item):
		return item in self.value

	def set(self, value, AD=True, rescan=True):
		"""
		Set the `value` of the cell
		"""
		self.source_check()

		self.source.set_cell_by_id(
			self.column_name, self.id, val=value, AD=AD, rescan=rescan)

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

	def row_obj(self) -> "_PyroTRow":
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

	def clear(self, AD=True, rescan=True):
		"""Clear the cell value"""
		self.source_check()

		self.source.set_cell_by_id(
			self.column_name, self.id, None, AD=AD, rescan=rescan)

	delete = clear
	remove = clear


class _PyroTRow(dict):
	def __init__(self, source: PyroTable, uid, CC):
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
			raise DeletedObjectError(
				f"Row has been deleted. Invalid row object (last known id: {self.id})")

	def source_check(self, checked=False):
		"""
		Raise error if the source is not verified/mismatched
		"""
		if checked:
			return True
		self.source.raise_source(self.CC)
		self.raise_deleted()

		return True

	def __getitem__(self, name):
		self.source_check()

		return self._get(name, rescan=True)

	def __bool__(self):
		"""
		return True if the row has values
		"""
		return any(self.values())

	def to_dict(self):
		"""
		returns a copy of the row as dict
		"""
		self.source_check()

		return self.source.row_by_id(self.id, rescan=False)

	def _get(self, name, rescan=True):
		"""
		returns the value of the cell in the row (Raises KeyError if not found)

		Args:
				name: column name
				rescan: rescan the table for the column names
		"""
		self.source_check()

		return self.source.get_cell_by_id(name, self.id, rescan=rescan)

	def get(self, name, default=None, rescan=True):
		"""
		returns the value of the cell in the row [if found, else default]

		Args:
				name: column name
				default: default value if the column is not found
				rescan: rescan the table for the column names
		"""
		self.source_check()

		if name not in self.source.column_names_set:
			return default

		return self.source.get_cell_by_id(name, self.id, rescan=rescan)

	def get_cell_obj(self, name, default=None, rescan=True):
		self.source_check()
		if name not in self.source.column_names_set:
			return default

		return self.source.get_cell_obj(col=name, row_id=self.id, rescan=rescan)

	def set_item(self, name, value, AD=True, rescan=True, source_checked=False, debug=False):
		"""
		* name: column name
		* value: accepts both raw value and _PickleTCell obj
		* AD: auto dump
		"""
		# Auto dumps
		if debug:
			print(f"Setting item: {name} = {value} (AD={AD}, rescan={rescan})")
		sc = self.source_check(source_checked)
		if debug:
			print(f"Source check passed: {sc}")
		self.source.raise_source(self.CC)
		if debug:
			print(f"Row CC: {self.CC} (source: {self.source.CC})")

		if isinstance(value, _PyroTCell):
			value = value.value

		if debug:
			logger.debug(f"Setting cell: {name} = {value} (id={self.id}), AD={AD}, rescan={rescan})")

		self.source.set_cell_by_id(name, self.id, value, AD=AD, rescan=rescan)
		if debug:
			logger.debug(f"Cell set: {name} = {value} (id={self.id})")

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
		self.source_check()

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
		self.source_check()
		return self.source.ids.index(self.id)

	def update(self, new: Union[dict, "_PyroTRow"], ignore_extra=False, AD=True):
		"""
		Update the row with new values
		- new: dict of new values
		- ignore_extra: ignore extra keys in new dict
		- AD: Auto dumps
		"""
		self.source_check()

		for k, v in new.items():
			try:
				self.source.set_cell(
					k, self.source.ids.index(self.id), v, AD=False)
			except KeyError:
				if not ignore_extra:
					raise

		self.source.auto_dump(AD=AD)

	def __str__(self):
		return "<PickleTable._PickleTRow object> " + str(self.to_dict())

	def __repr__(self):
		return str(self.to_dict())

	def keys(self):
		self.source_check()
		return self.source.column_names_set

	def values(self):
		return [self[k] for k in self.keys()]

	def items_iter(self, rescan=True):
		for k in self.keys():
			yield (k, self.__getitem__(k))

	def items(self):
		return list(self.items_iter())

	def next(self, loop_back=False):
		"""
		returns the next row object
		"""
		pos = self.index()+1
		if loop_back:
			pos = pos % self.source.height
		return self.source.row_obj(pos)

	def del_row(self, AD=True, rescan=True):
		"""
		Delete the row
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		# Auto dumps
		self.source_check()

		self.source.del_row_id(self.id, AD=AD, rescan=rescan)

		self.deleted = False

	def to_list(self) -> list:
		"""
		returns the row as list
		"""
		self.source_check()

		return [self[k] for k in self.source.column_names]

	def to_json(self) -> str:
		"""
		returns the row as json string
		"""
		self.source_check()

		return json.dumps(self.to_dict(), indent=4)

	def apply(self, func, *args, **kwargs):
		"""
		apply a function to the row
		- func: function to apply
		- args: arguments to pass to the function
		- kwargs: keyword arguments to pass to the function

		called as:
		```python
		row.apply(func, *args, **kwargs)
		```
		under the hood:
		```python
		func(row, *args, **kwargs)
		```
		"""
		self.source_check()

		return func(self, *args, **kwargs)

	def __eq__(self, other):
		self.source_check()
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
		self.source_check()
		return not self.__eq__(other)


class _PyroTColumn(list):
	def __init__(self, source: PyroTable, name, CC):
		self.source = source
		self.name = name
		self.CC = CC
		self.deleted = False

	def is_deleted(self):
		"""
		return True if the column is deleted, else False
		"""
		self.deleted = self.deleted or (
			self.name not in self.source.column_names_set)

		return self.deleted

	def raise_deleted(self):
		"""
		Raise error if the column is deleted
		"""
		if self.is_deleted():
			raise DeletedObjectError(
				f"Column has been deleted. Invalid column object (last known name: {self.name})")

	def source_check(self, checked=False):
		"""
		Raise error if the source is not verified/mismatched
		"""
		if checked:
			return True
		self.source.raise_source(self.CC)
		self.raise_deleted()

		return True

	def __getitem__(self, row: Union[int, slice]):
		"""
		row: the index of row (not id) [returns the cell value]
		"""
		return self._get(row, rescan=True, source_checked=False)

	def __setitem__(self, row: int, value):
		"""
		@ Auto dumps
		* row: row index (not id)
		* value: accepts both raw value and _PickleTCell obj
		"""

		# self.source.raise_source(self.CC)
		self.set_item(row, value, AD=True, rescan=True)

	def __len__(self) -> int:
		self.source_check()
		return self.source.height

	def __bool__(self):
		"""
		return True if the column has values
		"""
		self.source_check()
		return bool(self.source.height)

	def __str__(self):
		self.source_check()

		return "<PickleTable._PickleTColumn object> " + str(self.source._get_column(self.name))

	def __repr__(self):
		self.source_check()

		return repr(self.source._get_column(self.name))

	def __delitem__(self, row: int):
		"""
		@ Auto dump
		* row: index of row (not id)
		"""
		self.del_item(row, AD=True, rescan=True)

	def __iter__(self) -> Generator[_PyroTCell, None, None]:
		return self.get_cells_obj()

	def __contains__(self, item):
		self.source_check()
		return item in self.iter_values()

	def re__name(self, new_name, AD=True, rescan=True):
		"""
		Renames the column to a new name. (Dangerous operation; use with caution.)

		Args:
			new_name (str): The new name for the column.
			AD (bool, optional): If True, automatically dumps changes after renaming. Defaults to True.
			rescan (bool, optional): If True, rescans the source before renaming. Defaults to True.

		Warning:
			This operation will invalidate other relative objects that reference this column.
			A safer alternative is planned for future versions.

		Side Effects:
			- Updates the column name in the underlying database.
			- May break references in other objects that depend on the old column name.
			- Triggers auto-dump if AD is True.

		Raises:
			Any exceptions raised by underlying source methods.
		"""
		self.source._auto_rescan(rescan=rescan)
		self.source_check()

		self.source.add_column(new_name, exist_ok=True, AD=False, rescan=False)
		self.source._pk.db[new_name] = self.source._pk.db.pop(self.name)

		self.source.auto_dump(AD=AD)

		self.name = new_name

	def re_name(self, new_name, AD=True, rescan=True):
		"""
		Renames the current column to a new name.

		This method updates the column's name within the source, transferring its data to the new name and removing the old column entry. Note that `_PickleTColumn` instances initialized with the old name will not be updated, except for the current instance. This operation may invalidate references in other objects (such as cells referencing the previous column name), but the underlying memory space remains unchanged. Use with caution.

		Args:
			new_name (str): The new name for the column.
			AD (bool, optional): If True, automatically dumps changes to persistent storage. Defaults to True.
			rescan (bool, optional): If True, rescans the source before renaming. Defaults to True.

		Warning:
			This method may invalidate other objects that reference the old column name. A safer alternative using unique IDs for rows and columns is planned for future versions.
		"""
		self.source._auto_rescan(rescan=rescan)
		self.source_check()

		self.source.add_column(new_name, exist_ok=True, AD=False, rescan=False)
		self.source._pk.db[new_name] = self.source._pk.db[self.name]
		self.source.del_column(self.name, AD=False, rescan=False)

		self.source.auto_dump(AD=AD)

		self.name = new_name


	def _get(self, row: Union[int, slice], rescan=True, source_checked=False):
		self.source_check(source_checked)

		if isinstance(row, int):
			return self.source.get_cell(col=self.name, row=row, rescan=rescan)
		elif isinstance(row, slice):
			return [self.source.get_cell(col=self.name, row=i, rescan=rescan) for i in range(*row.indices(self.source.height))]
		else:
			raise TypeError(
				"indices must be integers or slices, not {}".format(type(row).__name__))



	def get(self, row: int, default=None, rescan=True, source_checked=False) -> Any:
		"""
		Retrieve the value from the column at the specified row index.

		Args:
			row (int): The index of the row (not id) from which to retrieve the value.
			default (Any, optional): The value to return if the row index is invalid or not an integer. Defaults to None.

		Returns:
			Any: The value at the specified row index, or the default value if the index is invalid.

		Notes:
			- The row parameter refers to the row's index, not its ID.
			- If the row index is out of bounds or not an integer, the default value is returned.
		"""
		sc = self.source_check(source_checked)
		if not isinstance(row, int):
			return default
		if row > (self.source.height-1):
			return default

		return self._get(row, rescan=rescan, source_checked=sc)

	def get_by_id(self, row_id: int, rescan=True, source_checked=False) -> Any:
		"""
		Retrieve the value of a row by its unique ID.

		Args:
			row_id (int): The unique identifier (not index) of the row to retrieve.

		Returns:
			Any: The value of the row corresponding to the given ID, or the default value if not found.

		Raises:
			Any exceptions raised by `self.source_check()`.

		Notes:
			- This method checks if the given row_id exists in the source's IDs.
			- If the row_id does not exist, it may raise a ValueError (as Item index not found).
		"""
		self.source_check(source_checked)

		# return self[self.source.ids.index(row_id)]
		return self.source.get_cell_by_id(self.name, row_id, rescan=rescan)

	def get_cell_obj(self, row: int = None, row_id: int = None, rescan=True, source_checked=False) -> Union["_PyroTCell", None]:
		"""
		Retrieve the cell object for this column at the specified row index.

		Args:
			row (int, optional): The index of the row to retrieve the cell from. Defaults to None (invalid).
			row_id (int, optional): The unique identifier of the row. Used if `row` is not provided. Defaults to None (invalid).
			default (Any, optional): The value to return if the row index is out of bounds. Defaults to None.
			rescan (bool, optional): Whether to rescan the source when retrieving the cell object. Defaults to True.

		Returns:
			Union["_PickleTCell", None]: The cell object at the specified row, or `default` if the row is out of bounds.

		Raises:
			ValueError: If neither `row` nor `row_id` is provided.
		"""

		self.source_check(source_checked)

		if row is None:
			# use row index
			if row_id is None:
				raise ValueError("row or row_id must be provided")

		return self.source.get_cell_obj(col=self.name, row=row, rescan=rescan)

	def _set_item(self, row: int, value, AD=True, rescan=True, source_checked=False):
		"""
		Sets the value of a cell in the column by row index, with options for auto-dumping and rescanning.

		Args:
			row (int): The row index of the cell to set (not the database ID).
			value: The value to set. Can be a raw value or a _PickleTCell object.
			AD (bool, optional): If True, automatically dumps changes to the database. Defaults to True.
			rescan (bool, optional): If True, rescans the database file if it has changed. Defaults to True.

		Notes:
			- This method is faster but considered unsafe.
			- If 'value' is a _PickleTCell object, its 'value' attribute is used.
			- Calls 'source_check' before setting the value.
		"""

		self.source_check(source_checked)
		# self.source.raise_source(self.CC)

		if isinstance(value, _PyroTCell):
			value = value.value

		self.source.set_cell(
			col=self.name,
			row=row,
			val=value,
			AD=AD,
			rescan=rescan
		)

	def set_item(self, row: int=None, value=None, row_id:int=None, AD=True, rescan=True, source_checked=False) -> "_PyroTCell":
		"""
		Sets the value of a cell in the column by row index or row ID.

		Parameters:
			row (int, optional): The row index to set the value at. Must provide either `row` or `row_id`, but not both.
			value: The value to set. Can be a raw value or a `_PickleTCell` object.
			row_id (int, optional): The unique row ID to set the value at. Used if `row` is not provided.
			AD (bool, default=True): If True, automatically dumps changes after setting the value.
			rescan (bool, default=True): If True, rescans the table after setting the value.

		Returns:
			_PickleTCell: The updated cell object.

		Raises:
			ValueError: If neither `row` nor `row_id` is provided, or if both are provided.
			IndexError: If the specified row index is out of bounds.
		"""
		sc = self.source_check(source_checked)
		# self.source.raise_source(self.CC)

		if row is None:
			# use row index
			if row_id is None:
				raise ValueError("row or row_id must be provided")
			row = self.source.ids.index(row_id)
		elif row_id is not None:
			raise ValueError("Only one of row or row_id must be provided")
		if row > (self.source.height-1):
			raise IndexError(
				f"Row index {row} is out of bounds for column '{self.name}' with height {self.source.height}")

		if isinstance(value, _PyroTCell):
			value = value.value

		# self.source.set_cell(col=self.name, row=row, val=value, AD=AD)
		cell = self.get_cell_obj(row, rescan=rescan, source_checked=sc)
		cell.set(value, AD=AD, rescan=False)

		return cell

	def set_all(self, value, AD=True, rescan=True, source_checked=False):
		"""
		Set all cells in the column to the value
		- value: value to set
		- AD: auto dump
		"""
		self.source._auto_rescan(rescan=rescan)
		sc = self.source_check(source_checked)

		for i in range(self.source.height):
			self.set_item(i, value, AD=False, rescan=False, source_checked=sc)

		self.source.auto_dump(AD=AD)

	def del_item(self, row: int, AD=True, rescan=True):
		"""
		@ Auto dumps


		Delete the cell value from the column by row index

		- row: row index (not id)
		- AD: auto dump
		"""
		self.source_check()
		self.source.set_cell(self.name, row, None, AD=AD, rescan=rescan)

	def iter_values(self, rescan=True) -> Generator[Any, None, None]:
		"""
		returns the values of the column
		"""
		self.source_check()
		self.source._auto_rescan(rescan=rescan)

		for i in self:
			yield i.get_value(rescan=False)

	def to_list(self, rescan=True) -> list:
		"""
		returns the column as list
		"""
		self.source_check()
		return list(self.iter_values(rescan=rescan))

	def to_dict(self, rescan=True) -> dict:
		"""
		returns the column as dict
		"""
		self.source_check()
		self.source._auto_rescan(rescan=rescan)

		d = {i: v for i, v in enumerate(self.iter_values())}
		return d

	def source_list(self):
		"""
		Returns a reference (not a copy) to the column list associated with the current source.

		Returns:
			list: A pointer to the column list for the given source name.

		Note:
			The returned list is not a copy; modifications to it will affect the original data.

		Raises:
			Exception: If the source check fails or the source is not properly initialized.
		"""
		self.source_check()
		return self.source._get_column(self.name)

	def get_cells_obj(self, start: int = 0, end: int = None, sep: int = 1, source_checked=False) -> Generator["_PyroTCell", None, None]:
		"""
		Return a list of all rows in db

		- start: start index (default: 0)
		- end: end index (default: None)
		- sep: step (default: 1)
		"""
		self.source_check(source_checked) # DO NOT CACHE as COLUMN CAN CHANGE DURING ITERATION
		if end is None:
			end = self.source.height
		if end < 0:
			end = self.source.height + end

		for i in range(start, end, sep):
			yield self.get_cell_obj(i)

	def append(self, *args, **kwargs):
		"""
		`append`, `extend`, `sort`, `reverse`, `pop`, `insert`, `remove` are not supported
		"""
		raise NotImplementedError(
			"You can't manually do append, extend, sort, reverse, pop, insert, remove on a column. Use alternate methods instead")

	extend = append
	sort = append
	reverse = append
	pop = append
	insert = append

	def update(self, column: Union[list, "_PyroTColumn"], AD=True, rescan=True):
		"""
		@ Auto dumps
		- column: list of values to update
		"""
		sc = self.source_check()

		if isinstance(column, self.__class__):
			column = column.to_list()

		self.source._auto_rescan(rescan=rescan)
		for i, v in enumerate(column):
			self._set_item(i, v, AD=False, rescan=False, source_checked=sc)

		self.source.auto_dump(AD=AD)

	def remove(self, value, n_times=1, AD=True, rescan=True):
		"""
		@ Auto dumps
		- This will remove the occurrences of the value in the column (from top to bottom)
		- n_times: number of occurrences to remove (0: all)
		"""
		self.source_check()

		self.source._auto_rescan(rescan=rescan)
		for i in self:
			if i == value:
				i.clear(AD=False, rescan=False)
				n_times -= 1
				if n_times == 0:
					break

		self.source.auto_dump(AD=AD)

	def clear(self, AD=True, rescan=True) -> None:
		"""
		@ Auto dumps
		# This will Set all cells in column to `None`
		"""
		sc = self.source_check()

		self.source._auto_rescan(rescan=rescan)

		for row in range(self.source.height):
			self._set_item(row, None, AD=False, rescan=False, source_checked=sc)

		self.source.auto_dump(AD=AD)

	def del_column(self, AD=True, rescan=True):
		"""
		@ Auto dumps
		# This will also invalidate this object. Handle with care
		"""
		self.source_check()

		self.source.del_column(self.name, AD=AD, rescan=rescan)

		self.deleted = True

	def apply(self, func=as_is, row_func=False, copy=False, AD=True, rescan=True, source_checked=False, force_rescan=False):
		"""
		Apply a function to all cells in the column, optionally overwriting existing values or returning a copy.

		Parameters:
			func (callable, optional): Function to apply to each cell value or row object. Defaults to `as_is`.
			row_func (bool, optional): If True, apply `func` to the row object instead of the cell value. Defaults to False.
			copy (bool, optional): If True, return a list of results instead of modifying the column in place. Defaults to False.
			AD (bool, optional): If True, automatically dump changes after applying the function. Defaults to True.
			rescan (bool, optional): If True, trigger a rescan after applying the function. Defaults to True.
			source_checked (bool, optional): If True, skip source check. Defaults to False.
			force_rescan (bool, optional): If True, force a rescan regardless of other flags. Defaults to False.

		Returns:
			list: List of values if `copy` is True.
			self: The column object itself if `copy` is False.

		Notes:
			- If `row_func` is True, `func` receives the row object; otherwise, it receives the cell value.
			- If `copy` is False, the column is modified in place.
			- The function triggers auto-dump and rescan behavior based on the provided flags.
		"""
		self.source_check(source_checked) # DO NOT CACHE as COLUMN CAN CHANGE DURING ITERATION

		self.source._auto_rescan(rescan=rescan or force_rescan)

		ret = []
		if row_func:
			for i in range(self.source.height):
				if copy:
					ret.append(func(self.source.row_obj(i)))
				else:
					# self[i] = func(self.source.row_obj(i))
					self._set_item(
						i,
						func(self.source.row_obj(i)),
						AD=False,
						rescan=(False or force_rescan),
					)
		else:
			for i in range(self.source.height):
				if copy:
					ret.append(func(self[i]))
				else:
					# self[i] = func(self[i])
					self._set_item(
						i,
						func(self[i]),
						AD=False,
						rescan=(False or force_rescan),
					)

		self.source.auto_dump(AD=AD)

		if not copy:
			return self

		return ret






# Backward compatibility Alias
PickleTable = PyroTable
_PickleTCell = _PyroTCell
_PickleTRow = _PyroTRow
_PickleTColumn = _PyroTColumn





# Process function
def _extreme_concurrency_process_worker(process_id, lock, TEST_FILE, THREADS_PER_PROCESS, expected_values, errors, operation_counter, OPERATIONS_PER_THREAD):
	"""Worker function for multiprocessing"""

	threads = []

	# Load initial data if file exists
	if os.path.exists(TEST_FILE):
		with lock:
			tb = PyroTable(TEST_FILE)


	# Worker function (runs in each thread)
	def worker(table:PyroTable, process_id, thread_id):
		nonlocal errors, operation_counter
		rng = random.Random(process_id * 1000 + thread_id)

		for i in range(OPERATIONS_PER_THREAD):
			if not expected_values:
				# If no expected values, we can only insert or read
				op_type = 'insert'
			else:
				# Randomly choose operation type
				# If read, ensure there are expected values to read from
				op_type = rng.choice(['insert', 'update', 'delete', 'read'])

			if op_type == 'read':
				row_id = rng.choice(list(expected_values.keys()))
			else:
				row_id = rng.randint(1, 100000)
				value = rng.randint(1, 100000)

			try:
				with lock:
					operation_counter.value += 1

				if op_type == 'insert' and row_id not in expected_values:
					with lock:
						expected_values[row_id] = value
						table.add_row({
							"id": row_id,
							"name": f"proc_{process_id}_thread_{thread_id}",
							"value": value,
							"notes": f"op_{i}"
						})

				elif op_type == 'update' and row_id in expected_values:
					with lock:
						expected_values[row_id] = value
						for row in table.search_iter(kw=row_id, column="id"):
							row.row_obj()["value"] = value

				elif op_type == 'delete' and row_id in expected_values:
					with lock:
						expected_values.pop(row_id)
						for row in table.search_iter(kw=row_id, column="id"):
							row.row_obj().del_row(AD=False, rescan=False)

				elif op_type == 'read' and row_id in expected_values:
					with lock:
						for row in table.search_iter(kw=row_id, column="id"):
							if row.row_obj()["value"] != expected_values[row_id]:
								print(f"\nValue mismatch for row {row_id}: expected {expected_values[row_id]}, got {row.row_obj()['value']}\n")

								errors.append(f"Value mismatch for row {row_id}")

				# Randomly save to disk
				if rng.random() < 0.01:  # 1% chance
					with lock:
						table.dump(TEST_FILE)

			except Exception as e:
				errors.append(f"Process {process_id} Thread {thread_id}: {str(e)}")


	# Start threads
	for thread_id in range(THREADS_PER_PROCESS):
		t = threading.Thread(
			target=worker,
			args=(tb, process_id, thread_id)
		)
		threads.append(t)
		t.start()

	# Wait for threads
	for t in threads:
		t.join()

	# Final save
	with lock:
		tb.dump(TEST_FILE)

def _extreme_concurrency_process_worker(
	process_id, lock, TEST_FILE, THREADS_PER_PROCESS,
	expected_values, errors, operation_counter, OPERATIONS_PER_THREAD, activities):
	"""Worker function for multiprocessing with fixed concurrency issues"""

	# Initialize table with lock protection
	with lock:
		tb = PyroTable(TEST_FILE)
	threads = []

	def worker(table: PyroTable, process_id, thread_id):
		nonlocal errors, operation_counter
		rng = random.Random(process_id * 1000 + thread_id + int(time.time()))

		for i in range(OPERATIONS_PER_THREAD):
			time.sleep(rng.uniform(0.01, 0.1))  # Simulate variable operation time
			try:
				# Atomic operation selection and execution
				with lock:
					pass
				operation_counter.value += 1
				available_ops = []

				# Determine possible operations based on current state
				if expected_values:
					available_ops.extend(['update', 'delete', 'read'])
				available_ops.append('insert')  # Always allow inserts

				op_type = rng.choice(available_ops)

				row_id = rng.randint(1, 10000000)
				value = rng.randint(1, 10000)

				# Execute operation with appropriate locking
				if op_type == 'insert':
					with lock:
						if row_id not in expected_values:
							expected_values[row_id] = value
							row = table.add_row({
								"id": row_id,
								"name": f"proc_{process_id}_thread_{thread_id}",
								"value": value,
								"notes": f"op_{i}"
							})
						
							activities.append({row_id: (
								"inserted", value, row.to_dict()
							)})

				elif op_type == 'update':
					with lock:
						if row_id in expected_values:
							expected_values[row_id] = value
							row = table.find_1st_row(kw=row_id, column="id", return_obj=True)

							if not row:
								errors.append(f"Row {row_id} not found for update")
								print(f"\nRow {row_id} not found for update\n")

								activities.append({row_id: (
									"update", value, None
								)})
								continue
							
							row["value"] = value

							activities.append({row_id: (
								"update", value, row.to_dict()
							)})

				elif op_type == 'delete':
					with lock:
						if row_id in expected_values:
							expected_values.pop(row_id)
							# More reliable deletion method
							row = table.find_1st_row(kw=row_id, column="id", return_obj=True)

							if not row:
								errors.append(f"Row {row_id} not found for deletion")
								print(f"\nRow {row_id} not found for deletion\n")

								activities.append({row_id: (
									"deleted", None
								)})
								continue
							
							r_dict = row.to_dict()
							row.del_row()

							activities.append({row_id: (
								"deleted", r_dict
							)})

				elif op_type == 'read':
					with lock:
						if row_id in expected_values:
							expected_value = expected_values[row_id]
							found = False
							row = table.find_1st_row(kw=row_id, column="id", return_obj=True)

							if not row:
								errors.append(f"Row {row_id} not found for read")
								print(f"\nRow {row_id} not found for read\n")

								activities.append({row_id: (
									"read", expected_value, None
								)})
								continue

							if row["value"] != expected_value:
								errors.append(f"Value mismatch for row {row_id}")
								print(f"\nValue mismatch for row {row_id}: "
										f"expected {expected_values[row_id]}, got {row['value']}\n")
							if not found:
								errors.append(f"Row {row_id} not found but expected")

							activities.append({row_id: (
								"read", expected_value, row.to_dict()
							)})

				# Random save with reduced frequency to minimize contention
				if rng.random() < 0.005:  # Reduced from 1% to 0.5%
					with lock:
						table.dump(TEST_FILE)

			except Exception as e:
				error_msg = f"Process {process_id} Thread {thread_id} Op {i}: {str(e)}"
				errors.append(error_msg)
				print(f"\n{error_msg}\n")

	# Start threads
	for thread_id in range(THREADS_PER_PROCESS):
		t = threading.Thread(
			target=worker,
			args=(tb, process_id, thread_id),
			daemon=True
		)
		threads.append(t)
		t.start()

	# Wait for threads with timeout
	for t in threads:
		t.join(timeout=120)  # 2 minute timeout per thread

	# Final save
	with lock:
		tb.dump(TEST_FILE)
		tb.to_json(f"{TEST_FILE}{process_id}_final.json")

if __name__ == "__main__":
	import string
	import os
	import time
	import random
	import string
	import io
	import json
	import threading
	import traceback
	from functools import wraps

	import multiprocessing

	# Timing Decorator
	def timed_test(test_func):
		@wraps(test_func)
		def wrapper(*args, **kwargs):
			start_time = time.perf_counter()
			print(f"\n⏱️  Starting {test_func.__name__}...")
			try:
				result = test_func(*args, **kwargs)
				elapsed = time.perf_counter() - start_time
				print(f"✅ {test_func.__name__} completed in {elapsed:.4f}s")
				return result
			except Exception as e:
				elapsed = time.perf_counter() - start_time
				print(f"❌ {test_func.__name__} failed after {elapsed:.4f}s")
				raise
		return wrapper

	# Helper Functions (same as before)
	def generate_random_string(length):
		"""Generate random lowercase string of given length"""
		return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

	def create_test_table(with_data=False):
		"""Create a basic test table with common columns"""
		tb = PyroTable()
		tb.add_column("id", exist_ok=True)
		tb.add_column("name", exist_ok=True)
		tb.add_column("value", exist_ok=True)
		tb.add_column("notes", exist_ok=True)

		if with_data:
			# Add some initial data
			tb.add_rows([
				{"id": 1, "name": "alpha", "value": 100, "notes": "first item"},
				{"id": 2, "name": "beta", "value": 200, "notes": "second item"},
				{"id": 3, "name": "gamma", "value": 300, "notes": "third item"}
			])
		return tb



	def assert_with_message(condition, message, *extra, message_on_fail=None, message_on_success=None, time_start=None):
		"""Helper for better assertion messages"""
		if time_start is not None:
			time_end = time.perf_counter()
			message = f"{message} (Time taken: {time_end - time_start:.4f}s)"

		if message_on_fail is None or message_on_fail is True:
			message_on_fail = message
		elif message_on_fail is False:
			message_on_fail = ""
		else:
			message_on_fail = f"{message_on_fail} ({message})"

		if message_on_success is None or message_on_success is True:
			message_on_success = message
		elif message_on_success is False:
			message_on_success = ""
		else:
			message_on_success = f"{message_on_success} ({message})"

		if not condition:
			if extra:
				if len(extra) == 1:
					message_on_fail = f"{message_on_fail} ({extra[0]})"
				elif len(extra) == 2:
					message_on_fail = f"{message_on_fail}\n(\n\tExpected: \n{extra[0]}\n\tGot: \n{extra[1]}\n)"
			if message_on_fail:
				raise AssertionError(f"❌ {message_on_fail}")
			else:
				raise AssertionError()

		if message_on_success:
			print(f"✅ {message_on_success}")

	# Test Cases with timing
	@timed_test
	def test_basic_operations():
		"""Test basic table operations with thorough checks"""
		print("\n=== Testing Basic Operations ===")
		tb = create_test_table()

		# Time individual operations
		ts = time.perf_counter()
		row = tb.add_row(
			{"id": 1, "name": "test", "value": 100, "notes": None})
		assert_with_message(
			tb.height == 1, "Row count after add", tb.height, 1, time_start=ts)

		ts = time.perf_counter()
		assert_with_message(
			row.index() == 0, "Row index correct", row.index(), 0, time_start=ts)

		ts = time.perf_counter()
		assert_with_message(tb.row(0)["name"] == "test", "Row data integrity", tb.row(0)[
							"name"], "test", time_start=ts)

		ts = time.perf_counter()
		ids = tb.column("id")
		assert_with_message(
			ids == [1], "Column data retrieval", ids, [1], time_start=ts)

		ts = time.perf_counter()
		tb.row_obj(0)["value"] = 150
		assert_with_message(tb.row(0)["value"] == 150, "Row modification", tb.row(0)[
							"value"], 150, time_start=ts)

		ts = time.perf_counter()
		tb["name"].set_all("updated")
		assert_with_message(tb.row(0)["name"] == "updated", "Column modification", tb.row(
			0)["name"], "updated", time_start=ts)

		ts = time.perf_counter()
		tb.row_obj(0).del_row()
		assert_with_message(tb.height == 0, "Row deletion",
							tb.height, 0, time_start=ts)

		def __index_error(fn):
			"""Test for IndexError on accessing deleted row"""
			ts = time.perf_counter()
			try:
				fn(0)
			except IndexError:
				print(
					f"✅ Row access after deletion (IndexError) (Time: {time.perf_counter() - ts:.4f}s)")
			else:
				print(
					f"❌ Row access after deletion (No IndexError) (Time: {time.perf_counter() - ts:.4f}s)")
				raise AssertionError("Row access after deletion")

		__index_error(tb.row)
		__index_error(tb.row_obj)

		def __key_error(fn):
			"""Test for KeyError on accessing non-existent column"""
			ts = time.perf_counter()
			x = None
			try:
				x = fn("non_existent")
			except KeyError:
				print(
					f"✅ Non-existent column access (KeyError) (Time: {time.perf_counter() - ts:.4f}s)")
			else:
				print(
					f"❌ Non-existent column access (No KeyError), got: {[x]} (Time: {time.perf_counter() - ts:.4f}s)")
				raise AssertionError("Non-existent column access")
		__key_error(tb.column)
		__key_error(tb.column_obj)

	@timed_test
	def test_persistence():
		"""Test saving and loading table with comprehensive checks"""
		print("\n=== Testing Persistence ===")
		test_file = "__persistence_test.pdb"
		tb = create_test_table(with_data=True)

		try:
			# Time file operations
			ts = time.perf_counter()
			tb.dump(test_file)
			assert_with_message(os.path.exists(test_file),
								"File creation", time_start=ts)

			ts = time.perf_counter()
			loaded_tb = PyroTable(test_file)
			assert_with_message(loaded_tb.height == 3,
								"Row count after load", time_start=ts)

			ts = time.perf_counter()
			assert_with_message(loaded_tb.column_names == ("id", "name", "value", "notes"),
								f'Column preservation (expected: {("id", "name", "value", "notes")}, got: {loaded_tb.column_names})',
								time_start=ts)

			ts = time.perf_counter()
			assert_with_message(loaded_tb.row(
				2)["name"] == "gamma", "Data integrity", time_start=ts)

			ts = time.perf_counter()
			loaded_tb.add_row(
				{"id": 4, "name": "delta", "value": 400, "notes": "new item"})
			loaded_tb.dump(test_file)
			assert_with_message(os.path.getsize(test_file) >
								0, "File size after modification", time_start=ts)

			ts = time.perf_counter()
			reloaded_tb = PyroTable(test_file)
			assert_with_message(reloaded_tb.height == 4,
								"Incremental save", time_start=ts)

		finally:
			if os.path.exists(test_file):
				os.remove(test_file)

	@timed_test
	def test_search_operations():
		"""Test search functionality with thorough validation"""
		print("\n=== Testing Search Operations ===")
		tb = create_test_table()
		ITEM_COUNT = 100000

		# Time data generation
		ts = time.perf_counter()
		for i in range(ITEM_COUNT):
			tb.add_row({
				"id": i,
				"name": f"item_{i%10}",
				"value": i*10,
				"notes": f"note_{i}" if i % 3 == 0 else None
			},
			# rescan=False,
			AD=False
			)
		print(
			f"⏱️  Data generation [1 row at a time] completed in {time.perf_counter() - ts:.4f}s")

		ts = time.perf_counter()
		rows = []
		for i in range(ITEM_COUNT, ITEM_COUNT * 2):
			rows.append(
				{"id": i, "name": f"item_{i%10}", "value": i*10, "notes": f"note_{i}" if i % 3 == 0 else None}
			)

		tb.add_rows(rows, AD=False)
		print(f"⏱️  Data generation [bulk add] completed in {time.perf_counter() - ts:.4f}s")

		ITEM_COUNT = ITEM_COUNT * 2  # Adjust for bulk add

		# Time searches
		ts = time.perf_counter()
		results = list(tb.search_iter(kw="item_1", column="name"))
		assert_with_message(len(results) == ITEM_COUNT//10,
							"Basic search count", time_start=ts)

		ts = time.perf_counter()
		first_20 = tb.find_1st(20, column="id")
		assert_with_message(first_20.value == 20,
							"Find first value", time_start=ts)

		ts = time.perf_counter()
		assert_with_message(first_20.row_obj()[
							"value"] == 200, "Find first row data", time_start=ts)

		ts = time.perf_counter()
		null_notes = list(tb.search_iter(kw=None, column="notes"))
		expected_nulls = [i for i in range(ITEM_COUNT) if i % 3 != 0]
		assert_with_message(
			len(null_notes) == len(expected_nulls),
			f"Null value search",
			len(expected_nulls), len(null_notes),
			time_start=ts
		)

		ts = time.perf_counter()

		def custom_key(row):
			return row["name"].split("_")[1] == "1" and row["notes"] is not None
		custom_results = list(tb.search_iter_row(
			kw=custom_key, is_function=True))
		assert_with_message(
			len(custom_results) == ITEM_COUNT//30,
			f"Custom key search count",
			ITEM_COUNT//30, len(custom_results),
			time_start=ts
		)

	@timed_test
	def test_bulk_operations():
		"""Test bulk data operations with comprehensive checks"""
		print("\n=== Testing Bulk Operations ===")
		tb = create_test_table()

		# Time bulk add
		rows_to_add = [
			{"id": i, "name": f"bulk_{i}", "value": i*5,
				"notes": f"note_{i}" if i % 2 == 0 else None}
			for i in range(1000)
		]

		ts = time.perf_counter()
		added_rows = tb.add_rows(rows_to_add)
		assert_with_message(
			tb.height == 1000, "Bulk add row count", tb.height, 1000, time_start=ts)

		ts = time.perf_counter()
		assert_with_message(len(added_rows) == 1000,
							"Returned rows count", time_start=ts)

		ts = time.perf_counter()
		assert_with_message(
			tb.row(999)["name"] == "bulk_999", "Last row integrity", time_start=ts)

		# Time column operations
		ts = time.perf_counter()
		tb["value"].apply(lambda x: x*2)
		sample_values = [tb.row(i)["value"] for i in [0, 500, 999]]
		expected_values = [0, 5000, 9990]
		assert_with_message(
			sample_values == expected_values,
			"Column apply operation",
			time_start=ts
		)

		ts = time.perf_counter()
		tb["name"].apply(lambda x: x.upper())
		assert_with_message(
			tb.row(100)["name"] == "BULK_100",
			"Bulk modification",
			time_start=ts
		)

	@timed_test
	def test_sorting():
		"""Test sorting functionality with thorough validation"""
		print("\n=== Testing Sorting ===")
		tb = create_test_table(with_data=True)

		# Initial data setup
		ts = time.perf_counter()
		tb.add_rows([
			{"id": 5, "name": "alpha", "value": 50, "notes": "duplicate name"},
			{"id": 4, "name": "delta", "value": 400, "notes": "out of order"},
			{'id': 0, 'name': 'alpha', 'value': 50, 'notes': 'zeroth item'},
			{'id': 4, 'name': 'delta', 'value': 400, 'notes': 'fourth item'},
			{'id': 5, 'name': 'alpha', 'value': 500, 'notes': 'duplicate name'},
			{'id': 6, 'name': None, 'value': None, 'notes': None}
		])
		print(f"⏱️  Data setup completed in {time.perf_counter() - ts:.4f}s")

		# Test basic numeric sort
		ts = time.perf_counter()
		tb.sort("id")
		assert_with_message(tb.column("id") == [0, 1, 2, 3, 4, 4, 5, 5, 6],
						"Numeric sort", time_start=ts)

		# Test data integrity after sort
		ts = time.perf_counter()
		assert_with_message(
			tb.row(1)["notes"] == "first item", "Data integrity after sort", time_start=ts)

		# Test custom sort key
		ts = time.perf_counter()
		tb.sort(key=lambda x: len(x["notes"] or ""), reverse=True)
		assert_with_message(
			tb.row(0)["notes"] == "duplicate name", "Custom sort key", time_start=ts)

		# Test sort with copy
		og_column = tb.column("value")
		ts = time.perf_counter()
		new_tb = tb.sort("value", copy=True)
		assert_with_message(
			new_tb.column("value") == [None, 50, 50, 100, 200, 300, 400, 400, 500],
			"Sort copy",
			[None, 50, 50, 100, 200, 300, 400, 400, 500], new_tb.column("value"),
			time_start=ts)

		# Test copy preservation
		ts = time.perf_counter()
		assert_with_message(tb.height == new_tb.height,
						"Copy row count preservation", time_start=ts)

		ts = time.perf_counter()
		assert_with_message(
			tb.column("value") == og_column,
			"Original table unchanged after sort copy",
			tb.column("value"), og_column,
			time_start=ts
		)

		# Test multi-column sort
		ts = time.perf_counter()
		tb.sort(['name', 'value'])
		expected_order = [(None, None), ('alpha', 50), ('alpha', 50), ('alpha', 100), ('alpha', 500),
						('beta', 200), ('delta', 400), ('delta', 400), ('gamma', 300)]
		results = [(r['name'], r['value']) for r in tb.rows()]
		assert_with_message(results == expected_order,
						f'Multi-column sort (name, value)',
						time_start=ts)

		# Test reverse sort
		ts = time.perf_counter()
		tb.sort('value', reverse=True)
		assert_with_message(tb.row(0)['value'] == 500 and tb.row(-1)['value'] is None,
						'Reverse sort', time_start=ts)

		# Test sort with None values
		ts = time.perf_counter()
		tb.sort('value')
		assert_with_message(
			tb.row(0)['value'] is None, 'Sort with None values', time_start=ts)

	@timed_test
	def test_import_export():
		"""Test CSV/JSON import/export with comprehensive validation"""
		print("\n=== Testing Import/Export ===")
		tb = create_test_table(with_data=True)

		# CSV Tests
		csv_file = "__test_csv.csv"
		try:
			ts = time.perf_counter()
			tb.add_row({"id": 4, "name": "Special,Value",
					   "value": 400, "notes": "With,comma"})
			print(
				f"⏱️  Data modification completed in {time.perf_counter() - ts:.4f}s")

			ts = time.perf_counter()
			tb.to_csv(csv_file)
			print(
				f"⏱️  CSV export completed in {time.perf_counter() - ts:.4f}s")

			ts = time.perf_counter()
			with open(csv_file, "r") as f:
				content = f.read()
			assert_with_message('"Special,Value"' in content,
								"CSV special character handling", time_start=ts)

			ts = time.perf_counter()
			new_tb = PyroTable()
			new_tb.load_csv(csv_file)
			assert_with_message(new_tb.height == 4,
								"CSV import row count", time_start=ts)

			ts = time.perf_counter()
			assert_with_message(new_tb.row(
				3)["name"] == "Special,Value", "CSV data integrity", time_start=ts)

		finally:
			if os.path.exists(csv_file):
				os.remove(csv_file)

		# JSON Tests
		json_file = "__test_json.json"
		try:
			ts = time.perf_counter()
			tb.to_json(json_file, format="dict")
			print(
				f"⏱️  JSON export completed in {time.perf_counter() - ts:.4f}s")

			ts = time.perf_counter()
			with open(json_file) as f:
				data = json.load(f)
			assert_with_message(isinstance(data, dict),
								"JSON dict format", time_start=ts)

			ts = time.perf_counter()
			assert_with_message(len(data["id"]) ==
								4, "JSON data count", time_start=ts)

			ts = time.perf_counter()
			new_tb = PyroTable()
			new_tb.load_json(json_file)
			assert_with_message(new_tb.row(
				2)["value"] == 300, "JSON data integrity", time_start=ts)

		finally:
			if os.path.exists(json_file):
				os.remove(json_file)



	@timed_test
	def test_concurrency():
		"""Test concurrent operations with thorough validation"""
		print("\n=== Testing Concurrency ===")
		test_file = "__concurrency_test.pdb"
		tb = create_test_table()
		lock = threading.Lock()
		errors = []
		expected_values = {}

		def worker(table, thread_id, num_rows=100):
			nonlocal errors
			try:
				for i in range(num_rows):
					row_id = i + (thread_id * 1000)
					value = random.randint(1, 10000)

					with lock:
						expected_values[row_id] = value
						table.add_row({
							"id": row_id,
							"name": f"thread_{thread_id}",
							"value": value,
							"notes": f"iteration_{i}"
						})

				with lock:
					table.dump(test_file)
			except Exception as e:
				errors.append(str(e))

		# Time thread operations
		ts = time.perf_counter()
		threads = []
		for i in range(5):
			t = threading.Thread(target=worker, args=(tb, i))
			threads.append(t)
			t.start()

		for t in threads:
			t.join()
		print(
			f"⏱️  Thread operations completed in {time.perf_counter() - ts:.4f}s")

		ts = time.perf_counter()
		assert_with_message(
			len(errors) == 0, f"No thread errors (found {len(errors)})", time_start=ts)

		ts = time.perf_counter()
		assert_with_message(
			tb.height == 500, "Total row count after concurrency", time_start=ts)

		# Time data validation
		ts = time.perf_counter()
		validation_errors = []
		for row_id, expected_value in expected_values.items():
			try:
				found = False
				for row in tb.search_iter(kw=row_id, column="id"):
					if row.value == row_id:
						if row.row_obj()["value"] != expected_value:
							validation_errors.append(
								f"Value mismatch for row {row_id}")
						found = True
						break
				if not found:
					validation_errors.append(f"Row {row_id} not found")
			except Exception as e:
				validation_errors.append(str(e))

		assert_with_message(
			len(validation_errors) == 0,
			f"Data validation (found {len(validation_errors)} errors)",
			time_start=ts
		)

		if os.path.exists(test_file):
			os.remove(test_file)

	@timed_test
	def test_extreme_concurrency():
		"""Brutal concurrency stress test with mixed operations"""
		print("\n=== Testing Extreme Concurrency ===")

		# Configuration
		NUM_PROCESSES = 4
		THREADS_PER_PROCESS = 32
		OPERATIONS_PER_THREAD = 100
		TEST_FILE = "__extreme_concurrency_test.pdb"

		# Shared state
		manager = multiprocessing.Manager()
		expected_values = manager.dict()
		activities = manager.list()  # For activity tracking
		errors = manager.list()
		operation_counter = manager.Value('i', 0)
		lock = manager.Lock()

		# Run the test
		ts_total = time.perf_counter()

		tb = create_test_table()
		tb.dump(TEST_FILE)  # Ensure the file exists for initial load

		# Create processes
		processes = []
		for i in range(NUM_PROCESSES):
			p = multiprocessing.Process(
				target=_extreme_concurrency_process_worker,
				args=(i, lock, TEST_FILE, THREADS_PER_PROCESS, expected_values, errors, operation_counter, OPERATIONS_PER_THREAD, activities)
			)
			processes.append(p)
			p.start()

		# Monitor progress
		def progress_monitor():
			while any(p.is_alive() for p in processes):
				with lock:
					ops = operation_counter.value
					errs = len(errors)
				print(f"\rOperations: {ops:,} | Errors: {errs}", end="")
				time.sleep(0.1)
			print()

		monitor_thread = threading.Thread(target=progress_monitor)
		monitor_thread.start()

		# Wait for processes
		for p in processes:
			p.join()
		monitor_thread.join()

		total_time = time.perf_counter() - ts_total
		print(f"⏱️  Total test time: {total_time:.2f}s")
		print(f"⚡ Operations/sec: {operation_counter.value/total_time:,.0f}")

		# Final validation
		ts = time.perf_counter()
		final_table = create_test_table()
		if os.path.exists(TEST_FILE):
			final_table = PyroTable(TEST_FILE)
			final_table.to_json("__extreme_concurrency_final.json")
			os.remove(TEST_FILE)

		# Check expected vs actual
		validation_errors = []
		actual_values = {row["id"]: row["value"] for row in final_table.rows()}

		expected_values = dict(expected_values)  # Convert to regular dict for easier comparison

		with open("__extreme_concurrency_activities.json", "w") as f:
			json.dump(list(activities), f, indent=4)
		# Check all expected values exist

		with open("actual_values.json", "w") as f:
			json.dump(actual_values, f, indent=4)
		with open("expected_values.json", "w") as f:
			json.dump(dict(expected_values), f, indent=4)
		for row_id, expected_value in expected_values.items():
			if row_id not in actual_values:
				validation_errors.append(f"Row {row_id} missing in final table")
			elif actual_values[row_id] != expected_value:
				validation_errors.append(
					f"Value mismatch for row {row_id}: "
					f"expected {expected_value}, got {actual_values[row_id]}"
				)

		# Check for orphaned rows
		for row_id in actual_values:
			if row_id not in expected_values:
				validation_errors.append(f"Orphaned row {row_id} in final table")

		assert_with_message(
			len(errors) == 0,
			f"No thread/process errors (found {len(errors)})",
			"\n".join(errors),
			time_start=ts
		)

		assert_with_message(
			len(validation_errors) == 0,
			f"Data validation (found {len(validation_errors)} errors)",
			"\n".join(validation_errors[:10]),  # Show first 10 errors if any
			time_start=ts
		)

	@timed_test
	def test_column_operations():
		print('\n=== Testing Column Operations ===')
		tb = create_test_table(with_data=True)
		ts = time.perf_counter()

		# Test column renaming
		tb['name'].re_name('new_name')
		assert_with_message('new_name' in tb.column_names, 'Column renaming',
							tb.column_names, time_start=ts)

		# Test column deletion
		ts = time.perf_counter()
		tb.del_column('notes')
		assert_with_message('notes' not in tb.column_names, 'Column deletion',
							tb.column_names, time_start=ts)

		# Test adding multiple columns
		ts = time.perf_counter()
		tb.add_column(['col1', 'col2', 'col3'])
		assert_with_message(all(c in tb.column_names for c in ['col1', 'col2', 'col3']),
							'Multiple column addition', time_start=ts)

		# Test duplicate column addition
		ts = time.perf_counter()
		failure_message = ''
		_success = False
		try:
			tb.add_column('col1')
			failure_message = 'Duplicate column addition should raise KeyError'
		except KeyError:
			_success = True
		except Exception as e:
			failure_message = f'Unexpected error during duplicate column addition: {e}'
			raise e
		finally:
			assert_with_message(_success, 'Duplicate column addition raises KeyError',
								time_start=ts, message_on_fail=failure_message)

		# Test column operations on empty table
		ts = time.perf_counter()
		empty_tb = create_test_table()
		empty_tb.add_column('test_col')
		assert_with_message(empty_tb.height == 0 and 'test_col' in empty_tb.column_names,
							'Column addition to empty table', time_start=ts)

	@timed_test
	def test_row_operations():
		print('\n=== Testing Row Operations ===')
		tb = create_test_table(with_data=True)
		ts = time.perf_counter()

		# Test row insertion at position
		new_row = tb.insert_row(
			{'id': 1.5, 'name': 'inserted', 'value': 150, 'notes': 'inserted'}, position=1)
		assert_with_message(tb.row(1)['name'] == 'inserted' and tb.height == 4,
							'Row insertion at position', time_start=ts)

		# Test row deletion by ID
		ts = time.perf_counter()
		row_id = new_row.id
		tb.del_row_id(row_id)
		assert_with_message(tb.height == 3 and row_id not in tb.ids,
							'Row deletion by ID', time_start=ts)

		# Test row clearing
		ts = time.perf_counter()
		tb.clear()
		assert_with_message(tb.height == 0, 'Table clearing', time_start=ts)

		# Test blank sheet
		ts = time.perf_counter()
		tb = create_test_table(with_data=True)
		tb.blank_sheet()
		assert_with_message(tb.height == 0 and len(tb.column_names) == 0,
							'Blank sheet creation', time_start=ts)

	@timed_test
	def test_cell_operations():
		print('\n=== Testing Cell Operations ===')
		tb = create_test_table(with_data=True)
		ts = time.perf_counter()

		# Test cell access
		cell = tb.get_cell_obj('name', 1)
		assert_with_message(cell.value == 'beta',
							'Cell value access', time_start=ts)

		# Test cell modification
		ts = time.perf_counter()
		cell.set('modified')
		assert_with_message(
			tb.row(1)['name'] == 'modified', 'Cell modification', time_start=ts)

		# Test cell clearing
		ts = time.perf_counter()
		cell.clear()
		assert_with_message(
			tb.row(1)['name'] is None, 'Cell clearing', time_start=ts)

		# Test cell comparison
		ts = time.perf_counter()
		cell1 = tb.get_cell_obj('id', 0)
		cell2 = tb.get_cell_obj('id', 1)
		assert_with_message(cell1 < cell2, 'Cell comparison', time_start=ts)

		# Test cell deletion
		ts = time.perf_counter()
		cell.clear()
		assert_with_message(
			tb.row(1)['name'] is None, 'Cell deletion', time_start=ts)

		# Test Batch Cell Update
		ts = time.perf_counter()
		to_update = [
			('notes', 0, 'updated first item'),
			('notes', 1, 'updated second item'),
			('notes', 2, 'updated third item')
		]

		tb.batch_set_cells(to_update, AD=False, rescan=False)
		assert_with_message(
			tb.row(0)['notes'] == 'updated first item' and
			tb.row(1)['notes'] == 'updated second item' and
			tb.row(2)['notes'] == 'updated third item',
			'Batch cell update', time_start=ts)



	@timed_test
	def test_table_operations():
		print('\n=== Testing Table Operations ===')
		tb1 = create_test_table(with_data=True)
		tb2 = create_test_table()
		ts = time.perf_counter()

		# Test table extension
		tb2.add_column(['id', 'name', 'value', 'notes'], exist_ok=True)
		tb2.add_row({'id': 4, 'name': 'delta',
					'value': 400, 'notes': 'fourth item'})
		tb1.extend(tb2)
		assert_with_message(tb1.height == 4 and tb1.row(3)['name'] == 'delta',
							'Table extension', time_start=ts)

		# Test table copying
		ts = time.perf_counter()
		tb_copy = tb1.copy()
		assert_with_message(tb_copy.height == tb1.height and
							tb_copy.column_names == tb1.column_names and
							tb_copy is not tb1, 'Table copying', time_start=ts)

		# Test table addition
		ts = time.perf_counter()
		tb3 = create_test_table()
		tb3.add(tb1)
		assert_with_message(tb3.height == tb1.height and
							tb3.column_names == tb1.column_names,
							'Table addition', time_start=ts)

	@timed_test
	def test_edge_cases():
		print('\n=== Testing Edge Cases ===')
		ts = time.perf_counter()

		# Test empty table operations
		empty_tb = create_test_table()
		assert_with_message(len(empty_tb) == 0 and not empty_tb,
							'Empty table properties', time_start=ts)

		# Test invalid column access
		ts = time.perf_counter()
		try:
			empty_tb.column('nonexistent')
			print("❌ Invalid column access (No KeyError)")
			raise AssertionError('Invalid column access')
		except KeyError:
			print(
				f"✅ Invalid column access (KeyError) (Time: {time.perf_counter()-ts:.4f}s)")

		# Test invalid row access
		ts = time.perf_counter()
		try:
			empty_tb.row(0)
			print("❌ Invalid row access (No IndexError)")
			raise AssertionError('Invalid row access')
		except IndexError:
			print(
				f"✅ Invalid row access (IndexError) (Time: {time.perf_counter()-ts:.4f}s)")

		# Test deleted object access
		ts = time.perf_counter()
		tb = create_test_table(with_data=True)
		row = tb.row_obj(0)
		tb.del_row(0)
		try:
			row['name']
			print("❌ Deleted row access (No DeletedObjectError)")
			raise AssertionError('Deleted row access')
		except DeletedObjectError:
			print(
				f"✅ Deleted row access (DeletedObjectError) (Time: {time.perf_counter()-ts:.4f}s)")

	@timed_test
	def test_advanced_search():
		print('\n=== Testing Advanced Search ===')
		tb = create_test_table(with_data=True)
		ts = time.perf_counter()

		# Add more varied data
		tb.add_rows([
			{'id': 4, 'name': 'delta', 'value': 400, 'notes': None},
			{'id': 5, 'name': 'epsilon', 'value': 500, 'notes': 'fifth item'},
			{'id': 6, 'name': 'zeta', 'value': 600, 'notes': 'sixth item'}
		])

		# Test regex search
		ts = time.perf_counter()
		results = list(tb.search_iter(
			kw='^[a-z]{4}$', column='name', regex=True))
		assert_with_message(len(results) == 2 and all(r.value in ['beta', 'zeta'] for r in results),
							'Regex search', time_start=ts)

		# Test case insensitive search
		ts = time.perf_counter()
		results = list(tb.search_iter(
			kw='GAMMA', column='name', case_sensitive=False))
		assert_with_message(len(results) == 1 and results[0].value == 'gamma',
							'Case insensitive search', time_start=ts)

		# Test full match search
		ts = time.perf_counter()
		results = list(tb.search_iter(
			kw='gamma', column='name', full_match=True))
		assert_with_message(len(results) == 1 and results[0].value == 'gamma',
							'Full match search', time_start=ts)

		# Test function search
		ts = time.perf_counter()

		def search_func(value):
			return isinstance(value, int) and value > 300 and value < 600
		results = list(tb.search_iter(
			kw=search_func, column='value', is_function=True))
		assert_with_message(len(results) == 2 and all(r.value in [400, 500] for r in results),
							'Function search', time_start=ts)

	@timed_test
	def run_all_tests():
		"""Run all test cases with timing and proper cleanup"""
		tests = [
			test_basic_operations,
			test_persistence,
			test_search_operations,
			test_bulk_operations,
			test_sorting,
			test_import_export,
			test_concurrency,
			test_column_operations,
			test_row_operations,
			test_cell_operations,
			test_table_operations,
			test_edge_cases,
			test_advanced_search,
			test_extreme_concurrency
		]


		start_time = time.perf_counter()
		failures = 0

		for test in tests:
			try:
				test()
			except AssertionError as e:
				failures += 1
				print(f"❌ {test.__name__} failed: {str(e)}")
				print('+'*50 + f"\n{traceback.format_exc()}\n" + '-'*50)
			except Exception as e:
				failures += 1
				print(f"❌ {test.__name__} failed (UNHANDLED): {str(e)}")
				print('+'*50 + f"\n{traceback.format_exc()}\n" + '-'*50)

		total_time = time.perf_counter() - start_time
		print(f"\n{'='*50}")
		print(f"⏱️  Test Summary: {len(tests)} tests, {failures} failures")
		print(f"⏱️  Total execution time: {total_time:.4f} seconds")
		print("="*50)

		
		# remove any existing test files
		test_files = ["__persistence_test.pdb", "__concurrency_test.pdb", "__extreme_concurrency_test.pdb"] + ["__extreme_concurrency_final.json", "__extreme_concurrency_activities.json, actual_values.json", "expected_values.json"]

		for file in test_files:
			if os.path.exists(file):
				os.remove(file)


		if failures > 0:
			raise SystemExit(1)

	run_all_tests()

