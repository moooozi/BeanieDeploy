import argparse
import logging
import os
import pickle
import multilingual
import globals as GV
import functions as fn
import tkinter.messagebox
import traceback
from app import MainApp


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip_check", action="store_true", help="Skip the check")
    parser.add_argument(
        "--release", action="store_true", help="The App is in release mode"
    )
    parser.add_argument(
        "--check_arch",
        type=str,
    )
    parser.add_argument(
        "--check_uefi",
        type=str,
    )
    parser.add_argument(
        "--check_ram",
        type=str,
    )
    parser.add_argument(
        "--check_space",
        type=str,
    )
    parser.add_argument(
        "--check_resizable",
        type=str,
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
    install_args = None
    args = parse_arguments()
    if args.skip_check:
        skip_check = True

    done_checks = {}
    if args.check_arch:
        done_checks["arch"] = args.check_arch
    if args.check_uefi:
        done_checks["uefi"] = args.check_uefi
    if args.check_ram:
        done_checks["ram"] = int(args.check_ram)
    if args.check_space:
        done_checks["space"] = int(args.check_space)
    if args.check_resizable:
        done_checks["resizable"] = int(args.check_resizable)
    if args.app_version:
        GV.APP_SW_VERSION = args.app_version
    if args.install_args:
        install_args = pickle.load(args.install_args)
    if args.release:
        fn.cleanup_on_reboot(script_dir)
    else:
        import sys

        sys.argv.append("--skip_check")
        skip_check = True
        print("The App is in debug mode")
    logging.info("APP STARTING: %s v%s" % (GV.APP_SW_NAME, GV.APP_SW_VERSION))
    fn.mkdir(GV.PATH.WORK_DIR)
    # tk.Label(LEFT_FRAME, image=tk.PhotoImage(file=GV.PATH.CURRENT_DIR + r'\resources\style\left_frame.gif')).pack()
    lang_code = multilingual.get_lang_by_code(fn.windows_language_code())
    multilingual.set_lang(lang_code if lang_code else "English")

    if install_args:
        app = MainApp(install_args)
    elif skip_check:
        app = MainApp(skip_check=skip_check)
    elif done_checks:
        app = MainApp(done_checks)
    else:
        app = MainApp()

    app.mainloop()


if __name__ == "__main__":
    # run()
    if parse_arguments().release:
        try:
            run()
        except Exception as e:
            # show a pop-up window with the error message
            message = tkinter.messagebox.showerror(
                title="Error", message=traceback.format_exc()
            )
    else:
        run()
