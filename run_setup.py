import os
import shutil
import subprocess
import sys

py = sys.executable


def run(*args, check=True):
	print(">", " ".join(args))
	return subprocess.run(args, check=check)


# 0. regenerate src/ from dev_src/
run(py, "build_src.py")

# 1. clean old artifacts. A leftover "build/" folder in the cwd shadows the
#    `build` module ("'build' is a package and cannot be directly executed").
for d in ("dist", "build", "pyrobox.egg-info"):
	shutil.rmtree(d, ignore_errors=True)

# 2. make sure the build tools exist
run(py, "-m", "pip", "install", "-q", "build", "twine")

# 3. build sdist + wheel
run(py, "-m", "build")

with open('VERSION', 'r') as f:
	version = f.read().strip()

# 4. local install test
run(py, "-m", "pip", "uninstall", "pyrobox", "-y", check=False)
run(py, "-m", "pip", "install", f"./dist/pyrobox-{version}.tar.gz")

# 5. publish only on explicit confirmation
if input(f"Upload pyrobox {version} to PyPI? [y/N] ").strip().lower() == "y":
	run(py, "-m", "twine", "upload", "dist/*")
else:
	print("Skipped PyPI upload.")
