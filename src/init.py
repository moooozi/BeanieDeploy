import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import procedure as prc
import functions as fn
import logging
prc.init_paths(GV.PATH)
app = tkt.init_tkinter(GV.APP_SW_NAME)  # initialize tkinter
fn.mkdir(GV.PATH.WORK_DIR)
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = ttk.Frame(app)
CONTAINER.pack(expand=True, fill='both')
TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(CONTAINER)
ttk.Label(LEFT_FRAME, image=tk.PhotoImage(file=GV.PATH.CURRENT_DIR + r'\resources\style\left_frame.gif')).pack()
Frames = {}
logging.basicConfig(
        filename=GV.PATH.WORK_DIR + '\\log_output.log',
        level=logging.INFO)
