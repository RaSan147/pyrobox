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
	if sys.platform.startswith('win'):
		data = subprocess.check_output(
			"wmic path win32_VideoController get name", shell=True).decode().lower()
	elif sys.platform.startswith('linux'):
		try:
			subprocess.run(["nvidia-smi"], capture_output=True, check=True)
			data = "nvidia"
		except (subprocess.CalledProcessError, FileNotFoundError):
			try:
				data = subprocess.check_output(
					"lspci | grep VGA", shell=True).decode().lower()
			except Exception as e:
				data = "none"
	elif sys.platform.startswith('darwin'):
		return "videotoolbox"

	if "nvidia" in data:
		# return "libx265"
		# return "hevc_nvenc"
		return "h264_nvenc"
	elif "intel" in data:
		return "h264_qsv"
	elif "amd" in data or "radeon" in data:
		return "h264_amf"
	else:
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
		import ctypes
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
		Union[str, bytes]: The joined and normalized path as a string or bytes, matching the type of the first path component.

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


def make_dir(*path):
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
	try:
		try:
			from App.pyroDB2 import _PyroTCell
		except ImportError:
			from pyroDB import _PickleTCell
		if isinstance(x, _PyroTCell):
			x = x.value
	except ImportError:
		pass
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
	try:
		try:
			from App.pyroDB2 import _PyroTCell
		except ImportError:
			from pyroDB import _PickleTCell
		if isinstance(x, _PyroTCell):
			x = x.value
	except ImportError:
		pass
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


try:
	from print_text3 import xprint
except ImportError:
	def xprint(*args, sep=' ', end='\n', **kwargs):
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
	# Test get_codec()
	print("\nTesting get_codec():")
	codec = get_codec()
	print(f"Detected codec: {codec} (platform: {sys.platform})")

	# Test file operations
	print("\nTesting file operations:")
	test_file = "UX_Tools_test_file.txt"
	test_json = "UX_Tools_test_json.json"
	test_video = "UX_Tools_test_video.mp4"
	
	# Create test files
	with open(test_file, "w", encoding="utf-8") as f:
		f.write("Hello\nWorld")
	
	test_data = {"key": "value", "num": 123}
	save_json_file(test_json, test_data)
	
	# Test read_str_file
	print("\nread_str_file():")
	print(read_str_file(test_file))
	
	# Test read_json_file
	print("\nread_json_file():")
	print(read_json_file(test_json))
	
	# Test get_exe_location
	print("\nget_exe_location():")
	print("Python executable:", get_exe_location("python"))
	print("FFmpeg executable:", get_exe_location("ffmpeg"))
	
	# Test set_terminal_title
	print("\nset_terminal_title() - should change terminal title")
	set_terminal_title("Utility Functions Test")
	
	# Test xpath
	print("\nxpath():")
	print("Joined path:", xpath("folder", "subfolder", "file.txt"))
	print("Posix style:", xpath("folder\\subfolder", "file.txt", posix=True))
	print("Windows style:", xpath("folder/subfolder", "file.txt", posix=False))
	
	# Test EXT
	print("\nEXT():")
	print("Extension of file.txt:", EXT("file.txt"))
	print("Extension of archive.tar.gz:", EXT("archive.tar.gz"))
	
	# Test file_exists
	print("\nfile_exists():")
	print(f"Does {test_file} exist?", file_exists(".", test_file))
	print("Does non_existent.txt exist?", file_exists(".", "non_existent.txt"))
	
	# Test remove_new_lines
	print("\nremove_new_lines():")
	multiline = "Line 1\nLine 2\\nLine 3"
	print(f"Original: {repr(multiline)}")
	print(f"Processed: {repr(remove_new_lines(multiline))}")
	
	# Test make_dir
	print("\nmake_dir():")
	UX_Tools_test_dir = make_dir("UX_Tools_test_dir", "subdir")
	print(f"Created directory: {UX_Tools_test_dir}")
	
	# Test os_scan_walk
	print("\nos_scan_walk():")
	print("Files in current directory:")
	for entry in os_scan_walk("."):
		print(f"- {entry.name}")
	
	# Test is_file and is_filetype
	print("\nis_file() and is_filetype():")
	print(f"Is {test_file} a file?", is_file(test_file))
	print(f"Is {test_file} a text file?", is_filetype(test_file, ext_type="text"))
	print(f"Is {test_video} a video file?", is_filetype(test_video, ext_type="video"))

	
	# Test Text_Box
	print("\nText_Box():")
	text_box.print_box("This is a test message", style="star")
	text_box.print_box("Another message\nwith multiple lines", style="dash")
	
	# Test ease_in_out
	print("\nease_in_out():")
	duration = 10
	ease_in = 2
	ease_out = 3
	for t in [0, 1, 5, 9, 10, 11]:
		print(f"t={t}: {ease_in_out(t, duration, ease_in, ease_out):.2f}")
	
	# Test str_comma and str_comma_to_float
	print("\nstr_comma() and str_comma_to_float():")
	num = 1234.5678
	print(f"Original: {num}, Formatted: {str_comma(num)}")
	comma_num = "1.234,56"
	print(f"Original: {comma_num}, Converted: {str_comma_to_float(comma_num)}")
	
	# Test CaseInsensitiveDict
	print("\nCaseInsensitiveDict():")
	cid = CaseInsensitiveDict({"Name": "John", "Age": 30})
	print("Access with different cases:", cid["NAME"], cid["name"])
	print("Contains check:", "AGE" in cid, "gender" in cid)
	
	# Test lprint
	print("\nlprint():")
	lprint("This should show the line number where it's called")
	
	# Clean up test files
	os.remove(test_file)
	os.remove(test_json)
	shutil.rmtree("UX_Tools_test_dir")
	
	print("\nAll tests completed!")