# import pickledb
import hashlib
import time, datetime
import secrets
from secrets import compare_digest
from enum import Enum
from typing import Tuple, List, TypeVar, Union, TYPE_CHECKING
import posixpath
from urllib.parse import unquote
import json
import re

VALID_USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_.-]{3,32}$')


def is_valid_username(username: str) -> bool:
	if not username or not isinstance(username, str):
		return False
	return bool(VALID_USERNAME_REGEX.match(username))


if TYPE_CHECKING:
	from pyrobox_ServerHost import ServerHost as SH


def normalize(p: str) -> str:
	p = unquote(p)                    # %2e%2e -> ..
	p = p.replace("\\", "/")          # windows
	if not p.startswith("/"):
		p = "/" + p
	p = posixpath.normpath(p)         # resolves .. and //
	# Windows posixpath can leave a leading '//' (UNC-style); URL ACLs are not UNC
	if p.startswith("//"):
		p = "/" + p.lstrip("/")
	return p.rstrip("/") or "/"


from http.cookies import SimpleCookie
import binascii

from pyroboxCore import logger
from pyroDB4 import PickleTable
from data_types import LimitedDict


def hash_password(password: str) -> bytes:
	"""Hash password with per-user salt using scrypt (or PBKDF2-HMAC fallback)."""
	salt = secrets.token_bytes(16)
	salt_hex = binascii.hexlify(salt).decode("ascii")
	try:
		key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
		key_hex = binascii.hexlify(key).decode("ascii")
		return f"scrypt$16384$8$1${salt_hex}${key_hex}".encode("ascii")
	except (AttributeError, ValueError):
		key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
		key_hex = binascii.hexlify(key).decode("ascii")
		return f"pbkdf2$100000$sha256${salt_hex}${key_hex}".encode("ascii")


def verify_password(stored: Union[bytes, str, None], password: str, common_salt: str = "0123456789") -> Tuple[bool, bool]:
	"""
	Verify password against stored hash.
	Returns: (is_valid: bool, needs_rehash: bool)
	"""
	if not stored or not password:
		return False, False

	if isinstance(stored, str):
		stored = stored.encode("ascii", errors="ignore")

	if stored.startswith(b"scrypt$"):
		try:
			parts = stored.split(b"$")
			n = int(parts[1])
			r = int(parts[2])
			p = int(parts[3])
			salt = binascii.unhexlify(parts[4])
			expected_key = binascii.unhexlify(parts[5])
			computed_key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p)
			return compare_digest(computed_key, expected_key), False
		except Exception:
			return False, False

	if stored.startswith(b"pbkdf2$"):
		try:
			parts = stored.split(b"$")
			iterations = int(parts[1])
			hash_name = parts[2].decode("ascii")
			salt = binascii.unhexlify(parts[3])
			expected_key = binascii.unhexlify(parts[4])
			computed_key = hashlib.pbkdf2_hmac(hash_name, password.encode("utf-8"), salt, iterations)
			return compare_digest(computed_key, expected_key), False
		except Exception:
			return False, False

	# Legacy single-round SHA-256 fallback (needs rehash)
	legacy_hash = hashlib.sha256((common_salt + password).encode("utf-8")).digest()
	if compare_digest(stored, legacy_hash):
		return True, True

	return False, False

# Loads user database. Passwords are hashed with User_handler.common_salt.


__all__ = [
	"User",
	"UserPermission",
	"permits",
	"create_user_cookie",
	"clear_user_cookie",
	"is_valid_username"
]



def compare_digest_hex(digest, hex_data):
	return compare_digest(hex_data.encode("ascii"), binascii.hexlify(digest))






class UserPermission(Enum):
	"""Enum for WebUI user permissions, inspired by Unix permission style

	Args:
		Enum (int): Permission code for user
	"""

	NOPERMISSION = -1
	VIEW = 0        # view file list
	DOWNLOAD = 1    # download files
	MODIFY = 2      # rename, overwrite, new folder
	DELETE = 3      # delete files
	UPLOAD = 4      # upload files
	ZIP = 5         # download zip folder
	ADMIN = 6       # admin
	MEMBER = 7      # member or guest

TOTAL_PERMISSIONS = max([each.value for each in UserPermission]) + 1

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
			ADMIN = 6,      # admin
			MEMBER = 7,     # member or guest
		)
		if name in options:
			return bool(self[options[name]])

		if name == "NOPERMISSION":
			return not any(self)


