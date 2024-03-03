#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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


import sys
import os
import signal
import shutil
import json
import time
from random import random
from tempfile import NamedTemporaryFile
from threading import Thread


def load(location, auto_dump, sig=True):
	'''Return a pickledb object. location is the path to the json file.'''
	return PickleDB(location, auto_dump, sig)

class PickleDB(object):

	key_string_error = TypeError('Key/name must be a string!')

	def __init__(self, location, auto_dump=True, sig=True):
		'''Creates a database object and loads the data from the location path.
		If the file does not exist it will be created on the first update.
		'''
		self.CC = 0 # consider it as country code and every items are its people. they gets NID
		self.load(location, auto_dump)
		self.dthread = None
		if sig:
			self.set_sigterm_handler()

	def __getitem__(self, item):
		'''Syntax sugar for get()'''
		return self.get(item, raiseErr=True)

	def __setitem__(self, key, value):
		'''Sytax sugar for set()'''
		return self.set(key, value)

	def __delitem__(self, key):
		'''Sytax sugar for rem()'''
		return self.rem(key)


	def __len__(self):
		'''Get a total number of keys, lists, and dicts inside the db'''
		return len(self.db)


	def set_sigterm_handler(self):
		'''Assigns sigterm_handler for graceful shutdown during dump()'''
		def sigterm_handler(*args, **kwargs):
			if self.dthread is not None:
				self.dthread.join()
			sys.exit(0)
		signal.signal(signal.SIGTERM, sigterm_handler)

	def new(self):
		self.CC = hash(time.time() + random() + time.thread_time())
		self.db = {}

	def load(self, location, auto_dump):
		'''Loads, reloads or changes the path to the db file'''
		location = os.path.expanduser(location)
		self.loco = location
		self.auto_dump = auto_dump
		if os.path.exists(location):
			self._loaddb()
		else:
			self.new()
		return True

	def _dump(self):
		'''Dump to a temporary file, and then move to the actual location'''
		with NamedTemporaryFile(mode='wt', delete=False) as f:
			json.dump({
					"CC": self.CC,
					"db": self.db
				}, f, indent=None, separators=(',', ':'))
		if os.stat(f.name).st_size != 0:
			shutil.move(f.name, self.loco)

	def dump(self):
		'''Force dump memory db to file'''
		self.dthread = Thread(target=self._dump)
		self.dthread.start()
		self.dthread.join()
		return True

	# save = PROXY OF SELF.DUMP()
	save = dump

	def _loaddb(self):
		'''Load or reload the json info from the file'''
		try:
			db = json.load(open(self.loco, 'rt'))
			self.CC = db["CC"]
			self.db = db["db"]
		except ValueError:
			if os.stat(self.loco).st_size == 0:  # Error raised because file is empty
				self.new()
			else:
				raise  # File is not empty, avoid overwriting it

	def _autodumpdb(self):
		'''Write/save the json dump into the file if auto_dump is enabled'''
		if self.auto_dump:
			self.dump()


	def validate_key(self, key):
		"""Make sure key is a string"""

		if not isinstance(key, str):
			raise self.key_string_error

	def set(self, key, value):
		'''Set the str value of a key'''
		self.validate_key(key)

		self.db[key] = value
		self._autodumpdb()
		return True


	def get(self, *keys, default=None, raiseErr=False):
		'''Get the value of a key or keys
		keys work as multidimensional

		keys: dimensional key sequence. if object is dict, key must be string (to fix JSON bug)

		default: act as the default, same as dict.get
		raiseErr: raise Error if key is not found, same as dict[unknown_key]'''
		key = keys[0]
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
		'''Return a list of all keys in db'''
		return self.db.keys()

	def items(self):
		"""same as dict.items()"""
		for i,j in self.db.items():
			yield i,j

	def exists(self, key):
		'''Return True if key exists in db, return False if not'''
		return key in self.db

	def rem(self, key):
		'''Delete a key'''
		if not key in self.db: # return False instead of an exception
			return False
		del self.db[key]
		self._autodumpdb()
		return True

	def append(self, key, more):
		'''Add more to a key's value'''
		tmp = self.db[key]
		self.db[key] = tmp + more
		self._autodumpdb()
		return True

	def lcreate(self, name):
		'''Create a list, name must be str'''
		if isinstance(name, str):
			self.db[name] = []
			self._autodumpdb()
			return True
		else:
			raise self.key_string_error

	def ladd(self, name, value):
		'''Add a value to a list'''
		self.db[name].append(value)
		self._autodumpdb()
		return True

	def lextend(self, name, seq):
		'''Extend a list with a sequence'''
		self.db[name].extend(seq)
		self._autodumpdb()
		return True

	def lgetall(self, name):
		'''Return all values in a list'''
		return self.db[name]

	def lget(self, name, pos):
		'''Return one value in a list'''
		return self.db[name][pos]

	def lrange(self, name, start=None, end=None):
		'''Return range of values in a list '''
		return self.db[name][start:end]

	def lremlist(self, name):
		'''Remove a list and all of its values'''
		number = len(self.db[name])
		del self.db[name]
		self._autodumpdb()
		return number

	def lremvalue(self, name, value):
		'''Remove a value from a certain list'''
		self.db[name].remove(value)
		self._autodumpdb()
		return True

	def lpop(self, name, pos):
		'''Remove one value in a list'''
		value = self.db[name][pos]
		del self.db[name][pos]
		self._autodumpdb()
		return value

	def llen(self, name):
		'''Returns the length of the list'''
		return len(self.db[name])

	def lappend(self, name, pos, more):
		'''Add more to a value in a list'''
		tmp = self.db[name][pos]
		self.db[name][pos] = tmp + more
		self._autodumpdb()
		return True

	def lexists(self, name, value):
		'''Determine if a value  exists in a list'''
		return value in self.db[name]

	def dcreate(self, name):
		'''Create a dict, name must be str'''
		if isinstance(name, str):
			self.db[name] = {}
			self._autodumpdb()
			return True
		else:
			raise self.key_string_error

	def dadd(self, name, pair):
		'''Add a key-value pair to a dict, "pair" is a tuple'''
		self.db[name][pair[0]] = pair[1]
		self._autodumpdb()
		return True

	def dget(self, name, key):
		'''Return the value for a key in a dict'''
		return self.db[name][key]

	def dgetall(self, name):
		'''Return all key-value pairs from a dict'''
		return self.db[name]

	def drem(self, name):
		'''Remove a dict and all of its pairs'''
		del self.db[name]
		self._autodumpdb()
		return True

	def dpop(self, name, key):
		'''Remove one key-value pair in a dict'''
		value = self.db[name][key]
		del self.db[name][key]
		self._autodumpdb()
		return value

	def dkeys(self, name):
		'''Return all the keys for a dict'''
		return self.db[name].keys()

	def dvals(self, name):
		'''Return all the values for a dict'''
		return self.db[name].values()

	def dexists(self, name, key):
		'''Determine if a key exists or not in a dict'''
		return key in self.db[name]

	def dmerge(self, name1, name2):
		'''Merge two dicts together into name1'''
		first = self.db[name1]
		second = self.db[name2]
		first.update(second)
		self._autodumpdb()
		return True

	def deldb(self):
		'''Delete everything from the database'''
		self.db = {}
		self._autodumpdb()
		return True



