"""Terminal markup → ANSI.

Markup
------
Style tags are ``/codes/`` with 1–3 chars from the maps below::

    /r/red/=/          /gh/bold green/=/     /_r/red-on-default bg/=/
    /d/dim/=/          /hu/bold underline/=/ /i/inverse/=/
    /s0.5/             pause 0.5s (xprint only)

    color  a r g y b p c w = _     (= reset, _ filler)
    bg     2nd char → k r g y b p c w _
    style  u i h d _               (underline / inverse / bold / dim)

Literals (urls, titles, paths)
------------------------------
Any ``/src/``, ``/api/``, … inside user text is also a tag. Wrap it::

    xIgnore(host)                  # → xStart + host + xEnd
    f"/c/{xIgnore(title)}/=/"      # color outside, literal inside

    xStart / xEnd   =  /~`  …  `~/     ignore all tags (no_code)
    /~~  …  ~~/                        keep tags but emit no ANSI (no_colors)

highlighter=True turns ``===x===`` → bold+underline and ``==x==`` → underline.
"""

import logging
import re
import sys
import platform
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


# ---- literal / mute wrappers -------------------------------------------------
xStart = "/~`"      # begin no_code  (tags stay as text)
xEnd = "`~/"        # end   no_code
xMute = "/~~"       # begin no_colors (tags consumed, no ANSI)
xUnmute = "~~/"     # end   no_colors

_LEN_START = len(xStart)
_LEN_END = len(xEnd)
_LEN_MUTE = len(xMute)
_LEN_UNMUTE = len(xUnmute)


def xIgnore(text) -> str:
	"""Wrap *text* so /codes/ inside are printed literally (uses xStart/xEnd)."""
	return f"{xStart}{text}{xEnd}"


class TerminalStyler:
	COLOR_MAP = {
		'a': '30', 'r': '31', 'g': '32', 'y': '33', 'b': '34',
		'p': '35', 'c': '36', 'w': '37', '=': '0', '_': True
	}
	BG_MAP = {
		'k': '40', 'r': '41', 'g': '42', 'y': '43', 'b': '44',
		'p': '45', 'c': '46', 'w': '47', '_': True
	}
	# _ = no-op filler; d = dim/faint (ANSI 2)
	STYLE_MAP = {'u': '4', 'i': '7', 'h': '1', '_': True, 'd': '2'}

	CODE_RE = re.compile(r"/([a-z=_]{1,3})/")
	PAUSE_RE = re.compile(r"/s([\d.]+)/")
	HIGHLIGHT_TRIPLE = re.compile(r"===(.*?)===")
	HIGHLIGHT_DOUBLE = re.compile(r"==(.*?)==")

	def __init__(self):
		self.no_code = False
		self.no_colors = False

	@staticmethod
	def _next_mark(text: str, start: int, n: int) -> int:
		"""Soonest index that may begin ``/``, ``xEnd``, or ``xUnmute``."""
		best = n
		a = text.find('/', start)
		if 0 <= a < best:
			best = a
		b = text.find(xEnd, start)
		if 0 <= b < best:
			best = b
		c = text.find(xUnmute, start)
		if 0 <= c < best:
			best = c
		return best

	def _code_ansi(self, code: str):
		"""Map a /xyz/ body to ANSI params (skip no-op ``_``)."""
		parts = []
		color_get = self.COLOR_MAP.get
		style_get = self.STYLE_MAP.get
		for c in code:
			v = color_get(c)
			if v and v is not True:
				parts.append(v)
		if len(code) > 1:
			v = self.BG_MAP.get(code[1])
			if v and v is not True:
				parts.append(v)
		for c in code:
			v = style_get(c)
			if v and v is not True:
				parts.append(v)
		return parts

	def _prep(self, text: str, highlighter: bool) -> str:
		self.no_code = False
		self.no_colors = False
		if highlighter:
			text = self.HIGHLIGHT_TRIPLE.sub(r"/hu/\1/=/", text)
			text = self.HIGHLIGHT_DOUBLE.sub(r"/u/\1/=/", text)
		return text

	def parse(self, text: str, highlighter: bool = False):
		"""Tokenize into ``('string'|'style'|'pause', value)``.

		Jumps marker-to-marker. ``xEnd`` / ``xUnmute`` are found explicitly
		because they do not start with ``/``.
		"""
		text = self._prep(text, highlighter)
		items = []
		n = len(text)
		i = 0
		chunk = 0
		append = items.append

		while i < n:
			# Closers first — may sit where text[i] != '/'.
			if text.startswith(xEnd, i):
				if i > chunk:
					append(('string', text[chunk:i]))
				self.no_code = False
				i += _LEN_END
				chunk = i
				continue
			if text.startswith(xUnmute, i):
				if i > chunk:
					append(('string', text[chunk:i]))
				self.no_colors = False
				i += _LEN_UNMUTE
				chunk = i
				continue

			if text[i] != '/':
				i = self._next_mark(text, i + 1, n)
				continue

			if text.startswith(xStart, i):
				if i > chunk:
					append(('string', text[chunk:i]))
				self.no_code = True
				i += _LEN_START
				chunk = i
				continue
			if text.startswith(xMute, i):
				if i > chunk:
					append(('string', text[chunk:i]))
				self.no_colors = True
				i += _LEN_MUTE
				chunk = i
				continue

			pause_match = self.PAUSE_RE.match(text, i)
			if pause_match:
				if i > chunk:
					append(('string', text[chunk:i]))
				append(('pause', float(pause_match.group(1))))
				i = pause_match.end()
				chunk = i
				continue

			code_match = self.CODE_RE.match(text, i)
			if code_match and not self.no_code:
				if i > chunk:
					append(('string', text[chunk:i]))
				end = code_match.end()
				if not self.no_colors:
					parts = self._code_ansi(code_match.group(1))
					if parts:
						append(('style', ';'.join(parts)))
				# Always consume the tag (unknown /z/ used to infinite-loop).
				i = end
				chunk = i
				continue

			# Literal '/' — keep it in the string span.
			i += 1

		if chunk < n:
			append(('string', text[chunk:]))
		return items

	def to_string(self, parsed, *, reset: bool = True) -> str:
		"""Join parse tokens to an ANSI string (pauses dropped)."""
		result = []
		for kind, value in parsed:
			if kind == 'style':
				result.append(f"\033[{value}m")
			elif kind == 'string':
				result.append(value)
		if reset:
			result.append("\033[0m")
		return ''.join(result)

	def style(self, text: str, highlighter: bool = False) -> str:
		"""Markup → ANSI string (pauses ignored)."""
		return self.to_string(self.parse(text, highlighter))


