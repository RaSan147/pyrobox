"""url_path / query / fragment parsing and request matching."""

import os
import sys

import pytest


def _bare_handler(directory=None):
	from pyroboxCore import Callable_dict, SimpleHTTPRequestHandler

	h = SimpleHTTPRequestHandler.__new__(SimpleHTTPRequestHandler)
	h.directory = os.fspath(directory or os.getcwd())
	h.url_path = '/'
	h.query = Callable_dict()
	h.fragment = ''
	h.method = 'GET'
	h.use_range = False
	h.range = None
	h.path = '/'
	return h


class TestURLManager:
	def test_splits_path_query_fragment(self):
		from pyroboxCore import URL_MANAGER

		path, query, fragment = URL_MANAGER('/store?page=10&limit=15#frag')
		assert path == '/store'
		assert query['page'] == ['10']
		assert query['limit'] == ['15']
		assert fragment == 'frag'

	def test_empty_path_becomes_root(self):
		from pyroboxCore import URL_MANAGER

		path, query, fragment = URL_MANAGER('?x=1')
		assert path == '/'
		assert query['x'] == ['1']
		assert fragment == ''

	def test_keeps_blank_query_values(self):
		from pyroboxCore import URL_MANAGER

		_, query, _ = URL_MANAGER('/a?flag=')
		assert query['flag'] == ['']


class TestHandlerUrlPathAttrs:
	def test_handle_one_request_attrs_are_declared_and_assignable(self, served_dir):
		h = _bare_handler(served_dir)
		assert h.url_path == '/'
		assert h.fragment == ''
		assert list(h.query.keys()) == []

		h.url_path = '/files/readme.txt'
		h.query['download'] = ['1']
		h.fragment = 'top'
		assert h.url_path.endswith('readme.txt')
		assert h.query('download') is not False
		assert h.fragment == 'top'

	def test_annotations_include_url_path(self):
		from pyroboxCore import BaseHTTPRequestHandler, SimpleHTTPRequestHandler

		base_ann = getattr(BaseHTTPRequestHandler, '__annotations__', {})
		assert 'url_path' in base_ann
		assert 'query' in base_ann
		assert 'fragment' in base_ann

		handler_ann = getattr(SimpleHTTPRequestHandler, '__annotations__', {})
		assert 'handlers' in handler_ann
		assert 'directory' in handler_ann


class TestTestReq:
	def test_exact_url_and_regex(self, served_dir):
		h = _bare_handler(served_dir)
		h.url_path = '/api/v1/items'

		assert h.test_req(url='/api/v1/items') is True
		assert h.test_req(url='/other') is False
		assert h.test_req(url_regex=r'/api/v\d+/items') is True
		assert h.test_req(url_regex=r'/api/v2/items') is False

	def test_query_and_fragment_checks(self, served_dir):
		from pyroboxCore import Callable_dict

		h = _bare_handler(served_dir)
		h.url_path = '/search'
		h.query = Callable_dict({'q': ['pyro'], 'page': ['1']})
		h.fragment = 'results'

		assert h.test_req(url='/search', hasQ='q') is True
		assert h.test_req(url='/search', hasQ=('q', 'page')) is True
		assert h.test_req(url='/search', hasQ='missing') is False
		assert h.test_req(url='/search', QV={'q': ['pyro']}) is True
		assert h.test_req(url='/search', QV={'q': ['nope']}) is False
		assert h.test_req(url='/search', fragent='results') is True
		assert h.test_req(url='/search', fragent='other') is False


class TestRouteRegistration:
	def test_on_req_registers_typed_handler_entry(self):
		from pyroboxCore import SimpleHTTPRequestHandler

		# Isolate: use a fresh method bucket so other tests are unaffected.
		method = 'PATCH'
		before = list(SimpleHTTPRequestHandler.handlers.get(method, []))

		@SimpleHTTPRequestHandler.on_req(method=method, url='/typed-route')
		def _typed_route_handler(self, **kwargs):
			return None

		try:
			entries = SimpleHTTPRequestHandler.handlers[method]
			assert len(entries) == len(before) + 1
			entry = entries[-1]
			assert set(entry.keys()) >= {
				'check', 'func', 'source', 'cache_name',
				'cache_args', 'cache_file', 'cache_line', 'cache_lines',
			}
			assert entry['func'] is _typed_route_handler
			assert entry['check']['url'] == '/typed-route'
		finally:
			SimpleHTTPRequestHandler.handlers[method] = before

	def test_alt_directory_handler_reads_instance_url_path(self, tmp_path):
		from pyroboxCore import SimpleHTTPRequestHandler

		asset_dir = tmp_path / 'assets'
		asset_dir.mkdir()
		(asset_dir / 'logo.txt').write_text('ok', encoding='utf-8')

		method = 'TRACE'
		before = list(SimpleHTTPRequestHandler.handlers.get(method, []))
		SimpleHTTPRequestHandler.alt_directory(
			dir=os.fspath(asset_dir),
			method=method,
			url='/static/logo.txt',
		)

		try:
			entry = SimpleHTTPRequestHandler.handlers[method][-1]
			h = _bare_handler(tmp_path)
			h.url_path = '/static/logo.txt'
			sent = {}

			def fake_send_file(path, filename=None, download=False, cookie=None, cache_control=''):
				sent['path'] = path
				return True

			h.send_file = fake_send_file
			h.send_error = lambda **kwargs: (_ for _ in ()).throw(AssertionError(kwargs))
			assert entry['func'](h) is True
			assert os.path.basename(sent['path']) == 'logo.txt'
		finally:
			SimpleHTTPRequestHandler.handlers[method] = before


@pytest.mark.parametrize('py_flag', ['-3.8', '-3.14'])
def test_import_on_supported_pythons(py_flag):
	"""Smoke-import pyroboxCore with installed 3.8 and 3.14 interpreters."""
	import shutil
	import subprocess
	from pathlib import Path

	py_launcher = shutil.which('py')
	if not py_launcher:
		pytest.skip('Windows py launcher not available')

	probe = subprocess.run(
		[py_launcher, py_flag, '-c', 'import sys; print(sys.version)'],
		capture_output=True,
		text=True,
	)
	if probe.returncode != 0:
		pytest.skip('Python %s not installed: %s' % (py_flag, probe.stderr.strip()))

	core = Path(__file__).resolve().parents[1] / 'pyroboxCore.py'
	code = (
		"import importlib.util, pathlib, sys; "
		"assert sys.version_info >= (3, 8); "
		"p=pathlib.Path(r'%s'); "
		"s=importlib.util.spec_from_file_location('pyroboxCore', p); "
		"m=importlib.util.module_from_spec(s); "
		"s.loader.exec_module(m); "
		"assert 'url_path' in m.BaseHTTPRequestHandler.__annotations__; "
		"h=m.SimpleHTTPRequestHandler.__new__(m.SimpleHTTPRequestHandler); "
		"h.url_path='/x'; h.query=m.Callable_dict(); h.fragment=''; "
		"assert h.test_req(url='/x') is True"
	) % (str(core).replace('\\', '\\\\'),)

	result = subprocess.run(
		[py_launcher, py_flag, '-I', '-c', code],
		capture_output=True,
		text=True,
		timeout=30,
	)
	assert result.returncode == 0, result.stderr or result.stdout
