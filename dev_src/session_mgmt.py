from platform import uname as platformuname
import os
import pickledb
# from pyroboxCore import logger    TODO: use logger without circular import
from typing import List, Union
from zlib import adler32 as _adler32



def adler32(plain_text) -> str:
    """Adler32 hash algorithm

    Args:
        plain_text (str): Input to be hashed

    Returns:
        str: Numerical hash as a string
    """

    return str(_adler32(str(plain_text).encode()))



class MachineSession():

    def __init__(self, path: Union [str , os.PathLike], name: Union [str , None] = None, main_dir: Union[str , os.PathLike] = "."):
        """Initialise a session for use in Config

        Args:
            path (str | os.PathLike): path where the files are served from
            name (str | None, optional): name of session if provided by user. Defaults to None.
            main_dir (str | os.PathLike, optional): current directory to place db file. Defaults to ".".

        Raises:
            NameError: Already a session serving that path, the other session should be used instead.
        """
        self.path = path

        try:
            os.makedirs(os.path.join(main_dir, "session_db") , exist_ok=True)
        except PermissionError:
            raise PermissionError('Permission denied to create session_db folder. Please run as administrator. Or install pyroboox using "pip install --user pyrobox"')

        self.__main_dir__ = main_dir
        self.id = adler32(str(platformuname())+ path)
        self.db_path = os.path.join(main_dir, "session_db", f"s_{self.id}.db")
        self.name = name
        self.user_db: pickledb.PickleDB = pickledb.load(
            os.path.join(self.db_path), True
        )

    def destroy(self):
        os.remove(self.db_path)

    delete = destroy


