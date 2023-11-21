import argparse
import logging
import multilingual
import globals as GV
import procedure as prc
import tkinter_templates as tkt
import functions as fn
import tkinter.messagebox

app = None

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-check", action="store_true", help="Skip the check")
    args = parser.parse_args()
    return args

def run():
    """
    Run the application.

    This function initializes the application by parsing command line arguments and setting up the necessary resources. 
    It then requests elevation (admin) if the application is not already running as admin. After that, it logs the starting 
    of the application, prints an important message to the console, initializes the necessary paths, initializes tkinter, 
    creates the required directories, builds the main GUI frames, and runs the page check. Finally, it starts the main event 
    loop of the application.
    """
    skip_check= False
    args = parse_arguments()
    if args.skip_check:
        skip_check = True
    fn.get_admin()  # Request elevation (admin) if not running as admin
    global app
    logging.info('APP STARTING: %s v%s' % (GV.APP_SW_NAME, GV.APP_SW_VERSION))
    print('################################################################\n'
          'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
          '################################################################\n\n')
    prc.init_paths(GV.PATH)
    app = tkt.init_tkinter(GV.APP_SW_NAME, GV.PATH.APP_ICON)  # initialize tkinter
    fn.mkdir(GV.PATH.WORK_DIR)
    TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(app)
    #tk.Label(LEFT_FRAME, image=tk.PhotoImage(file=GV.PATH.CURRENT_DIR + r'\resources\style\left_frame.gif')).pack()
    multilingual.set_lang("English")
    import page_check
    page_check.run(MID_FRAME, skip_check)
    app.mainloop()

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        # show a pop-up window with the error message
        message = tkinter.messagebox.showerror("Error", str(e))
