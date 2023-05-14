from platform import uname as platformuname
import os
import pickledb
# from pyroboxCore import logger    TODO: use logger without circular import 
from typing import List


def adler32(plain_text: str) -> str:
    """Adler32 hash algorithm

    Args:
        plain_text (str): Input to be hashed

    Returns:
        str: Numerical hash as a string
    """
    MOD_ADLER = 65521
    a = 1
    b = 0
    for plain_chr in plain_text:
        a = (a + ord(plain_chr)) % MOD_ADLER
        b = (b + a) % MOD_ADLER
    return str((b << 16) | a)


class MachineSession():

    def __init__(self, path: str | os.PathLike, name: str | None = None, main_dir: str | os.PathLike = "."):
        """Initialise a session for use in Config  

        Args:
            path (str | os.PathLike): path where the files are served from
            name (str | None, optional): name of session if provided by user. Defaults to None.
            main_dir (str | os.PathLike, optional): current directory to place db file. Defaults to ".".

        Raises:
            NameError: Already a session serving that path, the other session should be used instead.
        """
        self.path = path
        self.__main_dir__ = main_dir
        self.session_db: pickledb.PickleDB = pickledb.load(
                os.path.join(self.__main_dir__, "users.db"), True
            )
        prospective_id = adler32(str(platformuname()) + path)

        if self.session_db.exists(prospective_id) == False:
            self.id = prospective_id
            self.name = name
            self.user_db: pickledb.PickleDB = pickledb.load(
                os.path.join(self.__main_dir__, f"s_{self.id}.db"), True
            )
            self.session_db.set(self.id, self.name)
        else:
            # logger.warning("Path already in use with another session")
            raise NameError("Path already in use")

    def destroy(self):
        """Remove from current session db
        """
        self.session_db.rem(self.id)
        os.remove(os.path.join(self.__main_dir__, f"s_{self.id}.db"))
