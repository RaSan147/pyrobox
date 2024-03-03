from http import HTTPStatus
import os
from typing import Union

from ._fs_utils import get_titles, dir_navigator
from .pyroDB import PickleTable
from . import user_mgmt as u_mgmt
from .user_mgmt import User

from .pyroboxCore import config as CoreConfig, SimpleHTTPRequestHandler as SH_base, SimpleCookie, tools


from string import Template
from . import _page_templates as pt






class ServerConfig():
	def __init__(self, cli_args):
		self.name = cli_args.name
		self.admin_username = cli_args.admin_id
		self.admin_password = cli_args.admin_pass

		self.uDB = PickleTable()
		self.configDB = PickleTable()
		self.cli_args = cli_args


		self.GUESTS =  not self.cli_args.no_guest_allowed  # unless account mode, everyone is guest

		self.admin_perms = []
		self.member_perms = []
		self.guest_perms = []

		self.init_config()
		self.init_permissions(cli_args=cli_args)
		self.init_account()

		# Max size a zip file will be made
		self.max_zip_size = 6*1024*1024*1024 # 6GB

	def init_config(self):
		if self.name:
			if not self.name:
				raise ValueError("If you want to create a server User accounts based, value of --name is required")
			if not (self.admin_username and self.admin_password):
				raise ValueError("If you want to create a User accounts based server, --name and --admin-id and --admin-pass values are required")

			config_loc = os.path.join(CoreConfig.MAIN_FILE_dir, "config", self.name+ ".pdb")

			os.makedirs(os.path.dirname(config_loc), exist_ok=True)
			self.configDB = PickleTable(config_loc)

		self.configDB.add_column("name", "value", exist_ok=True)



	def init_account(self):
		userDB_loc = "" # will  create in memory
		if self.name:
			userDB_loc = os.path.join(CoreConfig.MAIN_FILE_dir, "userDB", self.name+ ".pdb")
			os.makedirs(os.path.dirname(userDB_loc), exist_ok=True)

		self.user_handler = u_mgmt.User_handler(init_permissions= {"member": self.member_perms, "admin": self.admin_perms, "guest": self.guest_perms})

		self.user_handler.load_db(userDB_loc)
		self.uDB = self.user_handler.user_db

		if (self.admin_username and self.admin_password):
			_admin = self.user_handler.get_user(self.admin_username, temp=True)

			if _admin:
				if not _admin.is_admin:
					raise ValueError(tools.text_box("Provided username is not an admin"))
				if not _admin.check_password(self.admin_password):
					raise ValueError(tools.text_box("Admin password is incorrect"))

			elif self.uDB.height == 0:
				self.user_handler.create_admin(self.admin_username, self.admin_password)

			else:
				raise ValueError(tools.text_box("Please start the server with an existing admin account"))

		if self.GUESTS:
			self.guest_id = self.user_handler.create_guest()

