import argparse
import logging
import os
import sys
from pathlib import Path

# Check for elevated helper mode (requires to handle /PIPE here for PyInstaller bundles)
if "/PIPE" in sys.argv:
    pipe_index = sys.argv.index("/PIPE")
    if pipe_index + 1 < len(sys.argv):
        pipe_name = sys.argv[pipe_index + 1]
        import privilege_helper

        privilege_helper.main(pipe_name)
        raise SystemExit(0)

# Handle PyInstaller bundle
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # # PyInstaller sets _MEIPASS for bundles
    bundle_dir = Path(getattr(sys, "_MEIPASS", ""))
    # Add the bundle directory to Python path so translations can be found
    sys.path.insert(0, str(bundle_dir))
else:
    # Running in normal Python environment
    bundle_dir = Path(__file__).parent

# Import our new systems
# Legacy imports (to be refactored)
import multilingual
from app import MainApp
from config.settings import get_config
from core.state import get_state
from services.system import get_windows_ui_locale, is_admin
from utils.logging import setup_file_logging


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip_check", action="store_true", help="Skip the check")
    parser.add_argument(
        "--release", action="store_true", help="The App is in release mode"
    )
    parser.add_argument(
        "--app_version",
        type=str,
    )
    return parser.parse_args()


def set_skip_check(skip: bool):
    state = get_state()
    state.compatibility.skip_check = skip
    if skip:
        sys.argv.append("--skip_check")


def run():
    """
    Run the application with proper error handling and logging.
    """
    try:
        # Set up the working directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)

        # Initialize configuration and logging
        config = get_config()
        setup_file_logging(config.paths.work_dir / "beaniedeploy.log")

        # Parse arguments
        args = parse_arguments()

        # Auto-detect release mode for PyInstaller builds
        is_pyinstaller_bundle = get_state().is_release_mode
        if is_pyinstaller_bundle:
            args.release = True
            logging.info("PyInstaller bundle detected - running in release mode")
        else:
            # Development mode - always skip checks
            set_skip_check(skip=True)
            logging.info("Running in debug mode")

        # Update version if provided
        if args.app_version:
            config.update_version(args.app_version)

        # Log application startup
        logging.info(f"APP STARTING: {config.app.name} v{config.app.version}")

        # Create work directory
        config.paths.work_dir.mkdir(parents=True, exist_ok=True)
        config.paths.wifi_profiles_dir.mkdir(parents=True, exist_ok=True)
        if config.paths.wifi_profiles_dir:
            config.paths.wifi_profiles_dir.mkdir(parents=True, exist_ok=True)

        # Set up language
        lang_name = multilingual.get_lang_name_by_code(
            get_windows_ui_locale().split("_")[0]
        )
        multilingual.set_lang(lang_name if lang_name else "English")

        # Create and run the main application
        app = MainApp(skip_check=args.skip_check) if args.skip_check else MainApp()

        app.mainloop()

    except Exception as e:
        logging.exception(f"Application error: {e}")
        raise


if __name__ == "__main__":
    args = parse_arguments()

    # Auto-detect release mode for PyInstaller builds
    is_pyinstaller_bundle = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    is_release_mode = args.release or is_pyinstaller_bundle

    if is_release_mode:
        try:
            run()
        except Exception as e:
            logging.error(f"Application failed in release mode: {e}")
            # Fail silently in release mode to avoid showing errors to users
            raise SystemExit(1) from e
    else:
        # Development mode - show errors and keep console open
        if is_admin():
            try:
                run()
            except Exception:
                logging.exception("Application failed in debug mode")
            finally:
                input("Press Enter to exit...")
        else:
            try:
                run()
            except Exception:
                logging.exception("Application failed without admin privileges")
                input("Press Enter to exit...")
