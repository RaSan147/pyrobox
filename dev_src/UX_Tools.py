from collections.abc import Callable
from typing import Union
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from queue import Queue
from typing import Generator, List, Union

from pathlib import Path
from importlib import import_module
import importlib.util

import sys
import subprocess
import ctypes


def import_loop(
	packages: list,
	export: Union[str, list, tuple] = None,
	action: Callable = None,
	fallback: Callable = None
):
	"""
	Try importing across a list of package names until one succeeds.
	- `export`: Attribute name (str) or list/tuple of candidate attribute names to extract from the module.
	- `action`: Callable (e.g. lambda / function) to perform on the imported module (or on the exported item if export is provided).
	- `fallback`: Callable to execute if all package candidates fail.
	"""
	for package in packages:
		try:
			mod = import_module(package)
			target = mod
			if export is not None:
				if isinstance(export, str):
					target = getattr(mod, export)
				elif isinstance(export, (list, tuple)):
					found = False
					for attr in export:
						if hasattr(mod, attr):
							target = getattr(mod, attr)
							found = True
							break
					if not found:
						raise AttributeError(f"None of {export} found in {package}")

			if callable(action):
				return action(target)
			return target
		except (ImportError, AttributeError):
			continue

	if callable(fallback):
		return fallback()
	return None


class OptionalDepManager:
	"""Declarative loader for optional runtime packages.

	Each entry is registered once; ``load(announce=...)`` probes/imports and
	toggles a shared ``disabled`` mapping. Missing deps can be announced via
	``on_missing`` (e.g. styled ``xprint``).
	"""

	def __init__(self, disabled=None, on_missing=None):
		self.disabled = disabled if disabled is not None else {}
		self.on_missing = on_missing
		self._specs = []
		self._exports = {}
		self._loaded = set()
		self._missing = {}
		self._announced = set()

	def add(
		self,
		key,
		package=None,
		*,
		exports=None,
		fallbacks=None,
		probe_only=False,
		pip_name=None,
		missing="feature disabled",
	):
		"""Register one optional dependency.

		Parameters
		----------
		key :
			Flag name stored in ``disabled`` (and default export name for the module).
		package :
			Import name (defaults to ``key``).
		exports :
			Optional ``str`` / sequence of attribute names to pull from the module,
			or a ``dict`` mapping ``{local_name: attr_name}``.
		fallbacks :
			Optional ``dict`` of ``{local_name: value}`` installed when import fails
			(e.g. exception types used in ``except`` clauses).
		probe_only :
			If True, only check that the package is importable (no exports stored).
		pip_name :
			Name shown in ``pip install ...`` hints (defaults to ``package``).
		missing :
			Short reason shown when the package is unavailable.
		"""
		self._specs.append({
			"key": key,
			"package": package or key,
			"exports": exports,
			"fallbacks": fallbacks or {},
			"probe_only": probe_only,
			"pip_name": pip_name or package or key,
			"missing": missing,
		})
		self.disabled.setdefault(key, False)
		return self

	def get(self, name, default=None):
		return self._exports.get(name, default)

	def __getattr__(self, name):
		try:
			return self._exports[name]
		except KeyError:
			raise AttributeError(
				f"{type(self).__name__!r} has no export {name!r}"
			) from None

	def available(self, key):
		return not self.disabled.get(key, False)

	def load(self, announce=False):
		"""Probe/import every registered dep. Safe to call multiple times."""
		for spec in self._specs:
			self._load_one(spec)
		if announce:
			self.announce_missing()
		return self

	def announce_missing(self):
		"""Emit warnings for deps that failed to load (once each)."""
		if not callable(self.on_missing):
			return
		for key, spec in self._missing.items():
			if key in self._announced:
				continue
			self.on_missing(
				key,
				pip_name=spec["pip_name"],
				missing=spec["missing"],
			)
			self._announced.add(key)

	def _store_exports(self, key, mod, exports):
		if exports is None:
			self._exports[key] = mod
		elif isinstance(exports, dict):
			for local_name, attr in exports.items():
				self._exports[local_name] = getattr(mod, attr)
		elif isinstance(exports, str):
			self._exports[exports] = getattr(mod, exports)
		else:
			for attr in exports:
				self._exports[attr] = getattr(mod, attr)

	def _load_one(self, spec):
		key = spec["key"]
		if key in self._loaded or key in self._missing:
			return

		# Honor a flag already set by the host before load().
		if self.disabled.get(key):
			self._missing[key] = spec
			self._exports.update(spec.get("fallbacks") or {})
			return

		package = spec["package"]
		try:
			if spec["probe_only"]:
				if importlib.util.find_spec(package) is None:
					raise ImportError(package)
			else:
				mod = import_module(package)
				self._store_exports(key, mod, spec["exports"])
			self._loaded.add(key)
		except (ImportError, AttributeError, ModuleNotFoundError):
			self.disabled[key] = True
			self._missing[key] = spec
			self._exports.update(spec.get("fallbacks") or {})


