import pickledb
import hashlib
import os
from secrets import compare_digest
from pyroboxCore import config, logger
from enum import Enum
from typing import Tuple, List, Literal, TypeVar

# Loads user database. Database is plaintext but stores passwords as a hash salted by config.PASSWORD

class UserPermission(Enum):
    """Enum for WebUI user permissions, inspired by Unix permission style

    Args:
        Enum (int): Permission code for user
    """

    NOPERMISSION = 0
    READ = 1
    DOWNLOAD = 2
    MODIFY = 3
    DELETE = 4
    UPLOAD = 5
    ZIP = 6


user_db = config.LOCALSESSION.user_db
class User:
    """Object for WebUI users"""
    def __init__(
        self,
        username: str,
        permission: UserPermission | Tuple[UserPermission],
        password: str = None,
    ):
        """Generate Object for WebUI users

        Args:
            username (str): plaintext username
            permission (UserPermission): password as a UserPermission enum
            password (str, optional): plaintext passsword (later to be hashed). Defaults to None.

        Raises:
            ValueError: User failed to create

        Returns:
            User: Object for WebUI users
        """

        # Private function
        def update_pw(self, password: str) -> Literal[0]:
            """Private method to update password, not usable from outside object

            Args:
                password (str): plaintext password to be salted and hashed

            Raises:
                ValueError: Password failed to be applied at database level

            Returns:
                Int: Zero if OK
            """
            # passwords and hashed passwords are not ever assigned to the object
            salted_password = self.get_salt_pw(password)
            logger.info(f"Updating password of user {self.username}")
            user_db.set(self.username, salted_password)
            return 0

        self.username = username
        if user_db.exists(username):
            self.permission = permission
        else:
            if username and permission and password:
                update_pw(self, password)
                self.permission = 0
                self.permit(permission)
            else:
                raise ValueError("No such username")

    Self = TypeVar("Self")
    # self refernce for use in classmethods that can't strong type User because it's inside the method
    common_salt = hashlib.md5(config.PASSWORD.encode()).hexdigest()
    # get the MD5 has of the CLI password to use as a salt, makes a longer string and avoids holding secrets in memory

    def get_salt_pw(self, password: str) -> str:
        """Method to generate salted and hashes password

        Args:
            password (str): plaintext password to be salted

        Returns:
            str: Checksum of password concat'ed to the MD5 hash of config.PASSWORD
        """
        return hashlib.sha256(password.encode() + self.common_salt.encode()).hexdigest()

    def unpack_permission(self, packed: int) -> List[int]:
        """Unpacks permission as int -> list of binary/bool switches like [0,1,0,0,1,0]

        Args:
            packed (int): permission stored as an integer in the object and db

        Returns:
            List[int]: list of binary switches to be changed
        """
        return [packed >> index & 1 for index in range(0, 6)]

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

    @classmethod
    def get_user(cls, username: str) -> Self | bool(False):
        """Lookup User

        Args:
            username (str): username of User

        Returns:
            User | bool(False): Valid User object or False
        """
        if user_db.exists(username) and user_db.exists(username + "__permissions"):
            permission = user_db.get(username + "__permissions")
            return cls(username=username, permission=permission)
        else:
            logger.error(f"User {username} does not exist")
            return False

    def get_permissions(self) -> Tuple[UserPermission]:
        """Get searchable permissions tuple

        Returns:
            Tuple[UserPermission]: Tuple that can be checked with `UserPermission(5) in user.get_permission()` to discern if user has given permission
        """
        output = []
        for index, each in enumerate(self.unpack_permission(self.permission)):
            if each:
                output.append(UserPermission(index))
        if output.__len__() == 0:
            output.append(UserPermission(0))
        return tuple(output)

    def permit(self, permission: UserPermission | Tuple[UserPermission]) -> Literal[0]:
        """Turn on permissions

        Args:
            permission (UserPermission | Tuple[UserPermission]): Single UserPermission to enable, or tuple of several
        """
        standing_permission = self.unpack_permission(self.permission)
        if type(permission) == UserPermission:
            permission = (permission,)
        for each in permission:
            standing_permission[each.value] = 1
        self.permission = self.pack_permission(standing_permission)
        user_db.set(
            self.username + "__permissions", self.pack_permission(standing_permission)
        )
        return 0

    def revoke(self, permission: UserPermission | Tuple[UserPermission]) -> Literal[0]:
        """Turn off permissions

        Args:
            permission (UserPermission | Tuple[UserPermission]): Single UserPermission to disable, or tuple of several
        """
        standing_permission = self.unpack_permission(
            user_db.get(self.username + "__permissions")
        )
        if type(permission) == UserPermission:
            permission = (permission,)
        for each in permission:
            standing_permission[each.value] = 0
        self.permission = self.pack_permission(standing_permission)
        user_db.set(
            self.username + "__permissions", self.pack_permission(standing_permission)
        )
        return 0

    def reset_pw(self, old_password: str, new_password: str) -> int:
        """Reset password

        Args:
            old_password (str): Old plaintext password for confirmation before change
            new_password (str): New plaintext password to be saved

        Returns:
            int: 0 if old_password accepted, else 1
        """
        salted_old_password = self.get_salt_pw(old_password)
        salted_new_password = self.get_salt_pw(new_password)
        if compare_digest(user_db.get(self.username), salted_old_password):
            logger.info(f"Updating password of user {self.username}")
            user_db.set(self.username, salted_new_password)
            return 0
        else:
            logger.info(f"User {self.username} password mismatch")
            return 1

    def check_creds(self, password: str) -> bool:
        """Check credentials

        Args:
            password (str): Password as plaintext

        Returns:
            bool: Was password valid?
        """
        salted_new_password = self.get_salt_pw(password)
        return compare_digest(user_db.get(self.username), salted_new_password)
