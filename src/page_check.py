import tkinter_templates as tkt
import globals as GV
import functions as fn
import procedure as prc
import gui_functions as gui
import logging
from page_manager import Page
import tkinter as tk


class PageCheck(Page):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.job_var = tk.StringVar()
        self.done_checks = {}
        self.skip_check = False

    def set_done_checks(self, done_checks):
        self.done_checks = done_checks

    def set_skip_check(self, skip_check):
        self.skip_check = skip_check

    def init_page(self):
        page_frame = tkt.generic_page_layout(self, self.LN.check_running)
        self.progressbar_check = tkt.add_progress_bar(page_frame)
        tkt.add_text_label(page_frame, var=self.job_var, pady=0, padx=10)
        self.update()

        def callback_compatibility(result):
            if result == "arch":
                self.progressbar_check["value"] = 10
            elif result == "uefi":
                self.job_var.set(self.LN.check_uefi)
                self.progressbar_check["value"] = 20
            elif result == "ram":
                self.job_var.set(self.LN.check_ram)
                self.progressbar_check["value"] = 30
            elif result == "space":
                self.progressbar_check["value"] = 50
                self.job_var.set(self.LN.check_space)
            elif result == "get_admin":
                args_list = [
                    f"--check_{key} {value}"
                    for key, value in vars(GV.COMPATIBILITY_RESULTS).items()
                ]
                args_string = " ".join(args_list)
                fn.get_admin(args_string)
            elif result == "resizable":
                self.job_var.set(self.LN.check_resizable)
                self.progressbar_check["value"] = 80
                # get available spins and ip location data once the last test begins
                gui.run_async_function(
                    fn.get_json,
                    kwargs={"url": GV.APP_AVAILABLE_SPINS_LIST, "named": "spin_list"},
                )
                gui.run_async_function(
                    fn.get_json,
                    kwargs={"url": GV.APP_FEDORA_GEO_IP_URL, "named": "geo_ip"},
                )

            elif isinstance(result, list) and result[0] == "compatibility_result":
                setattr(GV.COMPATIBILITY_RESULTS, result[1], result[2])
                self.job_var.set(self.LN.check_available_downloads)
            elif isinstance(result, tuple) and result[0] == "spin_list":
                GV.ALL_SPINS = result[1]
            elif isinstance(result, tuple) and result[0] == "geo_ip":
                GV.IP_LOCALE = result[1]
            if GV.ALL_SPINS and (
                self.skip_check
                or set(required_checks).issubset(
                    set(vars(GV.COMPATIBILITY_RESULTS).keys())
                )
            ):
                return 1

        if not self.skip_check:
            compatibility_results = prc.CompatibilityResult()
            required_checks = list(
                set(compatibility_results.checks) - set(self.done_checks)
            )
            gui.run_async_function(
                compatibility_results.compatibility_test,
                kwargs={"check_order": required_checks},
            )
        else:
            gui.run_async_function(
                fn.get_json,
                kwargs={"url": GV.APP_AVAILABLE_SPINS_LIST, "named": "spin_list"},
            )
            gui.run_async_function(
                fn.get_json, kwargs={"url": GV.APP_FEDORA_GEO_IP_URL, "named": "geo_ip"}
            )

        self.job_var.set(self.LN.check_available_downloads)
        gui.handle_queue_result(tkinter=self, callback=callback_compatibility)

        for check, result in self.done_checks.items():
            setattr(GV.COMPATIBILITY_RESULTS, check, result)
        # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
        # LOG #########################################################
        log = "\nInitial Test completed, results:"
        for key, value in vars(GV.COMPATIBILITY_RESULTS).items():
            log += "\n --> %s: %s" % (str(key), str(value))
        logging.info(log)
        if fn.detect_nvidia():
            logging.info("\nNote: NVIDIA Graphics card detected")
        # #############################################################
        errors = []
        if not self.skip_check:
            if GV.COMPATIBILITY_RESULTS.arch == -1:
                errors.append(self.LN.error_arch_9)
            elif GV.COMPATIBILITY_RESULTS.arch not in GV.ACCEPTED_ARCHITECTURES:
                errors.append(self.LN.error_arch_0)
            if GV.COMPATIBILITY_RESULTS.uefi == -1:
                errors.append(self.LN.error_uefi_9)
            elif GV.COMPATIBILITY_RESULTS.uefi != "uefi":
                errors.append(self.LN.error_uefi_0)
            if GV.COMPATIBILITY_RESULTS.ram == -1:
                errors.append(self.LN.error_totalram_9)
            elif GV.COMPATIBILITY_RESULTS.ram < GV.APP_MINIMAL_REQUIRED_RAM:
                errors.append(self.LN.error_totalram_0)
            if GV.COMPATIBILITY_RESULTS.space == -1:
                errors.append(self.LN.error_space_9)
            elif GV.COMPATIBILITY_RESULTS.space < GV.APP_MINIMAL_REQUIRED_SPACE:
                errors.append(self.LN.error_space_0)
            if GV.COMPATIBILITY_RESULTS.resizable == -1:
                errors.append(self.LN.error_resizable_9)
            elif GV.COMPATIBILITY_RESULTS.resizable < GV.APP_MINIMAL_REQUIRED_SPACE:
                errors.append(self.LN.error_resizable_0)
        if not errors:
            live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(GV.ALL_SPINS)
            if live_os_installer_index is not None:
                GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[live_os_installer_index]
            GV.USERNAME_WINDOWS = fn.get_windows_username()
            self.switch_page("Page1")
        else:
            self.master.pages["PageError"].set_errors(errors)
            self.switch_page("PageError")