# This will contain server configurations, user database and limits.


	def init_permissions(self, cli_args):
		def check(arg, perm):
			if arg:
				return perm

		permits = u_mgmt.permits

		DefaultPerms = self.configDB.find_1st("DefaultPerm", 'name')

		if DefaultPerms:
			self.DefaultPerms = DefaultPerms.row_obj()
		else:
			self.DefaultPerms = self.configDB.add_row(dict(name="DefaultPerm", value={}))

		def remove_perm(perm_list, perm):
			if perm in perm_list:
				perm_list.remove(perm)

		if self.DefaultPerms["value"].get("member", None):
			self.member_perms = User.unpack_permission_to_list(self.DefaultPerms["value"]["member"])
		else:
			self.member_perms = [
				permits.VIEW,
				check(not cli_args.no_upload, permits.UPLOAD),
				check(not cli_args.no_zip, permits.ZIP),
				check(not cli_args.no_modify, permits.MODIFY),
				check(not cli_args.no_delete, permits.DELETE),
				check(not cli_args.no_download, permits.DOWNLOAD),
				permits.MEMBER,
			]

			if cli_args.view_only or cli_args.read_only:
				remove_perm(self.member_perms, permits.UPLOAD)
				remove_perm(self.member_perms, permits.MODIFY)
				remove_perm(self.member_perms, permits.DELETE)

			if cli_args.view_only:
				remove_perm(self.member_perms, permits.DOWNLOAD)


		#######

		if self.DefaultPerms["value"].get("admin", None):
			self.admin_perms = User.unpack_permission_to_list(self.DefaultPerms["value"]["admin"])
		else:
			self.admin_perms = [
				permits.VIEW,
				permits.DELETE,
				permits.DOWNLOAD,
				permits.MODIFY,
				permits.UPLOAD,
				permits.ZIP,
				permits.ADMIN,
				permits.MEMBER,
			]


		#######
		if self.DefaultPerms["value"].get("guest", None):
			self.guest_perms = User.unpack_permission_to_list(self.DefaultPerms["value"]["guest"])
		elif not self.name:
			self.guest_perms = self.member_perms # if no account mode, guest is member
			self.guest_perms.remove(permits.MEMBER) # remove member permission

		else:
			self.guest_perms = [
				check(cli_args.guest_allowed, permits.VIEW),
				check(not cli_args.no_upload, permits.UPLOAD),
				check(not cli_args.no_zip, permits.ZIP),
				check(not cli_args.no_modify, permits.MODIFY),
				check(not cli_args.no_delete, permits.DELETE),
				check(not cli_args.no_download, permits.DOWNLOAD),
			]

			if cli_args.view_only or cli_args.read_only:
				remove_perm(self.guest_perms, permits.UPLOAD)
				remove_perm(self.guest_perms, permits.MODIFY)
				remove_perm(self.guest_perms, permits.DELETE)

			if cli_args.view_only:
				remove_perm(self.guest_perms, permits.DOWNLOAD)


		# remove None values
		self.member_perms = [x for x in self.member_perms if x is not None]
		self.admin_perms = [x for x in self.admin_perms if x is not None]
		self.guest_perms = [x for x in self.guest_perms if x is not None]

		self.update_config_perms() # update the config file with the new permissions | can be used from the admin page

	def update_config_perms(self):
			"""
			Update the permissions in the config file database

			This method updates the default permissions for members, admins, and guests.
			"""
			self.DefaultPerms["value"]["member"] = User.pack_permission_from_list(self.member_perms)
			self.DefaultPerms["value"]["admin"] = User.pack_permission_from_list(self.admin_perms)
			self.DefaultPerms["value"]["guest"] = User.pack_permission_from_list(self.guest_perms)



	def get_users(self):
		return self.uDB.get_column("username")






#############################################
#            PATCH SERVER CLASS            #
#############################################




class ServerHost(SH_base):
	"""
	Just a wrapper for SH_base to add some extra functionality
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


	def html_main_page(self, user:User, *args, cookie:Union[SimpleCookie, str]=None,  **kwargs):
		"""
		Return HTML page for the directory listing
		"""

		if user.NOPERMISSION or user.VIEW == False:
			return self.send_error(HTTPStatus.UNAUTHORIZED, "You don't have permission to see file list", cookie=cookie)


		displaypath = self.get_displaypath(self.url_path)

		title = get_titles(displaypath)

		_format = pt.directory_explorer_header().safe_substitute(
			PY_ERROR_PAGE="",
			PY_PAGE_TITLE=title,
			PY_PUBLIC_URL=CoreConfig.address(),
			PY_DIR_TREE_NO_JS=dir_navigator(displaypath),
			*args, **kwargs)

		return self.send_text(_format,  cookie=cookie)


	def send_error(self, code, message=None, explain=None, cookie:Union[SimpleCookie, str]=None):
		self.log_warning(["ERROR", code, message, explain]) # why warning? because it's not an server error, it's just a warning of error on client side

		displaypath = self.get_displaypath(self.url_path)

		title = get_titles(displaypath)

		_format = pt.error_page().safe_substitute(
			PY_ERROR_PAGE="active",
			PY_PAGE_TITLE=title,
			PY_PUBLIC_URL=CoreConfig.address(),
			PY_DIR_TREE_NO_JS=dir_navigator(displaypath))

		return super().send_error(code, message, explain, Template(_format), cookie=cookie)
