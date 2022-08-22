import multiprocessing
import tkinter as tk
import installation
import page_restart_required
import tkinter_templates as tkt
import globals as GV
import translations.en as LN
from init import MID_FRAME, app
import gui_functions as gui


def run(installer_kwargs, installer_img_dl_percent_factor: float, live_img_dl_factor: float = 0, queue=multiprocessing.Queue()):
    """the page on which the initial installation (creating bootable media) takes place"""
    tkt.clear_frame(MID_FRAME)
    # *************************************************************************************************************
    tkt.add_page_title(MID_FRAME, LN.install_running)
    progressbar_install = tkt.add_progress_bar(MID_FRAME)
    job_var = tk.StringVar(app)
    tkt.add_text_label(MID_FRAME, var=job_var, pady=0, padx=10)
    # INSTALL STARTING

    progressbar_install['value'] = 0
    app.update()

    def callback(queue_result):
        if queue_result == 'APP: critical_process_running':
            app.protocol("WM_DELETE_WINDOW", False)  # prevent closing the app during partition
        elif queue_result == 'APP: critical_process_done':
            app.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
        elif queue_result == 'STAGE: downloading':
            job_var.set(LN.job_starting_download)
        elif queue_result == 'STAGE: verifying_checksum':
            job_var.set(LN.job_checksum)
        elif queue_result == 'STAGE: creating_tmp_part':
            job_var.set(LN.job_creating_tmp_part)
            progressbar_install['value'] = 92
        elif queue_result == 'STAGE: copying_to_tmp_part':
            job_var.set(LN.job_copying_to_tmp_part)
            progressbar_install['value'] = 94
        elif queue_result == 'STAGE: adding_tmp_boot_entry':
            job_var.set(LN.job_adding_tmp_boot_entry)
            progressbar_install['value'] = 98
        elif queue_result == 'STAGE: install_done':
            return 1
        elif isinstance(queue_result, tuple) and queue_result[0] == 'ARIA2C: Tracking %s' % installer_kwargs.installer_iso_name:
            result = queue_result[1]
            progressbar_install['value'] = result['%'] * installer_img_dl_percent_factor
            job_var.set(LN.job_dl_install_media + '\n%s\n%s: %s/s, %s: %s' % (result['size'], LN.dl_speed,
                                                                              result['speed'],
                                                                              LN.dl_timeleft,
                                                                              result['eta']))
        elif isinstance(queue_result, tuple) and queue_result[0] == 'ARIA2C: Tracking %s' % installer_kwargs.live_img_iso_name:
            result = queue_result[1]
            progressbar_install['value'] = result['%'] * live_img_dl_factor
            job_var.set(LN.job_dl_install_media + '\n%s\n%s: %s/s, %s: %s' % (result['size'], LN.dl_speed,
                                                                              result['speed'],
                                                                              LN.dl_timeleft,
                                                                              result['eta']))
    job_var.set(LN.check_existing_download_files)
    gui.run_async_function(app, installation.install, kwargs=vars(installer_kwargs), callback=callback, queue=queue)
    return page_restart_required.run()
