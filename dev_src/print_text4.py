import logging
import re
import sys
import platform
from queue import Queue
from time import sleep
from shutil import get_terminal_size
from math import ceil
# Enable Windows console color and optionally adjust font size
if platform.system() == "Windows":
    import ctypes

    def enable_win_term_color(full_feature=False, font_height=16):
        try:
            kernel32 = ctypes.WinDLL('kernel32')
            hStdOut = kernel32.GetStdHandle(-11)

            # Enable ANSI escape sequences
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
            mode.value |= 4
            kernel32.SetConsoleMode(hStdOut, mode)

            if full_feature:
                class COORD(ctypes.Structure):
                    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

                class CONSOLE_FONT_INFOEX(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_ulong),
                        ("nFont", ctypes.c_ulong),
                        ("dwFontSize", COORD),
                        ("FontFamily", ctypes.c_uint),
                        ("FontWeight", ctypes.c_uint),
                        ("FaceName", ctypes.c_wchar * 32)
                    ]

                font = CONSOLE_FONT_INFOEX()
                font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
                kernel32.GetCurrentConsoleFontEx(hStdOut, False, ctypes.byref(font))
                font.dwFontSize.Y = font_height
                kernel32.SetCurrentConsoleFontEx(hStdOut, False, ctypes.byref(font))
        except Exception as e:
            print(f"[Warning] Failed to enable Windows terminal features: {e}")

    enable_win_term_color(full_feature=True)


class TerminalStyler:
	COLOR_MAP = {
		'a': '30', 'r': '31', 'g': '32', 'y': '33', 'b': '34',
		'p': '35', 'c': '36', 'w': '37', '=': '0', '_': True
	}
	BG_MAP = {
		'k': '40', 'r': '41', 'g': '42', 'y': '43', 'b': '44',
		'p': '45', 'c': '46', 'w': '47', '_': True
	}
	# _ = no-op filler (COLOR_MAP also has '_': True)
	# d = dim/faint (ANSI 2) - /d/muted/=/
	STYLE_MAP = {'u': '4', 'i': '7', 'h': '1', '_': True, 'd': '2'}

	CODE_RE = re.compile(r"/([a-z=_]{1,3})/")
	PAUSE_RE = re.compile(r"/s([\d.]+)/")

	def __init__(self):
		self.no_code = False
		self.no_colors = False

	def parse(self, text: str, highlighter: bool = False):
		items = []
		buffer = []

		if highlighter:
			text = re.sub(r"===(.*?)===", r"/hu/\1/=/", text)
			text = re.sub(r"==(.*?)==", r"/u/\1/=/", text)

		i = 0
		while i < len(text):
			if text[i:i+3] == '/~`':
				self.no_code = True
				i += 3
				continue
			if text[i:i+3] == '`~/':
				self.no_code = False
				i += 3
				continue
			if text[i:i+3] == '/~~':
				self.no_colors = True
				i += 3
				continue
			if text[i:i+3] == '~~/':
				self.no_colors = False
				i += 3
				continue

			pause_match = self.PAUSE_RE.match(text, i)
			if pause_match:
				if buffer:
					items.append({'type': 'string', 'value': ''.join(buffer)})
					buffer.clear()
				items.append({'type': 'pause', 'value': float(pause_match.group(1))})
				i += len(pause_match.group(0))
				continue

			code_match = self.CODE_RE.match(text, i)
			if code_match and not self.no_code:
				code = code_match.group(1)
				if self.no_colors:
					i += len(code_match.group(0))
					continue

				parts = [TerminalStyler.COLOR_MAP.get(c, '') for c in code if c in TerminalStyler.COLOR_MAP]
				if len(code) > 1:
					parts += [TerminalStyler.BG_MAP.get(c, '') for c in code[1] if c in TerminalStyler.BG_MAP]
				
				parts += [TerminalStyler.STYLE_MAP.get(c, '') for c in code if c in TerminalStyler.STYLE_MAP]

				if buffer:
					items.append({'type': 'string', 'value': ''.join(buffer)})
					buffer.clear()

				if parts and '' not in parts:
					while True in parts:
						parts.remove(True)
					# /_/ is a pure no-op filler - consume the tag, emit nothing
					if parts:
						items.append({'type': 'style', 'value': ';'.join(parts)})
					i += len(code_match.group(0))
				continue

			buffer.append(text[i])
			i += 1

		if buffer:
			items.append({'type': 'string', 'value': ''.join(buffer)})

		return items

	def to_string(self, parsed, *, reset: bool = True):
		result = []
		for part in parsed:
			if part['type'] == 'pause':
				continue  # Pauses are not converted to string
			elif part['type'] == 'style':
				result.append(f"\033[{part['value']}m")
			elif part['type'] == 'string':
				result.append(part['value'])
		if reset:
			result.append("\033[0m")
		return ''.join(result)

	def style(self, text: str, highlighter: bool = False) -> str:
		"""Convert /r/ markup to ANSI escape codes."""
		return self.to_string(self.parse(text, highlighter))


