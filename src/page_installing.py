import pathlib
import pickle
import time
import multiprocessing
import installation
import page_restart_required
import tkinter_templates as tkt
import multilingual
import gui_functions as gui
import global_tk_vars as tk_var
import functions as fn


def run(app, installer_args, queue=multiprocessing.Queue()):
    """the page on which the initial installation (creating bootable media) takes place"""
    app.update()
    tkt.init_frame(app)
    global LN, DI_VAR
    LN = multilingual.get_lang()
    DI_VAR = multilingual.get_di_var()
    # *************************************************************************************************************
    page_frame = tkt.generic_page_layout(app, LN.install_running)
    progressbar_install = tkt.add_progress_bar(page_frame)
    tkt.add_text_label(page_frame, var=tk_var.install_job_var, pady=0, padx=10)
    # INSTALL STARTING
    master = gui.get_first_tk_parent(app)
    progressbar_install["value"] = 0
    app.update()

    if not fn.is_admin():
        with open("install_args.pkl", "wb") as file:
            pickle.dump(installer_args, file)
        installer_args_path = pathlib.Path("install_args.pkl").absolute()
        fn.get_admin(f'--install_args "{installer_args_path}"')
        return 0

    # GUI Logic
    # Tracking downloads
    file_index = 0
    current_dl_file_name = "NONE"
    current_dl_file_size = 0
    current_dl_file_percent_factor = 0
    global_downloads_factor = (
        0.90  # When all downloads are complete, the progressbar will be at 90%
    )
    total_already_downloaded = 0
    already_downloaded_percent = 0
    total_download_size = 0

    num_of_files = 0
    for file in installer_args.dl_files:
        num_of_files += 1
        total_download_size += file.size

    def gui_update_callback(queue_result):
        if queue_result == "APP: critical_process_running":
            master.protocol(
                "WM_DELETE_WINDOW", False
            )  # prevent closing the app during partition
        elif queue_result == "APP: critical_process_done":
            master.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
        elif queue_result == "STAGE: downloading":
            tk_var.install_job_var.set(LN.job_starting_download)
        elif queue_result == "STAGE: verifying_checksum":
            tk_var.install_job_var.set(LN.job_checksum)
        elif queue_result == "STAGE: creating_tmp_part":
            tk_var.install_job_var.set(LN.job_creating_tmp_part)
            progressbar_install["value"] = 92
        elif queue_result == "STAGE: copying_to_tmp_part":
            tk_var.install_job_var.set(LN.job_copying_to_tmp_part)
            progressbar_install["value"] = 94
        elif queue_result == "STAGE: adding_tmp_boot_entry":
            tk_var.install_job_var.set(LN.job_adding_tmp_boot_entry)
            progressbar_install["value"] = 98
        elif queue_result == "STAGE: install_done":
            return 1
        elif (
            isinstance(queue_result, dict)
            and "type" in queue_result.keys()
            and queue_result["type"] == "dl_tracker"
        ):
            nonlocal file_index, current_dl_file_name, current_dl_file_size, current_dl_file_percent_factor
            nonlocal total_already_downloaded, already_downloaded_percent
            if queue_result["file_name"] != current_dl_file_name:
                total_already_downloaded += current_dl_file_size
                already_downloaded_percent = (
                    total_already_downloaded / total_download_size
                ) * 100
                file_index += 1
                for file in installer_args.dl_files:
                    if queue_result["file_name"] != file.file_name:
                        continue
                    current_dl_file_name = file.file_name
                    current_dl_file_size = file.size
                    current_dl_file_percent_factor = file.size / total_download_size
                    break
            if queue_result["status"] == "complete":
                pass
            elif queue_result["status"] == "downloading":
                progressbar_install["value"] = (
                    (queue_result["%"] * current_dl_file_percent_factor)
                    + already_downloaded_percent
                ) * global_downloads_factor

                formatted_speed = fn.format_speed(float(queue_result["speed"]))
                formatted_eta = fn.format_eta(float(queue_result["eta"])).format(
                    ln_hour=LN.eta_hour,
                    ln_minute=LN.eta_minute,
                    ln_second=LN.eta_second,
                    ln_left=LN.eta_left,
                )
                formatted_size = fn.format_size(float(queue_result["size"]))

                tk_var.install_job_var.set(
                    LN.job_dl_install_media
                    + f"\n{LN.downloads_number % (file_index, num_of_files)}"
                    f"\n{LN.dl_file_size}: {formatted_size}"
                    f"\n{LN.dl_speed}: {formatted_speed}"
                    f"\n{LN.dl_timeleft}: {formatted_eta}"
                )

        elif isinstance(queue_result, tuple) and queue_result[0] == "ERR: checksum":
            error_dict = queue_result[1]
            response_queue = queue
            print(error_dict)
            response = gui_download_hash_handler(app.master, **error_dict)
            response_queue.put(response)
            time.sleep(1)
            # Now exit the front end
            if response["app_quit"]:
                raise SystemExit

    tk_var.install_job_var.set(LN.check_existing_download_files)
    gui.run_async_function(
        installation.install, kwargs=vars(installer_args), queue=queue
    )
    gui.handle_queue_result(tkinter=app, callback=gui_update_callback, queue=queue)
    return page_restart_required.run(app)


def gui_download_hash_handler(master, error, file_hash="", expected_hash=""):
    go_next = False
    cleanup = False
    app_quit = False
    if error == "failed":
        question = tkt.input_pop_up(
            parent=master,
            title_txt=LN.job_checksum_failed,
            msg_txt=LN.job_checksum_failed_txt,
            primary_btn_str=LN.btn_yes,
            secondary_btn_str=LN.btn_no,
        )
        if question:
            go_next = True
        else:
            question = tkt.input_pop_up(
                parent=master,
                title_txt=LN.cleanup_question,
                msg_txt=LN.cleanup_question_txt,
                primary_btn_str=LN.btn_yes,
                secondary_btn_str=LN.btn_no,
            )
            if question:
                cleanup = True
            app_quit = True
    if error == "mismatch":
        question = tkt.input_pop_up(
            parent=master,
            title_txt=LN.job_checksum_mismatch,
            msg_txt=LN.job_checksum_mismatch_txt % (file_hash, expected_hash),
            primary_btn_str=LN.btn_retry,
            secondary_btn_str=LN.btn_abort,
        )
        if not question:
            question = tkt.input_pop_up(
                parent=master,
                title_txt=LN.cleanup_question,
                msg_txt=LN.cleanup_question_txt,
                primary_btn_str=LN.btn_yes,
                secondary_btn_str=LN.btn_no,
            )
            if question:
                cleanup = True
            app_quit = True
    return {"go_next": go_next, "cleanup": cleanup, "app_quit": app_quit}
