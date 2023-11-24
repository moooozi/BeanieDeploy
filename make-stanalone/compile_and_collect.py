import os
import py_compile
import shutil
import modulefinder
import sys
import pathlib

# Define the source and destination directories
src_dir = "../src"
dst_dir = "../release/src"
#print (sys.path)
print (pathlib.Path(sys.executable).parent.absolute())
#exit()
# Loop through all the files and subdirectories in the source directory
for root, dirs, files in os.walk(src_dir):
    # Get the relative path of the current directory
    if root.endswith("__pycache__"):
        continue
    rel_path = os.path.relpath(root, src_dir)
    # Create the corresponding destination directory if it does not exist
    os.makedirs(os.path.join(dst_dir, rel_path), exist_ok=True)
    # Loop through all the files in the current directory
    for file in files:
        # Get the source and destination file paths
        src_file = os.path.join(root, file)
        dst_file = os.path.join(dst_dir, rel_path, file)
        # Check the file extension
        if file.endswith(".py"):
            # Compile the python file and save it as a .pyc file
            py_compile.compile(src_file, dst_file + "c", optimize=2)
        else:
            # Copy the file as it is
            shutil.copy(src_file, dst_file)



dst_dir = "../release/interpreter/"
os.makedirs(dst_dir, exist_ok=True)
pythonlibs = list(x for x in pathlib.Path(sys.exec_prefix).iterdir() if x.is_file() and x.name.startswith("python") and (x.name.endswith(".exe") or x.name.endswith(".dll")))
for src_file in pythonlibs:
    dst_file = dst_dir + src_file.name
    shutil.copy(src_file, dst_file)

libs_dirs = []
libs_dirs.append(os.path.join(sys.exec_prefix, "tcl"))
for sys_path in sys.path:
    if sys_path.startswith(sys.exec_prefix) and sys_path != sys.exec_prefix:
        libs_dirs.append(sys_path)

print (libs_dirs)
for lib_dir in libs_dirs:
    src_dir = lib_dir
    dst_dir = "../release/interpreter/" + pathlib.Path(lib_dir).name
    # Loop through all the files and subdirectories in the source directory
    for root, dirs, files in os.walk(src_dir):
        # Get the relative path of the current directory
        if pathlib.Path(root).name == "__pycache__":
            continue
        pathparts = pathlib.Path(root).absolute().parts

        ignore_modules = ['test', 'ensurepip', 'idlelib','turtledemo', 'venv']
        if "Lib" in pathparts and pathparts.index("Lib") < len(pathparts)-1 and pathparts[pathparts.index("Lib")+1] in ignore_modules:
            continue
        if "site-packages" in pathlib.Path(root).parts:
            continue
        rel_path = os.path.relpath(root, src_dir)
        # Create the corresponding destination directory if it does not exist
        os.makedirs(os.path.join(dst_dir, rel_path), exist_ok=True)
        # Loop through all the files in the current directory
        for file in files:
            if "_test" in file:
                continue
            # Get the source and destination file paths
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, rel_path, file)
            # Check the file extension
            if file.endswith(".py"):
                # Compile the python file and save it as a .pyc file
                py_compile.compile(src_file, dst_file + "c", optimize=2)
            else:
                # Copy the file as it is
                shutil.copy(src_file, dst_file)

