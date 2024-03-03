from collections import OrderedDict


class Callable_dict(dict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __call__(self, *key):
		return all([i in self for i in key])


class GETdict(Callable_dict):
	"""
	to set item, use dict["key"] = value for the 1st time,
	then use dict.key or dict["key"] to both get and set value

	but using dick.key = value 1st, will assign it as attribute and its temporary
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self


	def __setitem__(self, key, value):
		super().__setitem__(key, value)

	def __setattr__(self, key, value):
		if self(key):
			self.__setitem__(key, value)
		else:
			super().__setattr__(key, value)

	def  __getattr__(self, __name: str):
		if self(__name):
			return self.__getitem__(__name)
		return super().__getattribute__(__name)


	# def __getitem__(self, __key):
	# 	return super().__getitem__(__key)

class Flag(GETdict):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__ = self

	def __getitem__(self, __key):
		return super().get(__key, None)

	def  __getattr__(self, __name: str):
		return super().get(__name, None)
		# try:
		# 	return super().__getitem__(__name)
		# except Exception:
		# 	return None


class LimitedDict(OrderedDict):
    def __init__(self, *args, max=0, **kwargs):
        self._max = max
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self._max > 0:
            if len(self) > self._max:
                self.popitem(False)



from string import Template as _Template

class Template(_Template):
	"""Custom string.Template class that supports addition of string and template"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __add__(self, other):
		if isinstance(other, _Template):
			return Template(self.template + other.template)
		return Template(self.template + str(other))



from queue import Queue

class Zfunc(object):
	"""Thread safe sequncial printing/queue task handler class"""

	__all__ = ["new", "update"]
	def __init__(self, caller, store_return=False):
		super().__init__()

		self.queue = Queue()
		# stores [args, kwargs], ...
		self.store_return = store_return
		self.returner = Queue()
		# queue to store return value if store_return enabled

		self.BUSY = False

		self.caller = caller

	def next(self):
		""" check if any item in queje and call, if already running or queue empty, returns """
		if self.queue.empty() or self.BUSY:
			return None

		self.BUSY = True
		args, kwargs = self.queue.get()

		x = self.caller(*args, **kwargs)
		if self.store_return:
			self.returner.put(x)

		self.BUSY = False

		if not self.queue.empty():
			# will make the loop continue running
			return True


	def update(self, *args, **kwargs):
		""" Uses xprint and parse string"""

		self.queue.put((args, kwargs))
		while self.next() is True:
			# use while instead of recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion to avoid recursion.... error
			pass



	def new(self, caller, store_return=False):
		self.__init__(caller, store_return)

