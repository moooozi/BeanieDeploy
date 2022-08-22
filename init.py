import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import procedure as prc


app = tkt.init_tkinter(GV.APP.SW_NAME)  # initialize tkinter
prc.init_paths(GV.PATH)
tkt.stylize(app, theme_dir=GV.PATH.CURRENT_DIR + '/resources/style/theme/azure-dark.tcl', theme_name='azure')  # use tkinter theme
#   MAIN CONTAINER & FRAMES   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /   /
CONTAINER = ttk.Frame(app)
CONTAINER.pack()
TOP_FRAME, MID_FRAME, LEFT_FRAME = tkt.build_main_gui_frames(CONTAINER)
ttk.Label(LEFT_FRAME, image=tk.PhotoImage(file=GV.PATH.CURRENT_DIR + r'\resources\left_frame.gif')).pack()
