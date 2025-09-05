import argparse
import os
import pickle
import traceback
import sys
from pathlib import Path
from typing import Optional

# Handle PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS) # type: ignore
    # Add the bundle directory to Python path so translations can be found
    sys.path.insert(0, str(bundle_dir))
else:
    # Running in normal Python environment
    bundle_dir = Path(__file__).parent

# Import our new systems
from config.settings import get_config
from utils.logging import setup_logging, get_logger
from utils.errors import get_error_handler, BeanieDeployError
from core.state import get_state_manager
from models.installation_context import InstallationContext

# Legacy imports (to be refactored)
import multilingual
from services.system import windows_language_code, is_admin
from app import MainApp


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip_check", action="store_true", help="Skip the check")
    parser.add_argument(
        "--release", action="store_true", help="The App is in release mode"
    )
    parser.add_argument(
        "--checks_dumb",
        type=argparse.FileType("rb"),
    )
    parser.add_argument(
        "--installation_context",
        type=argparse.FileType("rb"),
        help="Serialized InstallationContext for elevated installation process"
    )
    parser.add_argument(
        "--app_version",
        type=str,
    )
    args = parser.parse_args()
    return args

def set_skip_check(skip: bool):
    state = get_state_manager().state
    state.compatibility.skip_check = skip
    if skip:
        sys.argv.append("--skip_check")

def run():
    """
    Run the application with proper error handling and logging.
    """
    logger = None  # Initialize logger variable
    try:
        # Set up the working directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Initialize configuration and logging
        config = get_config()
        logger = setup_logging(
            level="DEBUG",  # Will be configurable later
            log_file=config.paths.work_dir / "beaniedeploy.log",
            console_output=True
        )
        
        # Parse arguments
        args = parse_arguments()
        
        
        # Auto-detect release mode for PyInstaller builds
        is_pyinstaller_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        if is_pyinstaller_bundle:
            args.release = True
            logger.info("PyInstaller bundle detected - running in release mode")
        else:
            # Development mode - always skip checks
            set_skip_check(True)
            logger.info("Running in debug mode")

        # Update version if provided
        if args.app_version:
            config.update_version(args.app_version)
        
        # Initialize state manager
        state_manager = get_state_manager()
        
        # Load serialized data if provided
        done_checks = None
        installation_context: Optional[InstallationContext] = None
        
        if args.checks_dumb:
            done_checks = pickle.load(args.checks_dumb)
            state_manager.state.update_compatibility_checks(done_checks)
            
        if args.installation_context:
            installation_context = pickle.load(args.installation_context)
                
        # Log application startup
        logger.info(f"APP STARTING: {config.app.name} v{config.app.version}")
        
        # Create work directory
        config.paths.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up language
        lang_code = multilingual.get_lang_by_code(windows_language_code())
        multilingual.set_lang(lang_code if lang_code else "English")
        
        # Create and run the main application
        if installation_context:
            app = MainApp(installation_context=installation_context)
        elif args.skip_check:
            app = MainApp(skip_check=args.skip_check)
        elif done_checks:
            app = MainApp(done_checks=done_checks)
        else:
            app = MainApp()
        
        app.mainloop()
        
    except BeanieDeployError as e:
        if logger:
            logger.error(f"Application error: {e}")
        else:
            print(f"Error during startup: {e}")
        get_error_handler().handle_error(e, "main")
        raise
    except Exception as e:
        if logger:
            logger.exception(f"Unexpected error: {e}")
        else:
            print(f"Unexpected error during startup: {e}")
        get_error_handler().handle_error(e, "main")
        raise


if __name__ == "__main__":
    # Initialize error handling
    error_handler = get_error_handler()
    logger = get_logger()
    
    args = parse_arguments()
    
    # Auto-detect release mode for PyInstaller builds
    is_pyinstaller_bundle = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
    is_release_mode = args.release or is_pyinstaller_bundle
    
    if is_release_mode:
        try:
            run()
        except Exception as e:
            logger.error(f"Application failed in release mode: {e}")
            # In release mode, fail silently to avoid showing errors to end users
            sys.exit(1)
    else:
        # Development mode - show errors and keep console open
        if is_admin():
            try:
                run()
            except Exception as e:
                logger.exception("Application failed in debug mode")
                print(f"\nError: {e}")
                print(traceback.format_exc())
            finally:
                input("Press Enter to exit...")
        else:
            try:
                run()
            except Exception as e:
                logger.exception("Application failed without admin privileges")
                print(f"\nError: {e}")
                input("Press Enter to exit...")
