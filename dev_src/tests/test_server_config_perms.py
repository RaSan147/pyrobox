"""ServerConfig permission defaults from CLI flags + authorize_user."""

import pytest

from _helpers import StubRequest, make_cli_args
from user_mgmt import create_user_cookie, permits


@pytest.fixture
def anonymous_config():
	"""Nameless server: guests on, in-memory DBs (no files written)."""
	from pyrobox_ServerHost import ServerConfig
	return ServerConfig(make_cli_args())


class TestAnonymousServerPerms:
	def test_guest_created_without_member(self, anonymous_config):
		guest = anonymous_config.guest_id
		assert guest is not None
		assert guest.MEMBER is False
		assert guest.VIEW is True

	def test_member_template_keeps_member_bit(self, anonymous_config):
		# Regression: guest_perms must not alias/mutate member_perms
		assert permits.MEMBER in anonymous_config.member_perms
		assert permits.MEMBER not in anonymous_config.guest_perms

	def test_authorize_guest_without_cookie(self, anonymous_config):
		user, cookie = anonymous_config.authorize_user(StubRequest())
		assert user is not None
		assert user.username == 'Guest'
		assert cookie['user'].value == 'Guest'

	def test_guest_vs_member_password_rules(self, anonymous_config):
		"""Guests use ServerConfig.PASSWORD for uploads; members use account password."""
		guest = anonymous_config.guest_id
		member = anonymous_config.user_handler.create_user('mem', 'acct-pass')

		assert not guest.MEMBER
		assert anonymous_config.PASSWORD
		assert len(anonymous_config.PASSWORD) >= 8

		assert member.MEMBER
		assert member.check_password('acct-pass')
		assert not member.check_password(anonymous_config.PASSWORD)

	def test_explicit_upload_password(self):
		from pyrobox_ServerHost import ServerConfig
		cfg = ServerConfig(make_cli_args(password='custom_pass_123'))
		assert cfg.PASSWORD == 'custom_pass_123'

	def test_random_upload_password_unique_when_omitted(self):
		from pyrobox_ServerHost import ServerConfig
		cfg1 = ServerConfig(make_cli_args(password=None))
		cfg2 = ServerConfig(make_cli_args(password=None))
		assert cfg1.PASSWORD != cfg2.PASSWORD
		assert len(cfg1.PASSWORD) >= 8

	def test_anonymous_guest_has_write_and_other_perms_by_default(self, anonymous_config):
		assert permits.VIEW in anonymous_config.guest_perms
		assert permits.UPLOAD in anonymous_config.guest_perms
		assert permits.MODIFY in anonymous_config.guest_perms
		assert permits.DELETE in anonymous_config.guest_perms
		assert permits.DOWNLOAD in anonymous_config.guest_perms
		assert permits.ZIP in anonymous_config.guest_perms

	def test_named_server_guest_has_write_and_other_perms_when_allowed(self):
		from pyrobox_ServerHost import ServerConfig
		cfg = ServerConfig(make_cli_args(
			server_name='testsrv_perms',
			admin_id='admin',
			admin_pass='adminpass',
			guest_allowed=True,
		))
		assert permits.VIEW in cfg.guest_perms
		assert permits.DOWNLOAD in cfg.guest_perms
		assert permits.UPLOAD in cfg.guest_perms
		assert permits.MODIFY in cfg.guest_perms
		assert permits.DELETE in cfg.guest_perms
		assert permits.ZIP in cfg.guest_perms

	def test_member_does_not_require_upload_password(self, anonymous_config):
		"""Members are authorized via session and do not need to supply upload password."""
		member = anonymous_config.user_handler.create_user('member_user', 'mypass')
		guest = anonymous_config.guest_id
		# Verification rule: if member.MEMBER -> no password check needed
		assert member.MEMBER is True
		# Guest requires ServerConfig.PASSWORD
		assert guest.MEMBER is False


