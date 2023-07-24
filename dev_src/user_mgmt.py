# import pickledb
import hashlib
import time, datetime
from secrets import compare_digest
from pyroboxCore import config, logger
from enum import Enum
from typing import Tuple, List, Literal, TypeVar, Union

from data_types import LimitedDict

import binascii

from pyroDB import PickleTable

# Loads user database. Database is plaintext but stores passwords as a hash salted by config.PASSWORD


__all__ = [
	"user_handler",
	"User",
	"UserPermission",
	"permits"
]



def compare_digest_hex(digest, hex):
	return compare_digest(hex.encode("ascii"), binascii.hexlify(digest))






class UserPermission(Enum):
	"""Enum for WebUI user permissions, inspired by Unix permission style

	Args:
		Enum (int): Permission code for user
	"""

	NOPERMISSION = 0
	VIEW = 1        # view file list
	DOWNLOAD = 2    # download files
	MODIFY = 3      # rename, overwrite, new folder
	DELETE = 4      # delete files
	UPLOAD = 5      # upload files
	ZIP = 6         # download zip folder

permits = UserPermission # lazy to type long words


class PermissionList(list):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __getattr__(self, name:str):
		name = name.upper()
		options = dict(
			VIEW = 0,       # view file list
			DOWNLOAD = 1,   # download files
			MODIFY = 2,     # rename, overwrite, new folder
			DELETE = 3,     # delete files
			UPLOAD = 4,     # upload files
			ZIP = 5,        # download zip folder
		)
		if name in options:
			return bool(self[options[name]])

		if name == "NOPERMISSION":
			return not any(self)


class User:
	"""Object for WebUI users"""
	def __init__(
		self, row={}
	):
		"""Generate Object for WebUI users

		Args:
			row (_PickleTRow|dict): user data row
			[username] (str): plaintext username
			[permission] (int): compiled UserPermission set
			[password ](str, hash): hashed password.

		Raises:
			ValueError: User failed to create

		Returns:
			User: Object for WebUI users
		"""


		self.db = row
		self.user_handler = user_handler # type: User_handler




	Self = TypeVar("Self")
	# self reference for use in classmethods that can't strong type User because it's inside the method

	@property
	def username(self):
		return self.db["username"]

	@property
	def permission_pack(self):
		return self.db["permission"]

	@property
	def password(self):
		return self.db["password"]

	@property
	def token(self):
		return self.db["token"]

	@property
	def permission(self):
		return self.unpack_permission(self.permission_pack)
	
	
	def is_admin(self):
		return self in self.user_handler.admins

	# get the sha1 hash of the CLI password to use as a salt, makes a longer string and avoids holding secrets in memory

	def salt_password(self, password):
		return hashlib.sha256((self.user_handler.common_salt+password).encode('utf-8')).digest()

	def set_password(self, password:str):
		# salt, hash and store password
		p_hash = self.salt_password(password)
		token = hashlib.sha256(p_hash + str(time.time()).encode()).digest()

		# only store binary data

		self.update("password", p_hash)
		self.update("token", token)

	

	def reset_pw(self, old_password: str, new_password: str) -> int:
		"""Reset password

		Args:
			old_password (str): Old plaintext password for confirmation before change
			new_password (str): New plaintext password to be saved

		Returns:
			int: True if old_password accepted, else False
		"""


		if self.check_pass(old_password):
			logger.info(f"Updating password of user {self.username}")
			salted_new_password = self.salt_password(new_password)

			self.update("password", salted_new_password)
			return True
		else:
			logger.info(f"User {self.username} password mismatch")
			return False

	def __setitem__(self, attr, value):
		self.update(attr, value)

	def __getitem__(self, attr):
		return self.db[attr]

	def update(self, attr, value):
		self.db[attr] = value

	def unpack_permission(self, packed: int) -> List[int]:
		"""Unpacks permission as int -> list of binary/bool switches like [0,1,0,0,1,0]

		Args:
			packed (int): permission stored as an integer in the object and db

		Returns:
			List[int]: list of binary switches to be changed [reversed to make correct order]
		"""
		return PermissionList([packed >> index & 1 for index in range(0, 6)])

	def pack_permission(self, unpacked: List[int]) -> int:
		"""Packs permissions from an ordered list of binary switches to an integer for storage in memory/object

		Args:
			unpacked (List[int]): list of binary switched that were modified

		Returns:
			int: permission stored as an integer in the object and db
		"""
		packed = 0
		for index, each in enumerate(unpacked):
			packed |= each << index
		return packed

	def get_permissions(self) -> Tuple[UserPermission]:
		"""Get searchable permissions tuple

		Returns:
			Tuple[UserPermission]: Tuple that can be checked with `UserPermission(5) in user.get_permission()` to discern if user has given permission
		"""
		output = []
		for index, each in enumerate(self.permission):
			if each:
				output.append(UserPermission(index))
		if output.__len__() == 0:
			output.append(UserPermission(0))
		return tuple(output)

	def permit(self, *permission:  UserPermission):
		"""Turn on permissions

		Args:
			permission (UserPermission | Tuple[UserPermission]): Single UserPermission to enable, or tuple of several
		"""
		if UserPermission.NOPERMISSION in permission:
			self.revoke_all()
			return

		new_permission = self.permission
		for each in permission:
			new_permission[each.value] = 1

		self._save_permission(new_permission)


	def revoke(self, *permission: UserPermission):
		"""Turn off permissions

		Args:
			permission (UserPermission | Tuple[UserPermission]): Single UserPermission to disable, or tuple of several
		"""
		new_permission = self.permission
		for each in permission:
			new_permission[each.value] = 0

		self._save_permission(new_permission)

	def revoke_all(self):
		"""Turn off all permissions
		"""
		permission = [0 for _ in range(len(self.permission))]
		self._save_permission(permission)


	def _save_permission(self, permission: list):
		"""Save permission to database
		"""
		self.update("permission", self.pack_permission(permission))




	def check_pass(self, password: str) -> bool:
		"""Check credentials

		Args:
			password (str): Password as plaintext

		Returns:
			bool: Was password valid?
		"""
		salted_new_password = self.salt_password(password)
		return compare_digest(self.password, salted_new_password)

	def check_token(self, token):
		"""match cookie token (hex str) with db["token"] (digest binary)
		"""
		return compare_digest_hex(digest=self.token, hex=token)
	

