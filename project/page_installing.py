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
    tkt.init_frame(MID_FRAME)
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(MID_FRAME, LN.install_running)
    progressbar_install = tkt.add_progress_bar(page_frame)
    job_var = tk.StringVar(app)
    tkt.add_text_label(page_frame, var=job_var, pady=0, padx=10)
    # INSTALL STARTING

    progressbar_install['value'] = 0
    app.update()

    def gui_update_callback(queue_result):
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
        elif isinstance(queue_result, tuple) and queue_result[0] in ('STAGE: checksum_failed', 'STAGE: checksum_mismatch'):
            hash_result = queue_result[1]
            response_queue = queue_result[2]
            response = download_hash_handler(hash_result)
            response_queue.put(response)

    job_var.set(LN.check_existing_download_files)
    gui.run_async_function(installation.install, kwargs=vars(installer_kwargs), queue=queue)
    gui.handle_queue_result(tkinter=app, callback=gui_update_callback, queue=queue)
    return page_restart_required.run()


def download_hash_handler(dl_hash):
    go_next = False
    cleanup = False
    app_quit = False
    if dl_hash == -1:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_failed,
                                  msg_txt=LN.job_checksum_failed_txt,
                                  primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
        if question:
            go_next = True
        else:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                cleanup = True
            app_quit = True
    else:
        question = tkt.open_popup(parent=app, title_txt=LN.job_checksum_mismatch,
                                  msg_txt=LN.job_checksum_mismatch_txt % dl_hash,
                                  primary_btn_str=LN.btn_retry, secondary_btn_str=LN.btn_abort)
        if not question:
            question = tkt.open_popup(parent=app, title_txt=LN.cleanup_question,
                                      msg_txt=LN.cleanup_question_txt,
                                      primary_btn_str=LN.btn_yes, secondary_btn_str=LN.btn_no)
            if question:
                cleanup = True
            app_quit = False
    return {'go_next': go_next, 'cleanup': cleanup, 'app_quit': app_quit}