from .tabulate import tabulate


class PickleTable(object):
	def __init__(self, filename, *args, **kwargs):

		self.busy = False
		self.pk = PickleDB(filename, *args, **kwargs)

		self.height = self.get_height()


	def get_height(self):
		h = 0
		h = len(self.pk[self.column_names[0]]) if self.column_names else 0

		#print(self.pk.db)
		return h

	def __str__(self):

		header = self.column_names
		x = tabulate([self.row(i) for i in range(min(self.height, 500))], headers="keys", tablefmt="orgtbl")
		if self.height > 50:
			x += "\n..."

		return x


	def lock(self, func):
		def inner(*args, **kwargs):

			while self.busy:
				time.sleep(.001)

			self.busy = True

			func(*args, **kwargs)

			self.busy = False

		return inner

	def column(self, name):
		return self.pk.db[name]

	def columns(self):
		'''Return a list of all columns in db'''
		return self.pk.db

	@property
	def column_names(self):
		return list(self.pk.db.keys())

	def add_column(self, name, exist_ok=False):
		tsize = self.height
		if name in self.column_names:
			if exist_ok :
				tsize = self.height- len(self.pk.db[name])
			else:
				raise KeyError("Column Name already exists")
		else:
			self.pk.db[name] = []

		self.pk.db[name].extend([None] * tsize)

		self.dump()

	def _del_column(self, name):
		self.pk.db.pop(name)

	def del_colum(self, name):
		self.lock(self._del_column)(name)

		self.dump()


	def rows(self):
		'''Return a list of all rows in db'''
		headers = self.column_names
		for i in range(self.height):
			yield [self.pk.db[j][i] for j in headers]

	def row(self, row):
		'''Return a row in db'''
		headers = self.column_names
		return _PickleTRow(self, row, 0, {j: self.pk.db[j][row] for j in headers})

	def _set_cell(self, col, row, val):
		"""doesn't auto save"""
		self.pk.db[col][row] = val

	def set_cell(self, col, row, val):
		"""runs auto save"""
		self._set_cell(col, row, val)
		self.auto_dump()

	def pop_row(self, index=-1):
		for i in self.column_names:
			self.pk.db.pop(index)

		self.height -=1

	def del_row(self, index):
		self.lock(self.pop_row)(index)

		self.auto_dump()






	def _add_row(self, row:dict):
		#print(self.column_names)
		#print(self.pk.db)
		for k in self.column_names:
			self.pk.db[k].append(None)





		for k, v in row.items():
			self.pk.db[k][self.height] = v


		self.height += 1


	def add_row(self, row:dict):
			self.lock(self._add_row)(row)
			self.auto_dump()







	def dump(self):
		self.pk.dump()

	def auto_dump(self):
		self.pk._autodumpdb()


class _PickleTRow(dict):
	def __init__(self, source:PickleTable, index, rid, items):
		self.source = source
		self.index = index
		self.rid = rid
		super().__init__(items)

	def __delitem__(self, name):
		self.source[name][self.index] = None
		self.source.auto_dump()


	def del_row(self):
		self.source.del_row(self.index)



if __name__ != "__main__":
	import time, os

	st = time.time()
	for i in range(10):
		p = PickleDB("__test.pdb")
		p.set("nn", ['spam', 'eggs']*1000)

		p = PickleDB("__test.pdb")


	et = time.time()
	print(et - st)
	print("avg:", (et-st)/10)

if __name__ == "__main__":


	st = time.time()

	tb = PickleTable("test.pdb")

	print(tb.height)

	tb.add_column("x", 1)
	tb.add_column("Ysz",1)
	tb.add_column("Y", 1)

	print("adding")
	for n in range(555555):
		#print(n)
		tb._add_row({"x":n, "Y":00})

	tb.add_column("m", 1)

	#tb.del_colum("x")
	tb.dump()

	# print(tb)
	print("Total cells", tb.height * len(tb.column_names))

	et = time.time()
	print(et - st)
