"""Tests for rename / new_folder / permanent delete path + permission logic.

Handlers in server.py are not imported (module-level CLI side effects). These
tests exercise the same resolution + FS steps the handlers use.
"""

import os
import shutil

import pytest

from pyroboxCore import validate_client_relpath
from user_mgmt import permits


def _resolve(handler, url_path, filename):
	"""Mirror delete/rename/new_folder destination resolution."""
	filename = filename.strip()
	rel_path = handler.get_rel_path(filename)
	if not handler.path_safety_check(filename, rel_path):
		return None
	import posixpath
	return handler.translate_path(posixpath.join(url_path, filename))


def _can_modify(user):
	return (not user.NOPERMISSION) and user.MODIFY


def _can_delete(user):
	return (not user.NOPERMISSION) and user.DELETE


@pytest.fixture
def work_handler(tmp_path):
	"""Handler whose directory is an isolated temp served root with a seed file."""
	from pyroboxCore import SimpleHTTPRequestHandler

	root = tmp_path / 'served'
	root.mkdir()
	(root / 'seed.txt').write_text('seed', encoding='utf-8')
	(root / 'subdir').mkdir()
	(root / 'subdir' / 'nested.txt').write_text('nested', encoding='utf-8')

	h = SimpleHTTPRequestHandler.__new__(SimpleHTTPRequestHandler)
	h.directory = os.fspath(root)
	h.url_path = '/'
	return h, root


class TestFileOpPermissions:
	def test_modify_required_for_rename_and_mkdir(self, member_user):
		assert _can_modify(member_user) is True
		member_user.revoke(permits.MODIFY)
		assert _can_modify(member_user) is False

	def test_delete_required(self, member_user):
		assert _can_delete(member_user) is True
		member_user.revoke(permits.DELETE)
		assert _can_delete(member_user) is False

	def test_nopermission_blocks_all(self, member_user):
		member_user.permit(permits.NOPERMISSION)
		assert _can_modify(member_user) is False
		assert _can_delete(member_user) is False

	def test_guest_without_modify(self, user_handler):
		guest = user_handler.create_guest()
		# default guest fixture perms include no MODIFY in default_guest_perms
		# (VIEW, DOWNLOAD, UPLOAD, ZIP only)
		assert guest.MODIFY is False
		assert _can_modify(guest) is False


class TestNewFolder:
	def test_creates_folder(self, work_handler):
		handler, root = work_handler
		dest = _resolve(handler, '/', 'brand_new')
		assert dest is not None
		assert not os.path.exists(dest)
		os.makedirs(dest)
		assert os.path.isdir(os.path.join(root, 'brand_new'))

	def test_nested_folder(self, work_handler):
		handler, root = work_handler
		dest = _resolve(handler, '/', 'a/b/c')
		# translate_path joins segments; handler creates leaf via makedirs
		assert dest is not None
		os.makedirs(dest)
		assert os.path.isdir(os.path.join(root, 'a', 'b', 'c'))

	def test_rejects_traversal_name(self, work_handler):
		handler, root = work_handler
		assert _resolve(handler, '/', '../outside') is None
		# Absolute URL-style names are remapped under the served root (translate_path),
		# not written outside - assert containment rather than total reject.
		dest = _resolve(handler, '/', '/etc/passwd')
		assert dest is not None
		assert handler.path_is_under_directory(dest)
		assert os.path.abspath(dest).startswith(os.path.abspath(str(root)))

	def test_rejects_absolute_upload_style_name(self, work_handler):
		handler, _ = work_handler
		# validate_client_relpath is stricter for uploads; path_safety also rejects drive
		assert handler.path_safety_check('C:/Windows') is False

	def test_existing_folder_detected(self, work_handler):
		handler, root = work_handler
		dest = _resolve(handler, '/', 'subdir')
		assert dest is not None
		assert os.path.exists(dest)


