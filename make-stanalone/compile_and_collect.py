import os
import py_compile
import shutil
import sys
import re
from pathlib import Path



# Define the release directory
release_dir = Path(r"../release")
# Remove the release directory if it exists
if release_dir.exists():
    shutil.rmtree(release_dir)

# Recreate the release directory
release_dir.mkdir(parents=True, exist_ok=True)

# Define the source and destination directories
src_dir = Path(r"../src")
dst_dir = Path(r"../release/src")


def is_ignored(name, ignores):
    for ignore in ignores:
        if isinstance(ignore, re.Pattern):
            if bool(re.fullmatch(ignore, name)):
                return True
        elif isinstance(ignore, str):
            if ignore == name:
                return True
        else:
            raise ValueError(f"Invalid type: {type(ignore)}. Expected str or re.Pattern.")
    return False

# Function to copy and compile files
def copy_and_compile_files(src_dir, dst_dir, ignore_paths=[], ignore_files=[]):
    for root, dirs, files in os.walk(src_dir):
        if "__pycache__" in root:
            continue
        current_path = Path(root).absolute().as_posix()
        if is_ignored(current_path, ignore_paths):
            continue
        rel_path = os.path.relpath(root, src_dir)
        (dst_dir / rel_path).mkdir(parents=True, exist_ok=True)
        for file in files:
            if is_ignored(file, ignore_files):
                continue
            src_file = Path(root) / file
            dst_file = dst_dir / rel_path / file
            if file.endswith(".py"):
                py_compile.compile(str(src_file), str(dst_file) + "c", optimize=2)
            else:
                shutil.copy(src_file, dst_file)

# Copy and compile files in the source directory
ignored_src_file_names = ["playground.py", "install_args.pkl"]
copy_and_compile_files(src_dir, dst_dir, ignore_files=ignored_src_file_names)

# Copy Python libraries
dst_dir = Path(r"../release/interpreter/")
dst_dir.mkdir(parents=True, exist_ok=True)
python_libs = [x for x in Path(sys.exec_prefix).iterdir() if x.is_file() and x.name.startswith("python") and (x.name.endswith(".exe") or x.name.endswith(".dll"))]
for src_file in python_libs:
    shutil.copy(src_file, dst_dir / src_file.name)

# Define library directories
libs_dirs = [Path(sys.exec_prefix) / "tcl"]
libs_dirs.extend(Path(p) for p in sys.path if p.startswith(sys.exec_prefix) and p != sys.exec_prefix)
libs_dirs.remove("site-packages") if "site-packages" in libs_dirs else None
# Copy and compile files in the library directories
ignore_modules = ['test', 'ensurepip', 'idlelib','turtledemo', 'venv', 'site-packages']
ignored_paths = [re.compile(f'.*/Lib/{module_name}(/.*)?$') for module_name in ignore_modules]

ignored_file_names = [re.compile('.*_test.*'),]
for lib_dir in libs_dirs:
    dst_dir = Path(r"../release/interpreter/") / lib_dir.name
    copy_and_compile_files(lib_dir, dst_dir, ignored_paths, ignored_file_names)
