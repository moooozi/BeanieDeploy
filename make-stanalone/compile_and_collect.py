import os
import py_compile
import shutil
import sys
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

print(Path(sys.executable).parent.absolute())

# Function to copy and compile files
def copy_and_compile_files(src_dir, dst_dir, ignore_modules=[]):
    for root, dirs, files in os.walk(src_dir):
        if "__pycache__" in root:
            continue
        pathparts = Path(root).absolute().parts
        if "Lib" in pathparts and pathparts.index("Lib") < len(pathparts)-1 and pathparts[pathparts.index("Lib")+1] in ignore_modules:
            continue
        rel_path = os.path.relpath(root, src_dir)
        (dst_dir / rel_path).mkdir(parents=True, exist_ok=True)
        for file in files:
            if any(ignore in file for ignore in ignore_modules):
                continue
            src_file = Path(root) / file
            dst_file = dst_dir / rel_path / file
            if file.endswith(".py"):
                py_compile.compile(str(src_file), str(dst_file) + "c", optimize=2)
            else:
                shutil.copy(src_file, dst_file)

# Copy and compile files in the source directory
copy_and_compile_files(src_dir, dst_dir)

# Copy Python libraries
dst_dir = Path(r"../release/interpreter/")
dst_dir.mkdir(parents=True, exist_ok=True)
python_libs = [x for x in Path(sys.exec_prefix).iterdir() if x.is_file() and x.name.startswith("python") and (x.name.endswith(".exe") or x.name.endswith(".dll"))]
for src_file in python_libs:
    shutil.copy(src_file, dst_dir / src_file.name)

# Define library directories
libs_dirs = [Path(sys.exec_prefix) / "tcl"]
libs_dirs.extend(Path(p) for p in sys.path if p.startswith(sys.exec_prefix) and p != sys.exec_prefix)

# Copy and compile files in the library directories
ignore_modules = ['test', 'ensurepip', 'idlelib','turtledemo', 'venv', '_test','site-packages']
for lib_dir in libs_dirs:
    if "site-packages" in lib_dir.parts:
        continue
    dst_dir = Path(r"../release/interpreter/") / lib_dir.name
    copy_and_compile_files(lib_dir, dst_dir, ignore_modules)