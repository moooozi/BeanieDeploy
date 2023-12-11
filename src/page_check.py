import tkinter_templates as tkt
import globals as GV
import multilingual
import functions as fn
import procedure as prc
import page_app_lang, page_error
import gui_functions as gui
import logging

import global_tk_vars as tk_var



def run(app, skip_check=False, done_checks : dict = {}):
    """The page on which is decided whether the app can run on the device or not"""
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    app.update()  # update tkinter GUI
    page_frame = tkt.generic_page_layout(app, LN.check_running)
    progressbar_check = tkt.add_progress_bar(page_frame)
    tkt.add_text_label(page_frame, var=tk_var.job_var, pady=0, padx=10)
    def callback_compatibility(result):
        tk_var.job_var.set(LN.check_available_downloads)
        if result == 'arch':
            progressbar_check['value'] = 10
        elif result == 'uefi':
            tk_var.job_var.set(LN.check_uefi)
            progressbar_check['value'] = 20
        elif result == 'ram':
            tk_var.job_var.set(LN.check_ram)
            progressbar_check['value'] = 30
        elif result == 'space':
            progressbar_check['value'] = 50
            tk_var.job_var.set(LN.check_space)
        elif result == 'get_admin':
            args_list = [f"--check_{key} {value}" for key, value in vars(GV.COMPATIBILITY_RESULTS).items()]
            args_string = " ".join(args_list)
            fn.get_admin(args_string)
        elif result == 'resizable':
            tk_var.job_var.set(LN.check_resizable)
            progressbar_check['value'] = 80
            # get available spins and ip location data once the last test begins
            gui.run_async_function(fn.get_json, kwargs={'url': GV.APP_AVAILABLE_SPINS_LIST, 'named': 'spin_list'})
            gui.run_async_function(fn.get_json, kwargs={'url': GV.APP_FEDORA_GEO_IP_URL, 'named': 'geo_ip'})

        elif isinstance(result, list) and result[0] == 'compatibility_result':
            setattr(GV.COMPATIBILITY_RESULTS, result[1], result[2])
            tk_var.job_var.set(LN.check_available_downloads)
        elif isinstance(result, tuple) and result[0] == 'spin_list':
            GV.ALL_SPINS = result[1]
        elif isinstance(result, tuple) and result[0] == 'geo_ip':
            GV.IP_LOCALE = result[1]
        if GV.ALL_SPINS and (skip_check or set(required_checks).issubset(set(vars(GV.COMPATIBILITY_RESULTS).keys()))):
            return 1

    if not skip_check:
        compatibility_results = prc.CompatibilityResult()
        required_checks = [x for x in compatibility_results.checks if x not in done_checks]
        gui.run_async_function(compatibility_results.compatibility_test, kwargs={'check_order': required_checks})
    else:
        gui.run_async_function(fn.get_json, kwargs={'url': GV.APP_AVAILABLE_SPINS_LIST, 'named': 'spin_list'})
        gui.run_async_function(fn.get_json, kwargs={'url': GV.APP_FEDORA_GEO_IP_URL, 'named': 'geo_ip'})

    gui.handle_queue_result(tkinter=app, callback=callback_compatibility)

    for check, result in done_checks.items():
        setattr(GV.COMPATIBILITY_RESULTS, check, result)
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
    if not skip_check:
        if GV.COMPATIBILITY_RESULTS.arch == -1:
            errors.append(LN.error_arch_9)
        elif GV.COMPATIBILITY_RESULTS.arch not in GV.ACCEPTED_ARCHITECTURES:
            errors.append(LN.error_arch_0)
        if GV.COMPATIBILITY_RESULTS.uefi == -1:
            errors.append(LN.error_uefi_9)
        elif GV.COMPATIBILITY_RESULTS.uefi != 'uefi':
            errors.append(LN.error_uefi_0)
        if GV.COMPATIBILITY_RESULTS.ram == -1:
            errors.append(LN.error_totalram_9)
        elif GV.COMPATIBILITY_RESULTS.ram < GV.APP_minimal_required_ram:
            errors.append(LN.error_totalram_0)
        if GV.COMPATIBILITY_RESULTS.space == -1:
            errors.append(LN.error_space_9)
        elif GV.COMPATIBILITY_RESULTS.space < GV.APP_minimal_required_space:
            errors.append(LN.error_space_0)
        if GV.COMPATIBILITY_RESULTS.resizable == -1:
            errors.append(LN.error_resizable_9)
        elif GV.COMPATIBILITY_RESULTS.resizable < GV.APP_minimal_required_space:
            errors.append(LN.error_resizable_0)
    if not errors:
        live_os_installer_index, GV.ACCEPTED_SPINS = prc.parse_spins(GV.ALL_SPINS)
        if live_os_installer_index is not None:
            GV.LIVE_OS_INSTALLER_SPIN = GV.ACCEPTED_SPINS[live_os_installer_index]
        GV.USERNAME_WINDOWS = fn.get_windows_username()
        return page_app_lang.run(app)
    else:
        page_error.run(app, errors)