def get_gpu_names():
	gpus = set()

	if sys.platform.startswith('win'):
		from ctypes import wintypes

		class DISPLAY_DEVICEW(ctypes.Structure):
			_fields_ = [
				("cb", wintypes.DWORD),
				("DeviceName", ctypes.c_wchar * 32),
				("DeviceString", ctypes.c_wchar * 128),
				("StateFlags", wintypes.DWORD),
				("DeviceID", ctypes.c_wchar * 128),
				("DeviceKey", ctypes.c_wchar * 128)
			]

		user32 = ctypes.windll.user32
		disp_dev = DISPLAY_DEVICEW()
		disp_dev.cb = ctypes.sizeof(DISPLAY_DEVICEW)
		
		dev_num = 0
		while user32.EnumDisplayDevicesW(None, dev_num, ctypes.byref(disp_dev), 0):
			gpu_name = disp_dev.DeviceString
			if gpu_name:
				gpus.add(gpu_name.lower())
			dev_num += 1

	elif sys.platform.startswith('linux'):
		try:
			# lspci lists all PCI devices. We filter for VGA (graphics) or 3D controllers.
			output = subprocess.check_output(['lspci'], text=True)
			for line in output.splitlines():
				if 'VGA compatible controller' in line or '3D controller' in line:
					# Output looks like: "01:00.0 VGA compatible controller: NVIDIA Corporation GA106 [GeForce RTX 3060]"
					# We split by ':' and take the last part.
					gpu_name = line.split(':')[-1].strip()
					gpus.add(gpu_name.lower())
		except (FileNotFoundError, subprocess.SubprocessError):
			pass

	elif sys.platform.startswith('darwin'):
		gpus.add("videotoolbox")

	return list(gpus)


def get_codec():
	"""
	Detects the available video codec hardware on the current system and returns the appropriate FFmpeg codec string.

	Returns:
		str: The recommended FFmpeg codec based on detected GPU hardware:
			- "h264_nvenc" for NVIDIA GPUs (Windows/Linux)
			- "h264_qsv" for Intel GPUs
			- "h264_amf" for AMD/Radeon GPUs
			- "videotoolbox" for macOS
			- "libx264" as a fallback if no hardware acceleration is detected

	Notes:
		- On Windows, uses WMIC to detect the video controller.
		- On Linux, checks for NVIDIA GPUs using `nvidia-smi`, otherwise parses `lspci` output.
		- On macOS, returns "videotoolbox" directly.
		- Requires `subprocess` and `sys` modules.
	"""
	def is_in(gpu:str, gpu_list:list):
		return any(gpu.lower() in keyword.lower() for keyword in gpu_list)

	gpus = get_gpu_names()
	if is_in("nvidia", gpus):
		return "h264_nvenc"
	elif is_in("intel", gpus):
		return "h264_qsv"
	elif is_in("amd", gpus) or is_in("radeon", gpus):
		return "h264_amf"
	
	return "libx264"


exe_location_cache = {}


def read_str_file(file_path):  # Function to load a text file
	with open(file_path, 'r', encoding='utf-8') as file:
		context = file.read()
	return context


def read_json_file(file_path):
	with open(file_path, "r", encoding="utf-8") as file:
		json_data = json.load(file)
	return json_data