class XPrint:
	def __init__(self):
		self.styler = TerminalStyler()
		self.wait_time = 0.0

	def slowtype(self, *text, sep=' ', end='\n', wait_time=0.0, highlighter=False):
		full_text = sep.join(map(str, text)) + end
		parsed = self.styler.parse(full_text, highlighter)

		for part in parsed:
			if part['type'] == 'pause':
				sleep(part['value'])
			elif part['type'] == 'style':
				sys.stdout.write(f"\033[{part['value']}m")
			elif part['type'] == 'string':
				if self.wait_time:
					for c in part['value']:
						sys.stdout.write(c)
						sys.stdout.flush()
						sleep(wait_time)
				else:
					sys.stdout.write(part['value'])
					sys.stdout.flush()
		sys.stdout.write("\033[0m")
		sys.stdout.flush()

	def remove_style(self, text, highlighter=False):
		parsed = self.styler.parse(text, highlighter)
		return ''.join(part['value'] for part in parsed if part['type'] == 'string')


class OneLinePrinter(XPrint):
	def __init__(self):
		super().__init__()
		self.old_len = []
		self.queue = Queue()
		self.BUSY = False

	def get_line_lengths(self, string: str):
		return [max(len(line), 1) for line in string.split('\n')]

	def get_line_height(self, length):
		width = int(get_terminal_size()[0])
		return ceil(length / width)

	def _clear_old(self):
		total = sum(self.get_line_height(l) for l in self.old_len) -1 
		sys.stdout.write("\033[2K\033[1G" + '\x1b[1A\x1b[2K' * total)

	def update(self, *text, sep=' ', end='\n', wait_time=0.0, highlighter=False):
		full_text = sep.join(map(str, text)) + end
		parsed_text = self.remove_style(full_text, highlighter)

		self._clear_old()
		self.slowtype(full_text, wait_time=wait_time, highlighter=highlighter, sep='', end='')
		self.old_len = self.get_line_lengths(parsed_text)


class XLogger:
	def __init__(self, name=None):
		if name is None:
			name = __name__

		self.logger = logging.getLogger(name)

		if not self.logger.hasHandlers():
			self.logger.setLevel(logging.DEBUG)
			stream_handler = logging.StreamHandler()
			formatter = logging.Formatter(
				'%(asctime)s %(message)s',
				datefmt='[%H:%M:%S]'
			)
			stream_handler.setFormatter(formatter)
			self.logger.addHandler(stream_handler)

		self.styler = TerminalStyler()

	def _log(self, level, *text, sep=' ', highlighter=False, **kwargs):
		full_text = sep.join(map(str, text))
		# clean_text = ''.join(part['value'] for part in self.styler.parse(full_text, highlighter)) # if part['type'] == 'string')
		clean_text = self.styler.to_string(self.styler.parse(full_text, highlighter))
		# print(clean_text)
		getattr(self.logger, level)(clean_text)

	def debug(self, *text, **kwargs): self._log('debug', *text, **kwargs)
	def info(self, *text, **kwargs): self._log('info', *text, **kwargs)
	def warning(self, *text, **kwargs): self._log('warning', *text, **kwargs)
	def error(self, *text, **kwargs): self._log('error', *text, **kwargs)
	def critical(self, *text, **kwargs): self._log('critical', *text, **kwargs)


# Shared styler + helpers for logging formatters
_styler = TerminalStyler()


def style_text(text: str, highlighter: bool = False) -> str:
	"""Convert /r/ markup in *text* to ANSI colors (for log formatters)."""
	return _styler.style(text, highlighter)


def delete_last_line(lines: int = 1) -> None:
	"""Erase the last *lines* of STDOUT (ANSI cursor up + clear). Migrated from IO_sys."""
	if lines == 0:
		sys.stdout.write("\n")
		delete_last_line(1)
		return
	for _ in range(max(0, int(lines))):
		sys.stdout.write("\x1b[1A")
		sys.stdout.write("\x1b[2K")
	sys.stdout.flush()


# Usage Examples
xprint = XPrint().slowtype
oneline = OneLinePrinter()
xlogger = XLogger()
xStart = "/~`"
xEnd = "`~/"

xIgnore = lambda x: f"{xStart}{x}{xEnd}"
red = lambda x: f"\033[31m{x}\033[0m"
green = lambda x: f"\033[32m{x}\033[0m"
blue = lambda x: f"\033[34m{x}\033[0m"
yellow = lambda x: f"\033[33m{x}\033[0m"
purple = lambda x: f"\033[35m{x}\033[0m"
cyan = lambda x: f"\033[36m{x}\033[0m"
white = lambda x: f"\033[37m{x}\033[0m"
bold = lambda x: f"\033[1m{x}\033[0m"
inverse = lambda x: f"\033[7m{x}\033[0m"
underline = lambda x: f"\033[4m{x}\033[0m"

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)

	xprint("/rhu/Hello, World!/=/\n", wait_time=0.02)
	xprint("/rXu/Hello, Fake World!/=/\n", wait_time=0.02)
	xprint("This is a /r/test/=/ with /g/green/=/ and /b/blue/=/ text.\n", wait_time=0.02)
	xprint("This is a /_r/test/=/ with /_g/green/=/ and /_b/blue/=/ /i/background/=/.\n", 	wait_time=0.02, highlighter=True)
	oneline.update("Progress: ", 0)
	for i in range(101):
		oneline.update(f"Progress: {i}%")
		sleep(0.01)
	xlogger.warning("/yhu/This is a warning with style/=/")

	print("\n\nTesting multiline")
		
	loads = [
"""\t\\
\t \\
\t  \\
""",
'''\t |
\t |
\t |
''',
"""\t  /
\t /
\t/
""",
"""
\t----

"""
]
	oneline = OneLinePrinter()
	for i in range(50):
		oneline.update(loads[i%len(loads)])
		sleep(.2)
