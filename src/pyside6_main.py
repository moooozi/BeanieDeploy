import argparse
import os
import pickle
import traceback
import sys
from pathlib import Path
from typing import Optional

from translations import ar

# Handle PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)  # type: ignore
    # Add the bundle directory to Python path so translations can be found
    sys.path.insert(0, str(bundle_dir))
else:
    # Running in normal Python environment
    bundle_dir = Path(__file__).parent

# Import our new systems
from config.settings import get_config
from utils.logging import setup_logging, get_logger
from utils.errors import BeanieDeployError
from core.state import get_state_manager
from models.installation_context import InstallationContext

# Legacy imports (to be refactored)
import multilingual
from services.system import cleanup_on_reboot, windows_language_code

# PySide6 specific imports
from pyside6_app import PySide6MainApp, create_pyside6_app


def parse_arguments():
    """Parse command line arguments."""
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


def run_pyside6():
    """
    Run the PySide6 version of the application.
    
    This is the new main entry point for the PySide6 version.
    Much cleaner than the CustomTkinter version because Qt handles:
    - Better error handling
    - Proper application lifecycle
    - Built-in message loops
    - Cross-platform consistency
    """
    logger = None
    app = None
    
    try:
        # Set up the working directory
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Initialize configuration and logging
        config = get_config()
        logger = setup_logging(
            level="DEBUG",
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
            args.skip_check = True
            logger.info("Running in development mode")

        skip_check = args.skip_check
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
        
        # Set up language (legacy system)
        try:
            lang_code = windows_language_code()
            if lang_code in multilingual.available_languages:
                multilingual.set_lang(lang_code)
            else:
                multilingual.set_lang("English")
            logger.info(f"Language set to: {lang_code}")
        except Exception as e:
            logger.warning(f"Failed to set up language: {e}")
            multilingual.set_lang("English")
        
        # Create PySide6 application
        app = create_pyside6_app()
        
        # Create main window
        main_window = PySide6MainApp(
            skip_check=skip_check,
            done_checks=done_checks,
            installation_context=installation_context
        )
        
        # Show the main window
        main_window.show()
        
        # Log successful startup
        logger.info("PySide6 application started successfully")
        
        # Start the Qt event loop
        return app.exec()
        
    except BeanieDeployError as e:
        if logger:
            logger.error(f"Application error: {str(e)}")
        return 1
        
    except Exception as e:
        error_msg = f"Unexpected error during startup: {str(e)}"
        if logger:
            logger.error(error_msg)
            logger.error(traceback.format_exc())
        else:
            print(f"FATAL ERROR: {error_msg}")
            traceback.print_exc()
        
        # Show error dialog if Qt app is available
        if app:
            from PySide6.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("BeanieDeploy - Fatal Error")
            msg_box.setText("A fatal error occurred during startup.")
            msg_box.setDetailedText(f"{error_msg}\n\n{traceback.format_exc()}")
            msg_box.exec()
        
        return 1
    
    finally:
        # Cleanup
        try:
            # Parse arguments again for cleanup (in case of early failure)
            args = parse_arguments()
            if hasattr(args, 'checks_dumb') and args.checks_dumb:
                args.checks_dumb.close()
            if hasattr(args, 'installation_context') and args.installation_context:
                args.installation_context.close()
        except:
            pass  # Ignore errors during cleanup
        
        try:
            cleanup_on_reboot("")  # Pass empty string as placeholder
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    # Run the PySide6 version
    exit_code = run_pyside6()
    sys.exit(exit_code)