def save_json_file(file_path, data_dict):
	with open(file_path, "w", encoding="utf-8") as f:
		json.dump(data_dict, f, indent=4, ensure_ascii=False)


def get_exe_location(executable='ffmpeg'):
	"""
	Returns the path to the specified executable if it exists in the system's PATH.

	Args:
		executable (str): The name of the executable to search for. Defaults to 'ffmpeg'.

	Returns:
		str or None: The full path to the executable if found, otherwise None.
	"""
	return shutil.which(executable)


def set_terminal_title(title):
	"""
	Sets the terminal or console window title.

	On Windows, uses the Windows API to set the console title.
	On other platforms, sends the appropriate escape sequence to set the terminal title.

	Args:
		title (str): The title to set for the terminal or console window.

	Raises:
		AttributeError: If the required Windows API function is not available.
		Exception: If writing to sys.stdout fails on non-Windows platforms.
	"""
	if sys.platform.startswith('win'):
		ctypes.windll.kernel32.SetConsoleTitleW(title)
	else:
		sys.stdout.write(f"\x1b]2;{title}\x07")


def open_explorar(path):
	"""
	Opens the given file or directory path in the system's default file explorer.

	Args:
		path (str): The file or directory path to open.

	Raises:
		OSError: If the operation fails due to an invalid path or unsupported platform.

	Platform Support:
		- Windows: Uses os.startfile to open the path.
		- Linux: Uses 'xdg-open' via subprocess to open the path.
		- macOS: Uses 'open' via subprocess to open the path.
	"""
	path = os.path.realpath(path)
	if sys.platform.startswith('win'):
		os.startfile(path)
	elif sys.platform.startswith('linux'):
		subprocess.Popen(["xdg-open", path])
	elif sys.platform.startswith('darwin'):
		subprocess.Popen(["open", path])


def xpath(*path: Union[str, bytes], realpath: bool = False, posix: bool = True) -> str:
	"""
	Joins multiple path components and normalizes the resulting path.

	Args:
		*path (Union[str, bytes]): One or more path components to join. Each component can be a string or bytes.
		realpath (bool, optional): If True, returns the absolute, normalized path with symbolic links resolved. Defaults to False.
		posix (bool, optional): If True, uses POSIX-style (forward slash) separators in the output path. If False, uses the system's default separator (e.g., backslash on Windows). Defaults to True.

	Returns:
		str: The joined and normalized path as a string or bytes, matching the type of the first path component.

	Notes:
		- If any path component is bytes, the result will be bytes; otherwise, it will be a string.
		- When `posix` is True, all separators are converted to forward slashes and redundant slashes are collapsed.
		- When `posix` is False, all separators are converted to the system default and redundant separators are collapsed.
	"""

	is_bytes = isinstance(path[0], bytes)  # detect if path is bytes

	# Convert all path components to strings
	str_paths = [p.decode() if isinstance(p, bytes) else str(p) for p in path]

	# Join and normalize path
	joined_path = os.path.join(*str_paths)

	if posix:
		# Convert to posix style
		joined_path = joined_path.replace("\\", "/")
		joined_path = re.sub(r"/+", "/", joined_path)
	else:
		# Convert to Windows style
		joined_path = joined_path.replace("/", "\\")
		joined_path = re.sub(r"[\\]+", r"\\", joined_path)

	out_path = os.path.realpath(joined_path) if realpath else joined_path
	return out_path


def EXT(path):
	"""
	Extracts and returns the file extension from a given file path.
	
	Examples:
		- EXT("example.txt") returns "txt"
		- EXT("archive.tar.gz") returns "gz"
		- EXT("no_extension") returns "no_extension"

	Parameters:
		path (str): The file path from which to extract the extension.

	Returns:
		str: The file extension (the substring after the last period). If there is no period in the path, returns the entire path.
	"""

	return path.rsplit('.', 1)[-1]


def file_exists(folder_path, filename):
	"""
	Check if a file exists in the specified folder.

	Args:
		folder_path (str): The path to the folder where the file is expected to be found.
		filename (str): The name of the file to check for existence.

	Returns:
		bool: True if the file exists in the specified folder, False otherwise.
	"""
	return os.path.isfile(os.path.join(folder_path, filename))


