import tkinter as tk
import tkinter.ttk as ttk
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
import functions as fn
import procedure as prc
import page_1, page_error
import gui_functions as gui
from init import app as tkinter, MID_FRAME, logging


def run(compatibility_test=True):
    """The page on which is decided whether the app can run on the device or not"""
    tkt.clear_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.check_running)
    progressbar_check = tkt.add_progress_bar(page_frame)
    job_var = tk.StringVar()
    tkt.add_text_label(page_frame, var=job_var, pady=0, padx=10)
    tkinter.update()  # update tkinter GUI
    if not compatibility_test:
        GV.COMPATIBILITY_RESULTS.uefi = 1
        GV.COMPATIBILITY_RESULTS.ram = 34359738368
        GV.COMPATIBILITY_RESULTS.space = 133264248832
        GV.COMPATIBILITY_RESULTS.resizable = 432008358400
        GV.COMPATIBILITY_RESULTS.arch = 'amd64'

    def callback_compatibility(result):
        if result == 'arch':
            progressbar_check['value'] = 10
        elif result == 'uefi':
            job_var.set(LN.check_uefi)
            progressbar_check['value'] = 20
        elif result == 'ram':
            job_var.set(LN.check_ram)
            progressbar_check['value'] = 30
        elif result == 'space':
            job_var.set(LN.check_space)
            progressbar_check['value'] = 50
        elif result == 'resizable':
            job_var.set(LN.check_resizable)
            progressbar_check['value'] = 80
        elif isinstance(result, dict) and result.keys() >= {"arch", "uefi"}:
            GV.COMPATIBILITY_RESULTS.__init__(**result)
            job_var.set(LN.check_available_downloads)
            progressbar_check['value'] = 95
        elif isinstance(result, tuple) and result[0] == 'spin_list':
            GV.ALL_SPINS = result[1]
        elif isinstance(result, tuple) and result[0] == 'geo_ip':
            GV.IP_LOCALE = result[1]
        if GV.ALL_SPINS and vars(GV.COMPATIBILITY_RESULTS):
            return 1

    if not vars(GV.COMPATIBILITY_RESULTS):
        fn.get_admin()  # Request elevation (admin) if not running as admin
        gui.run_async_function(prc.compatibility_test, args=(GV.APP.minimal_required_space,))
    if not GV.ALL_SPINS:
        gui.run_async_function(fn.get_json, kwargs={'url': GV.APP.AVAILABLE_SPINS_LIST, 'named': 'spin_list'})
    if not GV.IP_LOCALE:
        gui.run_async_function(fn.get_json, kwargs={'url': GV.APP.FEDORA_GEO_IP_URL, 'named': 'geo_ip'})

    gui.handle_queue_result(tkinter=tkinter, callback=callback_compatibility)
    # Try to detect GEO-IP locale while compatibility check is running. Timeout once check has finished
    # LOG #########################################################
    log = '\nInitial Test completed, results:'
    for key, value in vars(GV.COMPATIBILITY_RESULTS).items():
        log += '\n --> %s: %s' % (str(key), str(value))
    logging.info(log)
    if fn.detect_nvidia():
        logging.info('\nNote: NVIDIA Graphics card detected')
    # #############################################################
    errors = []
    if GV.COMPATIBILITY_RESULTS.arch == -1:
        errors.append(LN.error_arch_9)
    elif GV.COMPATIBILITY_RESULTS.arch not in GV.ACCEPTED_ARCHITECTURES:
        errors.append(LN.error_arch_0)
    if GV.COMPATIBILITY_RESULTS.uefi == -1:
        errors.append(LN.error_uefi_9)
    elif GV.COMPATIBILITY_RESULTS.uefi != 1:
        errors.append(LN.error_uefi_0)
    if GV.COMPATIBILITY_RESULTS.ram == -1:
        errors.append(LN.error_totalram_9)
    elif GV.COMPATIBILITY_RESULTS.ram < GV.APP.minimal_required_ram:
        errors.append(LN.error_totalram_0)
    if GV.COMPATIBILITY_RESULTS.space == -1:
        errors.append(LN.error_space_9)
    elif GV.COMPATIBILITY_RESULTS.space < GV.APP.minimal_required_space:
        errors.append(LN.error_space_0)
    if GV.COMPATIBILITY_RESULTS.resizable == -1:
        errors.append(LN.error_resizable_9)
    elif GV.COMPATIBILITY_RESULTS.resizable < GV.APP.minimal_required_space:
        errors.append(LN.error_resizable_0)

    if not errors:
        live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(GV.ALL_SPINS)
        if live_os_installer_index is not None:
            GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[live_os_installer_index]
        GV.USERNAME_WINDOWS = fn.get_windows_username()
        return page_1.run()
    else:
        page_error.run(errors)