class User:
	"""Object for WebUI users"""
	def __init__(self, row=None):
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


		self.db = {} if row is None else row
		self.user_handler = User_handler() # type: User_handler




	Self = TypeVar("Self")
	# self reference for use in classmethods that can't strong type User because it's inside the method

	def __getattr__(self, name):
		if hasattr(UserPermission, name):
			return self.check_permission(getattr(UserPermission, name))

	@property
	def username(self) -> str:
		return self.db["username"]

	@property
	def permission_pack(self) -> int:
		return self.db["permission"]

	@property
	def password(self) -> bytes:
		return self.db["password"]

	@property
	def token(self) -> bytes:
		return self.db["token"]

	@property
	def uid(self) -> str:
		return self.db["id"]

	@property
	def token_hex(self) -> str:
		return binascii.hexlify(self.token).decode("ascii")

	@property
	def permission(self) -> PermissionList:
		return self.unpack_permission(self.permission_pack)

	@property
	def allowed_paths(self) -> list:
		paths = self.db.get("allowed_paths", [])
		if isinstance(paths, str):
			try:
				paths = json.loads(paths)
			except Exception:
				paths = []
		return paths

	def set_allowed_paths(self, paths: list):
		self.update("allowed_paths", paths)

	def is_path_allowed(self, path: str) -> bool:
		allowed = self.allowed_paths
		if not allowed:                      # empty = unrestricted
			return True

		path = normalize(path)

		longest_match_len = -1
		longest_match_type = None
		has_allow_child = False

		for entry in allowed:
			if not isinstance(entry, dict):
				continue
				
			r_path = normalize(entry.get("path", ""))
			r_subdirs = entry.get("subdirs", True)
			r_type = entry.get("type", "allow").lower()
			
			r_len = len(r_path)

			# 1. Exact match
			if path == r_path:
				if r_len > longest_match_len:
					longest_match_len = r_len
					longest_match_type = r_type
					
			# 2. Path is inside the rule path (rule path is a parent)
			elif path.startswith(r_path + "/"):
				if r_subdirs:
					if r_len > longest_match_len:
						longest_match_len = r_len
						longest_match_type = r_type
				else:
					# If subdirs is False, allow files directly inside, but no deeper directories
					if path[len(r_path)+1:].find("/") == -1: 
						if r_len > longest_match_len:
							longest_match_len = r_len
							longest_match_type = r_type
							
			# 3. Path is an ancestor of the rule path (we are walking down the tree)
			elif r_path.startswith(path + "/") or path == "/":
				if r_type == "allow":
					has_allow_child = True

		# Follow the most specific rule if there is one
		if longest_match_type is not None:
			return longest_match_type == "allow"
			
		# If no direct match, but it's an ancestor of an allowed path, allow it so the user can navigate down
		if has_allow_child:
			return True

		return False


	def is_admin(self) -> bool:
		return self.ADMIN

	def is_guest(self) -> bool:
		return self.username == "Guest" or not bool(self.MEMBER)

	# get the sha1 hash of the CLI password to use as a salt, makes a longer string and avoids holding secrets in memory

	def salt_password(self, password) -> bytes:
		return hashlib.sha256((self.user_handler.common_salt+password).encode('utf-8')).digest()

	def generate_new_token(self) -> str:
		"""Generate and store a new cryptographically secure session token."""
		token = secrets.token_bytes(32)
		self.update("token", token)
		return self.token_hex

	def set_password(self, password:str) -> None:
		# salt, hash and store password
		p_hash = hash_password(password)
		self.update("password", p_hash)
		self.generate_new_token()



	def reset_pw(self, old_password: str, new_password: str) -> bool:
		"""Reset password

		Args:
			old_password (str): Old plaintext password for confirmation before change
			new_password (str): New plaintext password to be saved

		Returns:
			int: True if old_password accepted, else False
		"""


		if self.check_password(old_password):
			logger.info(f"Updating password of user {self.username}")
			self.update("password", hash_password(new_password))
			self.generate_new_token()
			return True
		else:
			logger.info(f"User {self.username} password mismatch")
			return False

	def create_cookie(self) -> SimpleCookie:
		"""Create a SimpleCookie with user credentials valid for 1 year"""
		return create_user_cookie(self)

	def __setitem__(self, attr, value):
		self.update(attr, value)

	def __getitem__(self, attr):
		return self.db[attr]

	def __bool__(self):
		return bool(self.username)

	def __str__(self):
		return str(self.db)

	def update(self, attr, value):
		self.db[attr] = value

	@staticmethod
	def unpack_permission(packed: int) -> List[int]:
		"""Unpacks permission as int -> list of binary/bool switches like [0,1,0,0,1,0,1]

		Args:
			packed (int): permission stored as an integer in the object and db

		Returns:
			List[int]: list of binary switches to be changed [reversed to make correct order]
		"""
		return PermissionList([packed >> index & 1 for index in range(0, TOTAL_PERMISSIONS)])

	@staticmethod
	def pack_permission(unpacked: List[int]) -> int:
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

	@staticmethod
	def pack_permission_from_list(unpacked: List[UserPermission]) -> int:
		"""Packs permissions from an ordered list of UserPermission to an integer for storage in memory/object

		Args:
			unpacked (List[UserPermission]): list of UserPermission that were modified

		Returns:
			int: permission stored as an integer in the object and db
		"""

		packed = 0
		for each in unpacked:
			packed |= 1 << each.value
		return packed

	@staticmethod
	def unpack_permission_to_list(packed: int) -> List[UserPermission]:
		"""Unpacks permission as int -> list of UserPermission like [UserPermission.VIEW, UserPermission.DOWNLOAD, UserPermission.ZIP]

		Args:
			packed (int): permission stored as an integer in the object and db

		Returns:
			List[UserPermission]: list of UserPermission that were modified
		"""
		return [UserPermission(each) for each in range(TOTAL_PERMISSIONS) if packed >> each & 1]

	def set_permission_pack(self, code) -> None:
		self.update("permission", code)

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
			output.append(UserPermission(-1)) # no permission
		return tuple(output)

	def check_permission(self, perm) -> bool:
		if isinstance(perm, list):
			return all([self.check_permission(each) for each in perm])
		return perm in self.get_permissions()


	def permit(self, *permission:  Union[UserPermission,List[UserPermission],Tuple[UserPermission]]):
		"""Turn on permissions

		Args:
			permission (UserPermission,... | Tuple[UserPermission]): Single UserPermission to enable, or tuple of several
		"""
		# if isinstance(permission, (list, tuple)) and len(permission) == 1:
		# 	permission = permission[0]

		if len(permission) == 1 and isinstance(permission[0], (list, tuple)):
			permission = permission[0]

		if UserPermission.NOPERMISSION in permission:
			self.revoke_all()
			return

		new_permission = self.permission

		for each in permission:
			if not hasattr(each, 'value') and not each: 
				continue # default permission may have none or empty at Initialization
			new_permission[each.value] = 1
			# -1 because 0 is no permission
		self._save_permission(new_permission)


	def revoke(self, *permission: Union[UserPermission,List[UserPermission],Tuple[UserPermission]]) -> None:
		"""Turn off permissions

		Args:
			permission (UserPermission | Tuple[UserPermission]): Single UserPermission to disable, or tuple of several
		"""
		if len(permission) == 1 and isinstance(permission[0], (list, tuple)):
			permission = permission[0]

		new_permission = self.permission
		for each in permission:
			new_permission[each.value] = 0

		self._save_permission(new_permission)

	def revoke_all(self) -> None:
		"""Turn off all permissions
		"""
		permission = [0 for _ in range(len(self.permission))]
		self._save_permission(permission)


	def _save_permission(self, permission: list) -> None:
		"""Save permission to database
		"""
		self.update("permission", self.pack_permission(permission))




	def check_password(self, password: str) -> bool:
		"""Check credentials

		Args:
			password (str): Password as plaintext

		Returns:
			bool: Was password valid?
		"""
		common_salt = getattr(getattr(self, "user_handler", None), "common_salt", "0123456789")
		valid, needs_rehash = verify_password(self.password, password, common_salt=common_salt)
		if valid and needs_rehash:
			self.update("password", hash_password(password))
		return valid

	def check_token(self, token) -> bool:
		"""match cookie token (hex str) with db["token"] (digest binary)
		"""
		return compare_digest_hex(digest=self.token, hex_data=token)