def remove_new_lines(txt):
	"""
	Replaces all newline characters in the input string with the literal string '\n'.

	This function temporarily replaces all occurrences of the literal string '\n' with a placeholder,
	removes all actual newline characters, and then restores the literal '\n' strings.

	Args:
		txt (str): The input string to process.

	Returns:
		str: The processed string with all newline characters removed and literal '\n' preserved.
	"""
	return txt.replace("\\n", '\0').replace("\n", "").replace("\0", "\\n")


def make_dir(*path, return_path_type=False):
	"""
	Creates a directory at the specified path if it does not already exist.
	Parameters:
		*path: str
			One or more path components to be joined into a single directory path.
	Returns:
		str: The full path of the created (or already existing) directory.
	Notes:
		- The function uses `xpath` to join the path components.
		- If the directory already exists, no exception is raised.
	"""
	
	path = xpath(*path)
	os.makedirs(path, exist_ok=True)

	if return_path_type:
		return Path(path)

	return path


def os_scan_walk_gen(*path, allow_dir=False) -> Generator[os.DirEntry, None, None]:
	"""
	Generator function to recursively scan directories and yield directory entries.

	Args:
		*path: One or more path components to join and use as the starting directory.
		allow_dir (bool, optional): If True, yields both files and directories. If False (default), yields only files.

	Yields:
		os.DirEntry: An entry object corresponding to a file or directory found during the scan.

	Raises:
		OSError: If a directory cannot be accessed, it is skipped.

	Notes:
		- Symbolic links are not followed when determining if an entry is a directory.
		- The function uses a queue to perform a breadth-first traversal of the directory tree.
	"""
	Q = Queue()
	Q.put(xpath(*path))
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)

			if allow_dir or not is_dir:

				yield entry

		dir.close()


def os_scan_walk(*path, allow_dir=False) -> List[os.DirEntry]:
	"""
	Recursively iterates through a directory and its subdirectories, returning a list of os.DirEntry objects for each file and, optionally, each directory.

	Args:
		*path: str
			Path(s) to the directory to scan.
		allow_dir: bool, optional
			If True, include directories in the returned list. Defaults to False.

	Returns:
		List[os.DirEntry]: 
			A list of os.DirEntry objects representing files (and optionally directories) found in the directory tree.
	"""

	files = []

	for entry in os_scan_walk_gen(*path, allow_dir=allow_dir):
		files.append(entry)

	return files


def is_file(*path):
	"""
	Checks if the given path points to an existing file.

	Args:
		*path: One or more path components to be joined and checked.

	Returns:
		bool: True if the constructed path points to an existing file, False otherwise.
	"""
	return os.path.isfile(xpath(*path))


def is_filetype(*path, ext_type=None):
	"""
	Checks if the file at the given path matches the specified file type.

	Args:
		*path: One or more path components that are joined to form the file path.
		ext_type (str): The expected file type category (e.g., 'image', 'video', 'audio', etc.).

	Returns:
		bool: True if the file's MIME type matches the specified type, False otherwise.

	Prints:
		The file path and its detected MIME type for debugging purposes.
	"""
	if ext_type is None:
		ext_type = path[-1]
		path = path[:-1]

	path = xpath(*path)
	mime = mimetypes.guess_type(path)[0]
	return mime and mime.split('/')[0] == ext_type


