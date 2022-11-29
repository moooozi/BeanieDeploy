import logging
import globals as GV
import procedure as prc
import tkinter_templates as tkt
import functions as fn
app = None

if __name__ == '__main__':
    logging.info('APP STARTING: %s v%s' % (GV.APP_SW_NAME, GV.APP_SW_VERSION))
    print('################################################################\n'
          'IMPORTANT: DO NOT CLOSE THIS CONSOLE WINDOW WHILE APP IS RUNNING\n'
          '################################################################\n\n')
    prc.init_paths(GV.PATH)
    app = tkt.init_tkinter(GV.APP_SW_NAME)  # initialize tkinter
    import __main__
    __main__.app = app
    fn.mkdir(GV.PATH.WORK_DIR)
    TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(app)
    #tk.Label(LEFT_FRAME, image=tk.PhotoImage(file=GV.PATH.CURRENT_DIR + r'\resources\style\left_frame.gif')).pack()
    import page_check
    page_check.run(MID_FRAME, False)
    app.mainloop()