class User_handler:
	def __init__(self, init_permissions=None):
		"""
		init_permissions: `dict` of `UserPermission` to be used as default for new users (member, admin, guest) `{"member": [perms,..], ...}`
		"""
		self.user_db = PickleTable()

		self.cached = LimitedDict({}, max=500)

		self.common_salt = "0123456789"

		self.admins:List[User] = []
		self.member_permission = {} if init_permissions is None else init_permissions

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
			"allowed_paths",

			exist_ok=True)


	def create_user(self, username, password, is_admin=False) -> User:
		if not is_valid_username(username):
			raise ValueError(f"Invalid username: {username!r}. Must be 3-32 alphanumeric characters, '.', '-', or '_'.")

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
			"allowed_paths": [],
		}

		row = self.user_db.add_row(u_data)

		user = User(row=row)
		self.assign_handler(user)
		user.set_password(password)

		user.permit(self.member_permission.get("member", []) )
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
		user.revoke_all()
		user.permit(self.member_permission.get("admin", []))
		user.permit(permits.ADMIN)

	def create_guest(self) -> User:
		user = self.create_user("Guest", "Guest")
		if "guest" in self.member_permission:
			user.revoke_all()
			user.permit(self.member_permission["guest"])

		return user

	def create_admin(self, username, password) -> User:
		user = self.create_user(username, password, is_admin=True)
		return user



	def _user(self, username=None, user=None) -> User:
		if not user:
			user = self.get_user(username)

		if not user:
			raise LookupError("User not found")
		return user

	def server_signup(self, username, password) -> dict:
		if not is_valid_username(username):
			return {
				"status": "error",
				"message": "Invalid username format. Must be 3-32 characters (letters, numbers, '.', '-', '_')."
			}

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
			"token": user.token_hex,
		}

	def server_login(self, username, password) -> dict:
		user = self.get_user(username)
		if user is None or not user.check_password(password):
			return {
				"status": "error",
				"message": "Invalid username or password"
			}

		user.update("last_active", round(datetime.datetime.now(datetime.timezone.utc).timestamp(),2))
		# print("logged in", user)
		# user.flags.clear() # clear flags

		return {
			"status": "success",
			"message": "User logged in",
			"user_name": username,
			"user_id": user["id"]
		}

	def get_user(self, username, temp=False) -> User:
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

	def delete_user(self, username) -> bool:
		user = self.get_user(username)
		if user is None:
			return False

		user.db.del_row() # delete from db
		self.cached.pop(username, None) # delete from cache
		return True


	def server_verify(self, username:str, token:str, return_user=False) -> Union[bool, User]:
		user = self.get_user(username)
		if not user:
			return False
		if not user.check_token(token):
			return False

		user["last_active"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

		if return_user:
			return user
		return True

	def authenticate_cookie(self, cookie: Union[SimpleCookie, None]) -> Union[User, None]:
		"""Extract user credentials from cookie and return authenticated User or None"""
		if not cookie:
			return None

		def get(k):
			x = cookie.get(k)
			if x is not None:
				return x.value
			return ""

		username = get("user")
		token = get("token")

		if not (username and token):
			return None

		user = self.get_user(username)
		if user and user.check_token(token):
			return user
		return None

	def authenticate_handler(self, handler: 'SH', allow_guests: bool = True, guest_user: User = None) -> Tuple[Union[User, None], SimpleCookie]:
		"""
		Authenticate request handler using cookies.
		Returns (user, cookie).
		"""
		user = self.authenticate_cookie(handler.cookie)

		if not user and allow_guests and guest_user:
			user = guest_user

		if not user:
			return (None, clear_user_cookie())

		return (user, create_user_cookie(user))


def create_user_cookie(user: User) -> SimpleCookie:
	"""Create a SimpleCookie for the given user"""
	cookie = SimpleCookie()
	cookie["user"] = user.username
	cookie["user"]["expires"] = 365 * 86400
	cookie["user"]["path"] = "/"
	cookie["user"]["samesite"] = "Lax"

	cookie["token"] = user.token_hex
	cookie["token"]["expires"] = 365 * 86400
	cookie["token"]["path"] = "/"
	cookie["token"]["httponly"] = True
	cookie["token"]["samesite"] = "Lax"

	cookie["permissions"] = user.permission_pack
	cookie["permissions"]["expires"] = 365 * 86400
	cookie["permissions"]["path"] = "/"
	cookie["permissions"]["samesite"] = "Lax"

	return cookie


def clear_user_cookie() -> SimpleCookie:
	"""Create a SimpleCookie to clear user credentials"""
	cookie = SimpleCookie()
	for k in ("user", "token", "permissions"):
		cookie[k] = ""
		cookie[k]["expires"] = -1
		cookie[k]["path"] = "/"
		cookie[k]["samesite"] = "Lax"
	cookie["token"]["httponly"] = True
	return cookie







def test():
	user_handler = User_handler()
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
	# u.permit(permits.DOWNLOAD, permits.DELETE, permits.ZIP)
	print(u.permission)
	print(u.permission.NOPERMISSION)
	print(u.permission.DOWNLOAD)
	print(u.get_permissions())
	print(u.NOPERMISSION)
	user_handler.set_admin(u)
	print(u.is_admin())

if __name__ == "__main__":
	test()

