"""
Modern build system using PyInstaller.
Replaces the custom bundling system with standard tooling.
"""
# ruff: noqa: T201  # Allow print statements in build script

import shutil
import subprocess
import sys
from pathlib import Path


def clean_build_artifacts():
    """Remove old build artifacts."""
    paths_to_clean = [
        "build",
        "dist",
        "*.spec",
    ]

    for path in paths_to_clean:
        if Path(path).exists():
            try:
                if Path(path).is_dir():
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                else:
                    Path(path).unlink()
                    print(f"Removed file: {path}")
            except (OSError, PermissionError) as e:
                print(f"Could not remove {path}: {e}")


def build_with_pyinstaller():
    """Build the application using PyInstaller."""

    print("Building BeanieDeploy with PyInstaller...")

    # Read version from ReleaseInfo.txt
    release_info = {}
    if Path("ReleaseInfo.txt").exists():
        with Path("ReleaseInfo.txt").open() as f:
            for line in f:
                if "==>" in line:
                    key, value = line.strip().split(" ==> ")
                    release_info[key] = value

    app_name = release_info.get("AppName", "BeanieDeploy")
    app_version = release_info.get("AppVersion", "0.94-Beta")

    # Find PyInstaller executable
    pyinstaller_path = shutil.which("pyinstaller")
    if not pyinstaller_path:
        # Try virtual environment path
        venv_pyinstaller = Path(".venv/Scripts/pyinstaller.exe")
        if venv_pyinstaller.exists():
            pyinstaller_path = str(venv_pyinstaller)
        else:
            print(
                "PyInstaller not found! Please install it with: pip install pyinstaller"
            )
            return False

    # PyInstaller command
    cmd = [
        pyinstaller_path,
        "--onefile",
        "--name",
        f"{app_name}-{app_version}",
        "--distpath",
        "dist",
        "--workpath",
        "build",
        "--specpath",
        ".",
        # Add the src directory to Python path
        "--paths",
        "src",
        # Add data files
        "--add-data",
        "src/locales;locales",
        "--add-data",
        "src/resources;resources",
        # Add hidden imports for babel translation system
        "--hidden-import",
        "babel.localedata",
        # Add hidden imports for langtable and related modules
        "--hidden-import",
        "langtable",
        "--hidden-import",
        "babel",
        "--hidden-import",
        "babel.localedata",
        # Collect all data for langtable
        "--collect-data",
        "langtable",
        "--collect-data",
        "babel",
        # Add hidden imports for jaraco modules used by pkg_resources
        "--hidden-import",
        "jaraco.classes",
        "--hidden-import",
        "jaraco.functools",
        "--hidden-import",
        "jaraco.text",
        "--hidden-import",
        "jaraco.context",
        "--hidden-import",
        "jaraco.collections",
        "src/main.py",
    ]

    # Add icon if it exists
    icon_path = Path("icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    # Add version info
    cmd.extend(["--version-file", "version_info.txt"])

    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created: dist/{app_name}-{app_version}.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False


def create_version_info():
    """Create version info file for PyInstaller."""

    # Read version from ReleaseInfo.txt
    release_info = {}
    if Path("ReleaseInfo.txt").exists():
        with Path("ReleaseInfo.txt").open() as f:
            for line in f:
                if "==>" in line:
                    key, value = line.strip().split(" ==> ")
                    release_info[key] = value

    app_name = release_info.get("AppName", "")
    app_version = release_info.get("AppVersion", "Snapshot")
    description = release_info.get("Description", "")
    author = release_info.get("Author", "")
    company = release_info.get("Company", author)
    copyright_info = release_info.get("Copyright", "")

    # Convert version to Windows format (1.0.0.0)
    version_parts = app_version.split("-")[0].split(".")
    while len(version_parts) < 4:
        version_parts.append("0")
    version_tuple = ", ".join(version_parts[:4])

    version_info_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'{company}'),
            StringStruct(u'FileDescription', u'{description}'),
            StringStruct(u'FileVersion', u'1.0.0.0'),
            StringStruct(u'InternalName', u'{app_name}'),
            StringStruct(u'LegalCopyright', u'{copyright_info}'),
            StringStruct(u'OriginalFilename', u'{app_name}-{app_version}.exe'),
            StringStruct(u'ProductName', u'{app_name}'),
            StringStruct(u'ProductVersion', u'{app_version}')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""

    with Path("version_info.txt").open("w", encoding="utf-8") as f:
        f.write(version_info_content)

    print("Created version_info.txt")


def main():
    """Main build function."""
    print("Building BeanieDeploy with PyInstaller")

    # Clean up old build artifacts
    clean_build_artifacts()

    # Create version info
    create_version_info()

    # Build with PyInstaller
    if build_with_pyinstaller():
        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