class Text_Box:
	"""
	A utility class for displaying text within a styled border in the terminal.

	Attributes:
		styles (dict): A dictionary mapping style names to their corresponding border characters.

	Methods:
		box(*text, style="equal"):
			Returns a string with the provided text centered and surrounded by a border of the specified style.

		print_box(*text, style="equal"):
			Prints the provided text centered and surrounded by a border of the specified style.
	"""
	def __init__(self):
		self.styles = {
			"equal": "=",
			"star": "*",
			"hash": "#",
			"dash": "-",
			"udash": "_"
		}

	def box(self, *text, style="equal"):
		"""
		Creates a bordered box around the provided text, centered according to the terminal width.

		Args:
			*text: Variable length argument list of strings or values to be included inside the box.
			style (str, optional): The border style to use. Defaults to "equal". If the style is not found in self.styles, the provided style string is used directly.

		Returns:
			str: The formatted string with the text centered and surrounded by a border.

		Notes:
			- The border width matches the current terminal width.
			- Each line of the input text is centered within the box.
			- The border is repeated above and below the text.
		"""
		text = " ".join(map(str, text))
		term_col = shutil.get_terminal_size()[0]

		s = self.styles[style] if style in self.styles else style
		tt = ""
		for i in text.split('\n'):
			tt += i.center(term_col) + '\n'
		return f"\n\n{s*term_col}\n{tt}{s*term_col}\n\n"

	def print_box(self, *text, style="equal"):
		"""
		Prints one or more strings with a border around them.

		Args:
			*text: One or more strings to be printed inside the box.
			style (str, optional): The style of the border. Defaults to "equal".

		Returns:
			None
		"""
		print(self.box(*text, style=style))


text_box = Text_Box()


def ease_in_out(t, duration, ease_in_time, ease_out_time):
	if t < 0:
		return 0
	if t > duration:
		return 1

	ease_in_end = ease_in_time
	ease_out_start = duration - ease_out_time

	if t < ease_in_end:
		# Ease-in phase (quadratic)
		normalized_time = t / ease_in_time
		return normalized_time ** 2
	elif t < ease_out_start:
		# Linear phase
		return (t - ease_in_end) / (ease_out_start - ease_in_end)
	else:
		# Ease-out phase (quadratic)
		normalized_time = (t - ease_out_start) / ease_out_time
		return 1 - (1 - normalized_time) ** 2


def str_comma(x):
	"""
	Simply swaps dots and commas in a string (or converts number to string first).
	Examples:
		"1.23" → "1,23"
		"1,23" → "1.23"
		4.56 → "4,56"
	"""
	_PyroTCell = import_loop(["pyroDB3", "pyroDB2", "pyroDB"], export="_PyroTCell")
	if _PyroTCell and isinstance(x, _PyroTCell):
		x = x.value

	if not isinstance(x, str):
		x = str(x)
	return x.replace('.', '\0').replace(',', '.').replace('\0', ',')


def str_comma_to_float(x):
	"""
	Converts comma-decimal strings to float by swapping commas to dots.
	Examples:
		"1,23" → 1.23
		"1.23" → 1.23 (unchanged)
	"""
	_Cell = import_loop(["pyroDB3", "pyroDB2", "pyroDB"], export=["_PyroTCell", "_PickleTCell"])
	if _Cell and isinstance(x, _Cell):
		x = x.value

	if isinstance(x, (int, float)):
		return float(x)
	return float(str(x).replace('.', '').replace(',', '.'))


# case insensitive dictionary
class CaseInsensitiveDict(dict):
	def __init__(self, *args, **kwargs):
		super(CaseInsensitiveDict, self).__init__(*args, **kwargs)

	def __getitem__(self, key):
		# get all keys and find the one that matches
		for k in self.keys():
			if k.lower() == key.lower():
				return super(CaseInsensitiveDict, self).__getitem__(k)

	def __delitem__(self, key):
		for k in self.keys():
			if k.lower() == key.lower():
				return super(CaseInsensitiveDict, self).__delitem__(k)

	def __contains__(self, key):
		for k in self.keys():
			if k.lower() == key.lower():
				return True
		return False

	def get(self, key, default=None):
		for k in self.keys():
			if k.lower() == key.lower():
				return super(CaseInsensitiveDict, self).get(k, default)
		return default

	def update(self, other):
		super(CaseInsensitiveDict, self).update(CaseInsensitiveDict(other))

	def pop(self, key, default=None):
		for k in self.keys():
			if k.lower() == key.lower():
				return super(CaseInsensitiveDict, self).pop(k, default)
		return default


def _fallback_xprint(*args, sep=' ', end='\n', **kwargs):
	"""
	Prints text with a specific format.
	"""
	blue_term_text = '\033[94m'
	reset_term_text = '\033[0m'

	args = list(args)  # Convert args to a list for modification
	for i, string in enumerate(args):
		if isinstance(string, str):
			# Replace special codes with terminal colors
			string = string.replace('/b/', blue_term_text)
			string = string.replace('/=/', reset_term_text)
			args[i] = string

	print(*args, sep=sep, end=end, **kwargs)