class XPrint:
	def __init__(self):
		self.styler = TerminalStyler()
		self.wait_time = 0.0

	def _emit(self, parsed, delay: float):
		if delay:
			# Slow path: flush per character so typing is visible.
			for kind, value in parsed:
				if kind == 'pause':
					sleep(value)
				elif kind == 'style':
					sys.stdout.write(f"\033[{value}m")
					sys.stdout.flush()
				elif kind == 'string':
					for c in value:
						sys.stdout.write(c)
						sys.stdout.flush()
						sleep(delay)
			sys.stdout.write("\033[0m")
			sys.stdout.flush()
			return

		# Fast path: one buffer, one flush — pause still forces a break.
		buf = []
		for kind, value in parsed:
			if kind == 'pause':
				if buf:
					sys.stdout.write(''.join(buf))
					sys.stdout.flush()
					buf.clear()
				sleep(value)
			elif kind == 'style':
				buf.append(f"\033[{value}m")
			elif kind == 'string':
				buf.append(value)
		buf.append("\033[0m")
		sys.stdout.write(''.join(buf))
		sys.stdout.flush()

	def slowtype(self, *text, sep=' ', end='\n', wait_time=0.0, highlighter=False):
		full_text = sep.join(map(str, text)) + end
		parsed = self.styler.parse(full_text, highlighter)
		delay = wait_time if wait_time else self.wait_time
		self._emit(parsed, delay)

	def remove_style(self, text, highlighter=False):
		"""Strip markup; return plain text only."""
		parsed = self.styler.parse(text, highlighter)
		return ''.join(value for kind, value in parsed if kind == 'string')


class OneLinePrinter(XPrint):
	"""Overwrite the previous status block in-place (\\r + clear)."""

	def __init__(self):
		super().__init__()
		self.old_len = []

	def get_line_lengths(self, string: str):
		return [max(len(line), 1) for line in string.split('\n')]

	def get_line_height(self, length):
		width = int(get_terminal_size()[0])
		return ceil(length / width)

	def _clear_old(self):
		total = sum(self.get_line_height(l) for l in self.old_len) - 1
		sys.stdout.write("\033[2K\033[1G" + '\x1b[1A\x1b[2K' * total)

	def update(self, *text, sep=' ', end='\n', wait_time=0.0, highlighter=False):
		full_text = sep.join(map(str, text)) + end
		parsed = self.styler.parse(full_text, highlighter)
		plain = ''.join(v for k, v in parsed if k == 'string')

		self._clear_old()
		delay = wait_time if wait_time else self.wait_time
		self._emit(parsed, delay)
		self.old_len = self.get_line_lengths(plain)


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
		clean_text = self.styler.style(full_text, highlighter)
		getattr(self.logger, level)(clean_text)

	def debug(self, *text, **kwargs): self._log('debug', *text, **kwargs)
	def info(self, *text, **kwargs): self._log('info', *text, **kwargs)
	def warning(self, *text, **kwargs): self._log('warning', *text, **kwargs)
	def error(self, *text, **kwargs): self._log('error', *text, **kwargs)
	def critical(self, *text, **kwargs): self._log('critical', *text, **kwargs)


# Shared styler + helpers for logging formatters
_styler = TerminalStyler()


def style_text(text: str, highlighter: bool = False) -> str:
	"""Convert /r/ markup in *text* to ANSI (for log formatters)."""
	return _styler.style(text, highlighter)


def delete_last_line(lines: int = 1) -> None:
	"""Erase the last *lines* of STDOUT (ANSI cursor up + clear)."""
	if lines == 0:
		sys.stdout.write("\n")
		delete_last_line(1)
		return
	for _ in range(max(0, int(lines))):
		sys.stdout.write("\x1b[1A")
		sys.stdout.write("\x1b[2K")
	sys.stdout.flush()


xprint = XPrint().slowtype
oneline = OneLinePrinter()
xlogger = XLogger()
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
	xprint("This is a /_r/test/=/ with /_g/green/=/ and /_b/blue/=/ /i/background/=/.\n",
	       wait_time=0.02, highlighter=True)

	# xIgnore keeps path segments literal
	host = "github.com/foo/src/bar|fix/api/x"
	xprint(f"/g/ok/=/ · {xIgnore(host)}\n")

	oneline.update("Progress: ", 0)
	for i in range(101):
		oneline.update(f"Progress: {i}%")
		sleep(0.01)
	xlogger.warning("/yhu/This is a warning with style/=/")

	print("\n\nTesting multiline")

	loads = [
		"""\t\\\n\t \\\n\t  \\\n""",
		'''\t |\n\t |\n\t |\n''',
		"""\t  /\n\t /\n\t/\n""",
		"""\n\t----\n\n""",
	]
	oneline = OneLinePrinter()
	for i in range(50):
		oneline.update(loads[i % len(loads)])
		sleep(.2)