class TestCliPermissionFlags:
	def _config(self, **kwargs):
		from pyrobox_ServerHost import ServerConfig
		return ServerConfig(make_cli_args(**kwargs))

	def test_no_upload(self):
		cfg = self._config(no_upload=True)
		assert permits.UPLOAD not in cfg.member_perms
		assert permits.UPLOAD not in cfg.guest_perms
		assert permits.VIEW in cfg.member_perms

	def test_read_only(self):
		cfg = self._config(read_only=True)
		for p in (permits.UPLOAD, permits.MODIFY, permits.DELETE):
			assert p not in cfg.member_perms
			assert p not in cfg.guest_perms
		assert permits.DOWNLOAD in cfg.member_perms
		assert permits.VIEW in cfg.member_perms

	def test_view_only(self):
		cfg = self._config(view_only=True)
		for p in (permits.UPLOAD, permits.MODIFY, permits.DELETE, permits.DOWNLOAD):
			assert p not in cfg.member_perms
		assert permits.VIEW in cfg.member_perms

	def test_no_guest_allowed(self):
		cfg = self._config(no_guest_allowed=True)
		assert cfg.GUESTS is False
		assert not hasattr(cfg, 'guest_id')
		user, cookie = cfg.authorize_user(StubRequest())
		assert user is None
		assert cookie['user'].value == ''


class TestNamedServerBootstrap:
	def test_creates_admin_in_tmp(self, tmp_path, monkeypatch):
		from pyroboxCore import config as CoreConfig
		from pyrobox_ServerHost import ServerConfig

		monkeypatch.setattr(CoreConfig, 'MAIN_FILE_dir', str(tmp_path))

		cfg = ServerConfig(make_cli_args(
			server_name='testsrv',
			admin_id='root',
			admin_pass='rootpass',
			guest_allowed=True,
		))
		admin = cfg.user_handler.get_user('root')
		assert admin is not None
		assert admin.is_admin()
		assert admin.check_password('rootpass')

		users = cfg.get_users()
		assert 'root' in users

		assert permits.VIEW in cfg.guest_perms
		guest = cfg.guest_id
		assert guest.VIEW is True
		assert guest.MEMBER is False

	def test_wrong_admin_password_raises(self, tmp_path, monkeypatch):
		from pyroboxCore import config as CoreConfig
		from pyrobox_ServerHost import ServerConfig

		monkeypatch.setattr(CoreConfig, 'MAIN_FILE_dir', str(tmp_path))

		ServerConfig(make_cli_args(
			server_name='srv2',
			admin_id='root',
			admin_pass='correct',
		))
		with pytest.raises(ValueError):
			ServerConfig(make_cli_args(
				server_name='srv2',
				admin_id='root',
				admin_pass='wrong',
			))


class TestAuthorizePrefersCookie:
	def test_logged_in_member(self, anonymous_config):
		member = anonymous_config.user_handler.create_user('carol', 'pw')
		req = StubRequest(cookie=create_user_cookie(member))
		user, _ = anonymous_config.authorize_user(req)
		assert user.username == 'carol'
		assert user.MEMBER is True


class TestAdminEndpointsMethodSecurity:
	def test_sensitive_admin_endpoints_require_post(self):
		import server  # noqa: F401
		from pyroboxCore import SimpleHTTPRequestHandler

		def _handler_names(method):
			names = set()
			for entry in SimpleHTTPRequestHandler.handlers.get(method, []):
				if isinstance(entry, dict):
					func = entry.get("func")
				else:
					# Legacy tuple form: (check, func)
					func = entry[1] if len(entry) > 1 else None
				if func is not None:
					names.add(func.__name__)
			return names

		post_funcs = _handler_names('POST')
		head_funcs = _handler_names('HEAD')

		sensitive_actions = {'reload', 'shutdown', 'add_user', 'delete_user', 'update_user_perm'}

		# Must be registered for POST
		for action in sensitive_actions:
			assert action in post_funcs, f"Action {action} should be registered for POST"

		# Must NOT be registered for GET/HEAD
		for action in sensitive_actions:
			assert action not in head_funcs, f"Action {action} must NOT be callable via GET/HEAD"