xprint = import_loop(["print_text4"], export="xprint", fallback=lambda: _fallback_xprint)



def lprint(*args, **kwargs):
	"""
	Prints a message prefixed with the file path and line number from where the function is called.

	This function is similar to `print`, but automatically includes the caller's file path and line number
	for easier debugging and tracing. The output format is:
		/b/["<file_path>", line <line_number>]:/=/

	Args:
		*args: Variable length argument list to be printed.
		**kwargs: Arbitrary keyword arguments passed to the built-in `print` function.

	Example:
		- lprint("This is a debug message")
		- Output: /b/["/path/to/file.py", line 42]:/=/ This is a debug message
	"""
	import inspect

	# Get the previous frame in the stack, otherwise it would be this function
	frame = inspect.currentframe().f_back
	# Extract the line number
	line_number = frame.f_lineno
	# Extract the file name
	file_path = frame.f_code.co_filename.replace('\\', '/')
	# file_path = '/'.join(file_path.split('/')[-2:])
	# Print the file name and line number, along with the provided arguments
	xprint(f'/b/["{file_path}", line {line_number}]:/=/ ', end='')
	print(*args, **kwargs)


if __name__ == '__main__':
	import io
	import time
	import traceback
	from functools import wraps

	class SkipTest(Exception):
		pass

	def timed_test(test_func):
		@wraps(test_func)
		def wrapper(*args, **kwargs):
			start_time = time.perf_counter()
			print(f"\n⏱️  Starting {test_func.__name__}...")
			try:
				result = test_func(*args, **kwargs)
				elapsed = time.perf_counter() - start_time
				print(f"✅ {test_func.__name__} completed in {elapsed:.4f}s")
				return result
			except SkipTest as e:
				elapsed = time.perf_counter() - start_time
				print(f"⚠️  {test_func.__name__} skipped ({e}) after {elapsed:.4f}s")
				wrapper._is_skipped = True
				return None
			except Exception as e:
				elapsed = time.perf_counter() - start_time
				print(f"❌ {test_func.__name__} failed after {elapsed:.4f}s")
				raise
		wrapper._is_skipped = False
		return wrapper

	def assert_with_message(condition, message, *extra, message_on_fail=None, message_on_success=None, time_start=None):
		"""Helper for better assertion messages"""
		if time_start is not None:
			time_end = time.perf_counter()
			message = f"{message} (Time taken: {time_end - time_start:.4f}s)"

		if message_on_fail is None or message_on_fail is True:
			message_on_fail = message
		elif message_on_fail is False:
			message_on_fail = ""
		else:
			message_on_fail = f"{message_on_fail} ({message})"

		if message_on_success is None or message_on_success is True:
			message_on_success = message
		elif message_on_success is False:
			message_on_success = ""
		else:
			message_on_success = f"{message_on_success} ({message})"

		if not condition:
			if extra:
				if len(extra) == 1:
					message_on_fail = f"{message_on_fail} ({extra[0]})"
				elif len(extra) == 2:
					message_on_fail = f"{message_on_fail}\n(\n\tExpected: \n{extra[0]}\n\tGot: \n{extra[1]}\n)"
			if message_on_fail:
				raise AssertionError(f"❌ {message_on_fail}")
			else:
				raise AssertionError()

		if message_on_success:
			print(f"  ✓ {message_on_success}")

	def _safe_remove(path):
		if os.path.exists(path):
			if os.path.isdir(path):
				shutil.rmtree(path, ignore_errors=True)
			else:
				try:
					os.remove(path)
				except OSError:
					pass

	@timed_test
	def test_import_loop():
		# 1. Direct module import
		m = import_loop(['json', 'non_existent_module_xyz'])
		assert_with_message(m is json, "Direct module import (json)")

		# 2. Export attribute from module
		dumps_fn = import_loop(['non_existent_module_xyz', 'json'], export='dumps')
		assert_with_message(callable(dumps_fn), "Export attribute (dumps) from module")
		assert_with_message(dumps_fn({'a': 1}) == '{"a": 1}', "Exported dumps function execution")

		# 3. Export candidate list of attributes
		loads_fn = import_loop(['json'], export=['non_existent_func', 'loads'])
		assert_with_message(callable(loads_fn), "Export candidates list attribute resolution")
		assert_with_message(loads_fn('{"a": 1}') == {'a': 1}, "Exported loads function execution")

		# 4. Action lambda on module
		v = import_loop(['sys'], action=lambda mod: mod.version_info[0])
		assert_with_message(v >= 3, "Action callable applied on imported module", ">=3", v)

		# 5. Export + Action combination
		res = import_loop(['json'], export='loads', action=lambda fn: fn('{"num": 100}'))
		assert_with_message(res == {'num': 100}, "Action callable applied on exported attribute", {'num': 100}, res)

		# 6. Fallback when all fail
		fb_res = import_loop(['non_existent_1', 'non_existent_2'], fallback=lambda: "FALLBACK_VALUE")
		assert_with_message(fb_res == "FALLBACK_VALUE", "Fallback triggered when all imports fail")

	@timed_test
	def test_gpu_and_codec():
		gpus = get_gpu_names()
		assert_with_message(isinstance(gpus, list), "get_gpu_names returns list", list, type(gpus))
		codec = get_codec()
		assert_with_message(isinstance(codec, str) and len(codec) > 0, "get_codec returns non-empty string", codec)

	@timed_test
	def test_file_operations():
		test_file = "__ux_test_file.txt"
		test_json = "__ux_test_json.json"
		test_dir = "__ux_test_dir"

		try:
			# Text write & read
			with open(test_file, "w", encoding="utf-8") as f:
				f.write("Line1\nLine2")
			content = read_str_file(test_file)
			assert_with_message(content == "Line1\nLine2", "read_str_file matches content", "Line1\nLine2", content)

			# JSON write & read
			payload = {"name": "test", "items": [1, 2, 3], "flag": True}
			save_json_file(test_json, payload)
			loaded_json = read_json_file(test_json)
			assert_with_message(loaded_json == payload, "save_json_file / read_json_file roundtrip", payload, loaded_json)

			# File existence & type
			assert_with_message(file_exists(".", test_file), "file_exists for created file")
			assert_with_message(not file_exists(".", "__non_existent_file_xyz.tmp"), "file_exists for non-existent file")
			assert_with_message(is_file(test_file), "is_file returns True for file")
			assert_with_message(is_filetype(test_file, ext_type="text"), "is_filetype detects text file")

			# make_dir & scan
			created_dir = make_dir(test_dir, "sub")
			assert_with_message(os.path.isdir(created_dir), "make_dir creates nested directories")

			scanned_dirs = [entry.name for entry in os_scan_walk(test_dir, allow_dir=True)]
			assert_with_message("sub" in scanned_dirs, "os_scan_walk (allow_dir=True) finds created directory")

		finally:
			_safe_remove(test_file)
			_safe_remove(test_json)
			_safe_remove(test_dir)

	@timed_test
	def test_path_and_string_utils():
		# xpath
		p_posix = xpath("folder", "subfolder", "file.txt", posix=True)
		assert_with_message(p_posix == "folder/subfolder/file.txt", "xpath posix style", "folder/subfolder/file.txt", p_posix)

		# EXT
		ext_single = EXT("archive.zip")
		assert_with_message(ext_single == "zip", "EXT single extension", "zip", ext_single)
		ext_multi = EXT("archive.tar.gz")
		assert_with_message(ext_multi == "gz", "EXT extension", "gz", ext_multi)

		# remove_new_lines
		cleaned = remove_new_lines("Line 1\nLine 2\\nLine 3")
		assert_with_message(cleaned == "Line 1Line 2\\nLine 3", "remove_new_lines strips actual newlines while preserving literal \\n", "Line 1Line 2\\nLine 3", cleaned)

	@timed_test
	def test_number_formatting():
		# str_comma
		assert_with_message(str_comma("1.23") == "1,23", "str_comma converts dot to comma", "1,23", str_comma("1.23"))
		assert_with_message(str_comma("1,23") == "1.23", "str_comma converts comma to dot", "1.23", str_comma("1,23"))
		assert_with_message(str_comma(4.56) == "4,56", "str_comma formats float", "4,56", str_comma(4.56))

		# str_comma_to_float
		assert_with_message(str_comma_to_float("1,23") == 1.23, "str_comma_to_float converts comma string to float", 1.23, str_comma_to_float("1,23"))
		assert_with_message(str_comma_to_float("1.234,56") == 1234.56, "str_comma_to_float handles thousands dot", 1234.56, str_comma_to_float("1.234,56"))
		assert_with_message(str_comma_to_float(42.5) == 42.5, "str_comma_to_float preserves existing float", 42.5, str_comma_to_float(42.5))

		# ease_in_out
		assert_with_message(ease_in_out(0, 10, 2, 3) == 0.0, "ease_in_out at start is 0.0")
		assert_with_message(ease_in_out(10, 10, 2, 3) == 1.0, "ease_in_out at end is 1.0")

	@timed_test
	def test_case_insensitive_dict():
		cid = CaseInsensitiveDict({"Name": "Alice", "AGE": 25})
		assert_with_message(cid["name"] == "Alice", "CaseInsensitiveDict get lowercase", "Alice", cid["name"])
		assert_with_message(cid["NAME"] == "Alice", "CaseInsensitiveDict get uppercase", "Alice", cid["NAME"])
		assert_with_message(cid["age"] == 25, "CaseInsensitiveDict get mixed case", 25, cid["age"])
		assert_with_message("name" in cid, "CaseInsensitiveDict membership check")
		assert_with_message("AGE" in cid, "CaseInsensitiveDict uppercase membership check")
		assert_with_message("missing" not in cid, "CaseInsensitiveDict non-existent key check")

		cid["CITY"] = "Wonderland"
		assert_with_message(cid["city"] == "Wonderland", "CaseInsensitiveDict set item case insensitive")

		val = cid.pop("City")
		assert_with_message(val == "Wonderland" and "city" not in cid, "CaseInsensitiveDict pop case insensitive")

	@timed_test
	def test_printing_and_box():
		# Capture output of xprint & Text_Box
		old_stdout = sys.stdout
		sys.stdout = io.StringIO()
		try:
			xprint("Testing /b/blue text/=/")
			text_box.print_box("Box Message", style="star")
			lprint("Line print message")
			out = sys.stdout.getvalue()
		finally:
			sys.stdout = old_stdout

		assert_with_message("blue text" in out, "xprint formats correctly")
		assert_with_message("Box Message" in out, "text_box prints content")
		assert_with_message("line " in out, "lprint outputs line marker")

	def run_all_tests():
		"""Run all test cases with timing and proper cleanup, mirroring pyroDB3 test runner"""
		tests = [
			test_import_loop,
			test_gpu_and_codec,
			test_file_operations,
			test_path_and_string_utils,
			test_number_formatting,
			test_case_insensitive_dict,
			test_printing_and_box,
		]

		start_time = time.perf_counter()
		failures = 0
		skipped = 0

		print(f"{'='*60}")
		print(f"🚀 Running UX_Tools Test Suite ({len(tests)} test suites)")
		print(f"{'='*60}")

		for test in tests:
			try:
				result = test()
				if result is None and getattr(test, '_is_skipped', False):
					skipped += 1
			except AssertionError as e:
				failures += 1
				print(f"❌ {test.__name__} failed: {str(e)}")
				print('+'*50 + f"\n{traceback.format_exc()}\n" + '-'*50)
			except Exception as e:
				failures += 1
				print(f"❌ {test.__name__} failed (UNHANDLED): {str(e)}")
				print('+'*50 + f"\n{traceback.format_exc()}\n" + '-'*50)

		total_time = time.perf_counter() - start_time
		print(f"\n{'='*60}")
		skip_str = f", {skipped} skipped" if skipped else ""
		print(f"⏱️  Test Summary: {len(tests)} test suites, {failures} failures{skip_str}")
		print(f"⏱️  Total execution time: {total_time:.4f} seconds")
		print(f"{'='*60}")

		if failures > 0:
			raise SystemExit(1)

	run_all_tests()