"""Regenerate ``src/`` (the shipped ``pyrobox`` package) from ``dev_src/``.

Usage:  python build_src.py [--dry-run]

- copies runtime .py modules and rewrites sibling imports to relative ones
- copies html/js/css assets next to them (loaded as package data)
- keeps hand-written ``src/__init__.py`` and ``src/__main__.py``
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DEV = os.path.join(ROOT, "dev_src")
SRC = os.path.join(ROOT, "src")

KEEP = {"__init__.py", "__main__.py"}

PY_MODULES = [
	"_arg_parser", "_exceptions", "_fs_utils", "_list_maker", "_page_templates",
	"_sub_extractor", "_zipfly_manager", "clone", "data_types", "pyroDB4",
	"print_text4", "pyrobox_ServerHost", "pyroboxCore", "server", "user_mgmt", "UX_Tools",
]

ASSET_RE = re.compile(r"^(html_.*\.html|script_.*\.js|style_main\.css|video\.css|plyr\.polyfilled\.min\.js)$")
ASSET_SKIP = re.compile(r"(\.bak\.|\.test\.| copy\.)")

_names = "|".join(re.escape(m) for m in PY_MODULES)
RE_FROM = re.compile(r"^(\s*)from\s+(%s)\s+import\s+" % _names, re.M)
RE_IMPORT = re.compile(r"^(\s*)import\s+(%s)(\s+as\s+\w+)?\s*$" % _names, re.M)


def rewrite(text):
	text = RE_FROM.sub(lambda m: "%sfrom .%s import " % (m.group(1), m.group(2)), text)

	def _imp(m):
		alias = m.group(3) or ""
		return "%sfrom . import %s%s" % (m.group(1), m.group(2), alias)

	return RE_IMPORT.sub(_imp, text)


# dev_src keeps print_text4 as an external (pulled-in) optional module; the
# shipped package bundles it, so import it directly there.
XPRINT_DEV = 'xprint = import_loop(["print_text4"], export="xprint", fallback=lambda: _fallback_xprint)'
XPRINT_SRC = "from .print_text4 import xprint"


def patch(name, text):
	if name == "UX_Tools":
		if XPRINT_DEV not in text:
			sys.exit("build_src: xprint import line not found in UX_Tools.py")
		text = text.replace(XPRINT_DEV, XPRINT_SRC)
	return text


def main():
	dry = "--dry-run" in sys.argv
	assets = sorted(f for f in os.listdir(DEV)
		if ASSET_RE.match(f) and not ASSET_SKIP.search(f) and os.path.isfile(os.path.join(DEV, f)))

	# clean stale generated files
	for f in sorted(os.listdir(SRC)):
		p = os.path.join(SRC, f)
		if os.path.isfile(p) and f not in KEEP:
			print("remove", f)
			if not dry:
				os.remove(p)

	for m in PY_MODULES:
		with open(os.path.join(DEV, m + ".py"), encoding="utf-8", newline="") as fh:
			text = fh.read()
		print("py   ", m + ".py")
		if not dry:
			with open(os.path.join(SRC, m + ".py"), "w", encoding="utf-8", newline="") as fh:
				fh.write(patch(m, rewrite(text)))

	for a in assets:
		print("asset", a)
		if not dry:
			shutil.copyfile(os.path.join(DEV, a), os.path.join(SRC, a))


if __name__ == "__main__":
	main()