class User_handler:
	def __init__(self):
		self.user_db = PickleTable()

		self.cached = LimitedDict({}, max=500)

		self.common_salt = "0123456789"

		self.admins = []

	def set_common_salt(self, sys_Pass):
		self.common_salt = hashlib.md5(sys_Pass).hexdigest()

	def load_db(self, db_path=""):
		self.user_db = PickleTable(db_path)
		self.user_db.add_column("username",
			"password",
			"created_at",
			"last_active",
			"id",
			"token",
			"permission",

			exist_ok=True)


	def create_user(self, username, password, is_admin=False):
		p_hash = token = None
		uid = hashlib.sha1((str(time.time()) + username).encode("utf-8")).hexdigest()

		u_data = {
			"username": username,
			"password": p_hash,
			"created_at": round(datetime.datetime.now(datetime.timezone.utc).timestamp(),2),
			"last_active": round(datetime.datetime.now(datetime.timezone.utc).timestamp(),2), # datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),

			"id": uid, #
			"token": token,

			"permission": 0,
		}

		row = self.user_db.add_row(u_data)

		user = User(row=row)
		user.set_password(password)
		self.assign_handler(user)

		if is_admin:
			self.set_admin(user)

		return user
	
	def assign_handler(self, user:User):
		# assign user handler to user
		# so that if multiple user handlers are created, the user can always find the correct parent
		user.user_handler = self

	def set_admin(self, user:User):
		# add user to admin list
		if user not in self.admins:
			self.admins.append(user)
	
	def create_guest(self):
		user = self.create_user("Guest", "Guest")

	def _user(self, username=None, user=None):
		if not user:
			user = self.get_user(username)

		if not user:
			raise LookupError("User not found")
		return user

	def server_signup(self, username, password):
		# check if username is already taken
		if self.get_user(username, temp=True) is not None:
			return {
				"status": "error",
				"message": "Username already taken"
			}

		# create user
		user = self.create_user(username, password)
		return {
			"status": "success",
			"message": "User created",
			"user_name": user.username,
			"token": user.token
		}

	def server_login(self, username, password):
		user = self.get_user(username)
		if user is None:
			return {
				"status": "error",
				"message": "User not found"
			}

		if not user.check_pass(password):
			return {
				"status": "error",
				"message": "Wrong password"
			}

		user.update("last_active", round(datetime.datetime.now(datetime.timezone.utc).timestamp(),2))
		print("logged in", user)
		# user.flags.clear() # clear flags

		return {
			"status": "success",
			"message": "User logged in",
			"user_name": username,
			"user_id": user["id"]
		}

	def get_user(self, username, temp=False):
		user = self.cached.get(username)
		if user:
			return user


		user_cell = self.user_db.find_1st(kw=username, column="username", return_obj=True)

		if not user_cell:
			return None

		user_row = user_cell.row_obj()

		user = User(row=user_row)
		self.assign_handler(user)

		if not temp:
			self.cached[username] = user

		return user

	def server_verify(self, username:str, token:str, return_user=False):
		user = self.get_user(username)
		if not user:
			return False
		if user.check_token(token):
			return False

		user["last_active"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

		if return_user:
			return user
		return True


user_handler = User_handler()




def test():
	user_handler.load_db()
	z = user_handler.server_signup(username="Admin", password="pass")
	print(z)



	u = user_handler.get_user("Admin")
	if u is None:
		print("User not found")
		return

	print(u)
	print(u.username)
	print(u.db)
	print(u.permission)
	u.permit(permits.DOWNLOAD, permits.DELETE)
	print(u.permission)
	print(u.permission.NOPERMISSION)
	print(u.permission.DOWNLOAD)
	print(u.get_permissions())

if __name__ == "__main__":
	test()