class TestRename:
	def test_rename_file(self, work_handler):
		handler, root = work_handler
		src = _resolve(handler, '/', 'seed.txt')
		dst = _resolve(handler, '/', 'renamed.txt')
		assert src and dst
		os.rename(src, dst)
		assert not (root / 'seed.txt').exists()
		assert (root / 'renamed.txt').read_text(encoding='utf-8') == 'seed'

	def test_rename_into_subdir(self, work_handler):
		handler, root = work_handler
		src = _resolve(handler, '/', 'seed.txt')
		dst = _resolve(handler, '/', 'subdir/moved.txt')
		assert src and dst
		os.rename(src, dst)
		assert (root / 'subdir' / 'moved.txt').exists()

	def test_rejects_dotdot_new_name(self, work_handler):
		handler, _ = work_handler
		assert _resolve(handler, '/', '../escape.txt') is None

	def test_rejects_unsafe_either_side(self, work_handler):
		handler, _ = work_handler
		assert handler.path_safety_check('seed.txt', '../x') is False
		assert handler.path_safety_check('../x', 'ok.txt') is False


class TestDeletePermanent:
	def test_delete_file(self, work_handler):
		handler, root = work_handler
		path = _resolve(handler, '/', 'seed.txt')
		assert path and os.path.isfile(path)
		os.remove(path)
		assert not (root / 'seed.txt').exists()

	def test_delete_directory_tree(self, work_handler):
		handler, root = work_handler
		path = _resolve(handler, '/', 'subdir')
		assert path and os.path.isdir(path)
		shutil.rmtree(path)
		assert not (root / 'subdir').exists()

	def test_rejects_delete_outside(self, work_handler):
		handler, root = work_handler
		assert _resolve(handler, '/', '../seed.txt') is None
		# seed still present - no escape delete
		assert (root / 'seed.txt').exists()


class TestOddLiveNames:
	"""Odd filenames under test/live_served must resolve under the served root."""

	@pytest.fixture
	def live_handler(self):
		from pyroboxCore import SimpleHTTPRequestHandler

		live = os.path.join(
			os.path.dirname(__file__), '..', 'test-dir', 'live_served')
		live = os.path.abspath(live)
		if not os.path.isdir(live):
			pytest.skip('live_served fixture missing')

		h = SimpleHTTPRequestHandler.__new__(SimpleHTTPRequestHandler)
		h.directory = live
		h.url_path = '/'
		return h, live

	@pytest.mark.parametrize(
		'name',
		[
			'plain.txt',
			'file (1).txt',
			'Utf-8 café.txt',
			'name-with-dots...txt',
			'UPPER_and_lower.TXT',
			'plus+plus.txt',
			'emoji 📦 name.txt',
		],
	)
	def test_odd_files_resolve_inside_root(self, live_handler, name):
		handler, live = live_handler
		path = _resolve(handler, '/', name)
		assert path is not None
		assert handler.path_is_under_directory(path)
		assert os.path.isfile(path)

	@pytest.mark.parametrize(
		'name',
		[
			'Empty Folder',
			'Folder & with (bad) name!',
			'spaces in folder name',
			'nested deep/level two',
		],
	)
	def test_odd_dirs_resolve_inside_root(self, live_handler, name):
		handler, live = live_handler
		path = _resolve(handler, '/', name)
		assert path is not None
		assert handler.path_is_under_directory(path)
		assert os.path.isdir(path)

	def test_hash_in_filename_is_truncated_by_translate_path(self, live_handler):
		"""translate_path strips '#' as a URL fragment - known limitation for such names."""
		handler, live = live_handler
		# Fixture uses underscore form that survives URL/path translation
		path = _resolve(handler, '/', 'hash_sharp_tag.txt')
		assert path is not None
		assert os.path.isfile(path)
		# Raw '#' name would be cut to 'hash' by translate_path
		cut = handler.translate_path('/hash#tag.txt')
		assert os.path.basename(cut.rstrip('/\\')) == 'hash'

	def test_validate_client_relpath_allows_parens_and_spaces(self):
		assert validate_client_relpath('file (1).txt') == 'file (1).txt'
		assert validate_client_relpath('spaces in folder name/inner file.txt') == (
			'spaces in folder name/inner file.txt')
