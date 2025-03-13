import argparse
import logging
import os
import pickle
import time
import multilingual
import globals as GV
import functions as fn
import traceback
import sys
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
        "--install_args",
        type=argparse.FileType("rb"),
    )
    parser.add_argument(
        "--app_version",
        type=str,
    )
    args = parser.parse_args()
    return args


def run():
    """
    Run the application.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    skip_check = False
    args = parse_arguments()
    if args.skip_check:
        skip_check = True

    done_checks = None
    install_args = None

    if args.checks_dumb:
        done_checks = pickle.load(args.checks_dumb)
    if args.install_args:
        install_args = pickle.load(args.install_args)
    if args.app_version:
        GV.APP_SW_VERSION = args.app_version
    if args.release:
        fn.cleanup_on_reboot(script_dir)
    else:
        sys.argv.append("--skip_check")
        skip_check = True
        print("The App is in debug mode")
    logging.info("APP STARTING: %s v%s" % (GV.APP_SW_NAME, GV.APP_SW_VERSION))
    fn.mkdir(GV.PATH.WORK_DIR)
    lang_code = multilingual.get_lang_by_code(fn.windows_language_code())
    multilingual.set_lang(lang_code if lang_code else "English")

    if install_args:
        app = MainApp(install_args=install_args)
    elif skip_check:
        app = MainApp(skip_check=skip_check)
    elif done_checks:
        app = MainApp(done_checks=done_checks)
    else:
        app = MainApp()

    app.mainloop()


if __name__ == "__main__":
    # run()
    if parse_arguments().release:
        try:
            run()
        except Exception as e:
            pass
    else:
        if fn.is_admin():
            try:
                run()
            except:
                print(traceback.format_exc())
            finally:
                time.sleep(5)
        else:
            run()
