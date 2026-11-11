from pathlib import Path

path = Path(__file__).with_name("pyroboxCore.py")
text = path.read_text(encoding="utf-8")
start = text.index(
	"\t@staticmethod\n\tdef on_req(method='', url='', hasQ=(), QV=None, fragent='', url_regex='', func=null):"
)
end = text.index("\tdef redirect(self, location, cookie:Union[SimpleCookie, str]=None):")

new = r'''	@staticmethod
	def on_req(
		method: str = '',
		url: str = '',
		hasQ: Optional[Union[str, Sequence[str]]] = None,
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
		func: HTTPRouteHandler = null,
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for an HTTP method and URL/query/fragment shape.

		Parameters
		----------
		method :
			HTTP verb (e.g. ``GET``, ``POST``, ``HEAD``). ``GET`` is stored with ``HEAD``.
		url :
			Exact path to match (``self.url_path``). Empty means no path constraint.
		hasQ :
			Query keys that must all be present (values ignored). A single string is
			treated as one key; use a sequence for several keys.
		QV :
			Query keys and exact string values that must match ``self.query``. Skipped
			if falsy (``None`` or empty mapping). Values are compared with ``!=`` to
			``self.query[k]``.
		fragent :
			URL fragment (hash) that must match ``self.fragment`` if non-empty.
		url_regex :
			If non-empty, ``self.url_path`` must match ``^`` + ``url_regex`` + ``$``.
		func :
			Handler to register when used as ``@handler.on_req(...)``; may be omitted
			and supplied by the decorator syntax.

		Returns
		-------
		Decorator that appends the route entry to ``handlers[method]``.
		"""
		self = __class__

		method = method.upper()
		if method == 'GET':
			method = 'HEAD'

		if method not in self.handlers:
			self.handlers[method] = []

		def decorator(func: HTTPRouteHandler = func) -> HTTPRouteHandler:
			# Freeze matcher + handler + inspect snapshot at decoration time (dispatch order = append order).
			self.handlers[method].append(
				build_route_handler_entry(
					url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex, func=func)
			)
			return func
		return decorator

	@staticmethod
	def on_GET(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for GET (stored under HEAD with ``on_req``)."""
		self = __class__

		return self.on_req(method='GET', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)

	@staticmethod
	def on_POST(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for POST."""
		self = __class__

		return self.on_req(method='POST', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)

	@staticmethod
	def on_HEAD(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for HEAD."""
		self = __class__

		return self.on_req(method='HEAD', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)

	@staticmethod
	def on_OPTIONS(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for OPTIONS."""
		self = __class__

		return self.on_req(method='OPTIONS', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)

	@staticmethod
	def on_DELETE(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for DELETE."""
		self = __class__

		return self.on_req(method='DELETE', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)

	@staticmethod
	def on_PUT(
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> Callable[[HTTPRouteHandler], HTTPRouteHandler]:
		"""Register a handler for PUT."""
		self = __class__

		return self.on_req(method='PUT', url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)


	@staticmethod
	def alt_directory(
		dir: str,
		method: str = '',
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
		cache_control: str = "",
		cookie: Optional[Union[SimpleCookie, str]] = None,
	) -> None:
		"""Serve one file from ``dir`` by last URL segment; registers via ``on_req``; returns ``None``."""
		self = __class__

		@self.on_req(method=method, url=url, hasQ=hasQ, QV=QV, fragent=fragent, url_regex=url_regex)
		def alt_dir_function(self: Type[__class__], *args, **kwargs):
			"""
			re-direct request to specific directory
			"""

			file = self.url_path.split("/")[-1]
			requested_file = tools.xpath(dir, file)

			if not os.path.exists(requested_file):
				self.send_error(code=HTTPStatus.NOT_FOUND, message="File not found")
				self.log_info(f'File not found: {requested_file}')
				return None

			return self.send_file(
				requested_file, 
				cookie=cookie,
				cache_control=cache_control
				)



	def log_error(self, *args, **kwargs):
		"""
		Log error as well as show the function name and info
		"""
		if getattr(self, 'handler_func', None):
			self.log_info(f'Error on [{self.handler_func_name}] -> [{self.handler_func_args}] -> at line [{self.handler_func_line}] -> in [{self.handler_func_file}]')

		return super().log_error(*args, **kwargs)


	def test_req(
		self,
		url: str = '',
		hasQ: Union[str, Sequence[str]] = (),
		QV: Optional[Mapping[str, Any]] = None,
		fragent: str = '',
		url_regex: str = '',
	) -> bool:
		"""Return True if the current request matches the registration pattern.

		Parameters match those passed to ``on_req`` / ``on_GET`` / etc.: exact ``url``,
		presence checks ``hasQ``, value checks ``QV``, optional ``fragent``, and
		optional full-path ``url_regex`` over ``self.url_path``.
		"""
		if url_regex and not re.search("^" + url_regex + '$', self.url_path):
			return False
		if url and url != self.url_path:
			return False

		if isinstance(hasQ, str):
			hasQ = (hasQ,)

		if hasQ and self.query(*hasQ) is False:
			return False
		if QV:
			for k, v in QV.items():
				if not self.query(k):
					return False
				if self.query[k] != v:
					return False

		if fragent and self.fragment != fragent:
			return False

		return True

	def do_HANDLE(self, method: str) -> None:
		"""Serve a single REQUEST."""
		method = method.upper()

		# GET is served from the HEAD handler table; the body is still
		# streamed below unless the actual request method was HEAD.
		dispatch = "HEAD" if method == "GET" else method

		if dispatch not in self.handlers:
			return self.send_error(
				code=HTTPStatus.NOT_IMPLEMENTED,
				message="Unsupported method (%r)" % self.command,
			)

		# ---- Range header ------------------------------------------------
		# ``(None, None)`` is truthy - leave unused range as None and gate on use_range.
		self.range = None
		self.use_range = False
		if "Range" in self.headers:
			try:
				self.range = parse_byte_range(self.headers["Range"])
				self.use_range = True
			except ValueError:
				return self.send_error(
					code=HTTPStatus.BAD_REQUEST,
					message="Invalid byte range",
				)

		path = self.translate_path(self.path)
		url_path, query, fragment = self.url_path, self.query, self.fragment
		spathsplit = self.url_path.split("/")

		try:
			# First matching RouteHandlerEntry wins; ``func`` is the registered callable.
			for entry in self.handlers[dispatch]:
				if not isinstance(entry, dict):
					continue
				check = entry.get("check")
				func = entry.get("func")
				if check is None or func is None:
					continue
				if not self.test_req(**check):
					continue

				self.log_info(
					f"[{dispatch}] -> [{entry.get('cache_name', func.__name__)}] -> {self.url_path}"
				)

				# Copy registration-time debug fields (no inspect.* here).
				self.handler_func = func
				self.handler_func_name = entry.get("cache_name", func.__name__)
				self.handler_func_args = entry.get("cache_args", "")
				self.handler_func_source = entry.get("source", "")
				self.handler_func_file = entry.get("cache_file", "")
				clines = entry.get("cache_lines")
				clineno = entry.get("cache_line")
				self.handler_func_lines = clines if clines else None
				self.handler_func_line = clineno if clineno else None

				try:
					resp = func(self, url_path=url_path, query=query,
								fragment=fragment, path=path,
								spathsplit=spathsplit)
				except PostError:
					self.log_error(traceback.format_exc())
					return self.send_error(
						code=HTTPStatus.BAD_REQUEST,
						message="Bad request",
					)

				if resp:
					try:
						if self.method != "HEAD":
							self.copyfile(resp, self.wfile)
					except (ConnectionAbortedError, ConnectionResetError,
							BrokenPipeError) as e:
						self.log_info(tools.text_box(
							e.__class__.__name__, e, "\nby ",
							[self.address_string()]))
					finally:
						close = getattr(resp, "close", None)
						if close is not None:
							close()
				return

			return self.send_error(
				code=HTTPStatus.NOT_FOUND, message="File Not Found.",
			)

		except (ConnectionAbortedError, ConnectionResetError,
				BrokenPipeError) as e:
			self.log_info(tools.text_box(
				e.__class__.__name__, e, "\nby ",
				[self.address_string()]))
		except Exception as e:
			self.log_error(traceback.format_exc())
			self.send_error(code=500, message=str(e))


'''

path.write_text(text[:start] + new + text[end:], encoding="utf-8")
t2 = path.read_text(encoding="utf-8")
assert "build_route_handler_entry(" in t2
assert "def do_HANDLE" in t2
assert "_load_handler_meta" not in t2
assert "linecache" not in t2
print("ok", len(new))
