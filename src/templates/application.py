from tkinter_templates import *


class Application(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # windll.shcore.SetProcessDpiAwareness(1)
        dpi_factor = get_dpi_scaling_factor()
        self.geometry(str("%sx%s+%s+%s" % (WIDTH, HEIGHT, WIDTH_OFFSET, HEIGHT_OFFSET)))
        self.minsize(MINWIDTH, MINHEIGHT)
        self.maxsize(int(MAXWIDTH * dpi_factor), int(MAXHEIGHT * dpi_factor))
        self.iconbitmap(GV.PATH.APP_ICON)

        # ctk.tk.call('tk', 'scaling', 1.4)
        # ctk.resizable(False, False)

        # top_frame.grid_propagate(False)

        dark_theme(DARK_MODE, self)

        ####
        ###Treeview Customisation (theme colors are selected)
        bg_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
        )
        text_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )
        selected_color = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        )

        treestyle = ttk.Style()
        treestyle.theme_use("default")
        treestyle.configure(
            "Treeview",
            background=bg_color,
            foreground=text_color,
            fieldbackground=bg_color,
            borderwidth=0,
        )
        treestyle.map(
            "Treeview",
            background=[("selected", bg_color)],
            foreground=[("selected", selected_color)],
        )
        self.bind("<<TreeviewSelect>>", lambda event: self.focus_set())

    def wait_and_handle_queue_output(
        self,
        output_queue: multiprocessing.Queue,
        callback,
        frequency=100,
        retry_count=0,
    ):
        try:
            while not output_queue.empty():
                output = output_queue.get_nowait()
                callback(output)
        except queue.Empty:
            if retry_count:
                self.after(
                    frequency,
                    self.wait_and_handle_queue_output,
                    output_queue,
                    callback,
                    frequency,
                    retry_count - 1,
                )
