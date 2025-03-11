from dataclasses import dataclass, fields
import pathlib
import pickle
import queue
import tempfile
import time
from typing import List, Optional
import installation
from models.spin import Spin
import tkinter_templates as tkt
import gui_functions as gui
import functions as fn
import globals as GV
import procedure as prc
import logging
import types
import tkinter as tk
from page_manager import Page


@dataclass
class DownloadFile:
    file_name: str
    file_hint: str
    dl_link: str
    dst_dir: str
    hash256: str
    size: int

    @classmethod
    def from_spin(
        cls,
        spin: Spin,
        file_name=None,
        file_hint=None,
        dst_dir=None,
    ) -> "DownloadFile":
        return cls(
            file_name=file_name,
            file_hint=file_hint,
            dl_link=spin.dl_link,
            dst_dir=dst_dir,
            hash256=spin.hash256,
            size=spin.size,
        )


@dataclass
class InstallerArgs:
    work_dir: str = None
    dl_files: List[DownloadFile] = None
    ks_kwargs: dict = None
    part_kwargs: dict = None
    rpm_source_dir: str = None
    rpm_dst_dir_name: str = None
    wifi_profiles_src_dir: Optional[str] = None
    wifi_profiles_dst_dir_name: Optional[str] = None
    grub_cfg_relative_path: str = None
    tmp_partition_label: str = None
    kickstart_cfg_relative_path: str = None
    efi_file_relative_path: str = None


class PageInstalling(Page):
    def __init__(self, parent, installer_args=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.installer_args = installer_args
        self.queue = queue.Queue()
        self.install_job_var = tk.StringVar(parent)

    def init_page(self):
        self.update()
        if not self.installer_args:
            self.prepare()

        page_frame = tkt.generic_page_layout(self, self.LN.install_running)
        self.progressbar_install = tkt.add_progress_bar(page_frame)
        tkt.add_text_label(page_frame, var=self.install_job_var, pady=0, padx=10)
        # INSTALL STARTING
        master = gui.get_first_tk_parent(self)
        self.progressbar_install.set(0)
        self.update()

        if not fn.is_admin():
            with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as temp_file:
                pickle.dump(self.installer_args, temp_file)
                temp_file_path = pathlib.Path(temp_file.name).absolute()
            args_string = f'--install_args "{temp_file_path}"'
            fn.get_admin(args_string)
            return 0

        # GUI Logic
        # Tracking downloads
        self.file_index = 0
        self.current_dl_file_name = "NONE"
        self.current_dl_file_size = 0
        self.current_dl_file_percent_factor = 0
        self.global_downloads_factor = (
            0.90  # When all downloads are complete, the progressbar will be at 90%
        )
        self.total_already_downloaded = 0
        self.already_downloaded_percent = 0
        self.total_download_size = 0

        self.num_of_files = 0
        for file in self.installer_args.dl_files:
            self.num_of_files += 1
            self.total_download_size += file.size

        self.install_job_var.set(self.LN.check_existing_download_files)
        gui.run_async_function(
            installation.install, kwargs=vars(self.installer_args), queue=self.queue
        )
        gui.handle_queue_result(
            tkinter=self, callback=self.gui_update_callback, queue=self.queue
        )

    def set_installer_args(self, installer_args):
        print("Setting installer args")
        self.installer_args = installer_args

    def prepare(self):

        wifi_profiles = (
            self.get_wifi_profiles() if GV.INSTALL_OPTIONS.export_wifi else None
        )

        install_method = GV.KICKSTART.partition_method
        # creating new partition for root is only needed when installing alongside Windows
        GV.PARTITION.make_root_partition = (
            True if install_method == "dualboot" else False
        )
        # Only create separate boot partition if encryption is enabled
        GV.PARTITION.boot_part_size = 0
        # Do not create additional efi partition
        GV.PARTITION.efi_part_size = 0

        if GV.KICKSTART.partition_method != "custom":
            if GV.KICKSTART.is_encrypted:  # create separate boot partition
                GV.PARTITION.boot_part_size = GV.APP_LINUX_BOOT_PARTITION_SIZE
            GV.KICKSTART.ostree_args = GV.SELECTED_SPIN.ostree_args
            GV.KICKSTART.wifi_profiles_dir_name = GV.WIFI_PROFILES_DIR_NAME

            # LOG ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            log_kickstart = "\nKickstart arguments (sensitive data sensored):"
            for key, value in vars(GV.KICKSTART).items():
                if key in ("passphrase", "fullname", "username", "wifi_profiles"):
                    if not value:
                        continue
                    log_kickstart += "\n --> %s: (sensitive data)" % key
                else:
                    log_kickstart += "\n --> %s: %s" % (key, value)
            logging.info(log_kickstart)
            log_partition = "\nPartitioning details:"
            for key, value in vars(GV.PARTITION).items():
                log_partition += "\n --> %s: %s" % (key, value)
            logging.info(log_partition)
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        if GV.SELECTED_SPIN.is_live_img:
            installer_img = DownloadFile.from_spin(GV.LIVE_OS_INSTALLER_SPIN)
            live_img = DownloadFile.from_spin(GV.SELECTED_SPIN)
        else:
            installer_img = GV.SELECTED_SPIN
            live_img = None

        installer_args = InstallerArgs()
        installer_args.work_dir = GV.PATH.WORK_DIR

        installer_img.file_name = GV.INSTALL_ISO_NAME
        installer_img.file_hint = "installer_iso"
        installer_args.dl_files = [
            installer_img,
        ]

        if GV.SELECTED_SPIN.is_live_img:
            live_img.file_name = GV.LIVE_ISO_NAME
            live_img.file_hint = "live_img_iso"
            installer_args.dl_files.append(live_img)

        for index, file in enumerate(installer_args.dl_files):
            if not file.dl_link or not file.dl_link:
                raise ValueError(
                    "items in installer_args.dl_files must include valid dl_link"
                )
            if not file.file_name:
                file.file_name = fn.get_file_name_from_url(file.dl_link)
            if not file.dst_dir:
                file.dst_dir = GV.PATH.WORK_DIR
            if not file.hash256:
                file.hash256 = ""
            else:  # for consistency
                file.hash256 = file.hash256.strip().lower()
            if not file.size:
                file.size = 0

        installer_args.ks_kwargs = GV.KICKSTART
        installer_args.part_kwargs = GV.PARTITION
        installer_args.rpm_source_dir = GV.PATH.RPM_SOURCE_DIR
        installer_args.rpm_dst_dir_name = GV.ADDITIONAL_RPM_DIR_NAME
        installer_args.wifi_profiles_src_dir = (
            GV.PATH.WIFI_PROFILES_DIR if wifi_profiles else None
        )
        installer_args.wifi_profiles_dst_dir_name = (
            GV.WIFI_PROFILES_DIR_NAME if wifi_profiles else None
        )
        installer_args.grub_cfg_relative_path = GV.PATH.RELATIVE_GRUB_CFG
        installer_args.tmp_partition_label = GV.PARTITION.temp_part_label
        installer_args.kickstart_cfg_relative_path = GV.PATH.RELATIVE_KICKSTART
        installer_args.efi_file_relative_path = GV.APP_DEFAULT_EFI_FILE_PATH

        self.installer_args = installer_args

    def get_wifi_profiles(self):
        wifi_profiles = prc.get_wifi_profiles(GV.PATH.WIFI_PROFILES_DIR)
        with open(
            GV.PATH.CURRENT_DIR + "/resources/autoinst/wifi_network_file_template"
        ) as wifi_network_file_template:
            wifi_network_template = wifi_network_file_template.read().strip()
            for index, profile in enumerate(wifi_profiles):
                network_file = wifi_network_template.replace("%name%", profile["name"])
                network_file = network_file.replace("%ssid%", profile["ssid"])
                network_file = network_file.replace("%hidden%", profile["hidden"])
                network_file = network_file.replace("%password%", profile["password"])
                with open(
                    f"{GV.PATH.WIFI_PROFILES_DIR}\\imported_wifi{str(index)}.nmconnection",
                    "w",
                ) as wifi_profile:
                    wifi_profile.write(network_file)
        return wifi_profiles

    def gui_update_callback(self, queue_result):
        master = gui.get_first_tk_parent(self)
        if queue_result == "APP: critical_process_running":
            master.protocol(
                "WM_DELETE_WINDOW", False
            )  # prevent closing the app during partition
        elif queue_result == "APP: critical_process_done":
            master.protocol("WM_DELETE_WINDOW", None)  # re-enable closing the app
        elif queue_result == "STAGE: downloading":
            self.install_job_var.set(self.LN.job_starting_download)
        elif queue_result == "STAGE: verifying_checksum":
            self.install_job_var.set(self.LN.job_checksum)
        elif queue_result == "STAGE: creating_tmp_part":
            self.install_job_var.set(self.LN.job_creating_tmp_part)
            self.progressbar_install.set(0.92)
        elif queue_result == "STAGE: copying_to_tmp_part":
            self.install_job_var.set(self.LN.job_copying_to_tmp_part)
            self.progressbar_install.set(0.94)
        elif queue_result == "STAGE: adding_tmp_boot_entry":
            self.install_job_var.set(self.LN.job_adding_tmp_boot_entry)
            self.progressbar_install.set(0.98)
        elif queue_result == "STAGE: install_done":
            return 1
        elif (
            isinstance(queue_result, dict)
            and "type" in queue_result.keys()
            and queue_result["type"] == "dl_tracker"
        ):
            if queue_result["file_name"] != self.current_dl_file_name:
                self.total_already_downloaded += self.current_dl_file_size
                self.already_downloaded_percent = (
                    self.total_already_downloaded / self.total_download_size
                ) * 100
                self.file_index += 1
                for file in self.installer_args.dl_files:
                    if queue_result["file_name"] != file.file_name:
                        continue
                    self.current_dl_file_name = file.file_name
                    self.current_dl_file_size = file.size
                    self.current_dl_file_percent_factor = (
                        file.size / self.total_download_size
                    )
                    break
            if queue_result["status"] == "complete":
                pass
            elif queue_result["status"] == "downloading":
                self.progressbar_install.set(
                    (
                        (queue_result["%"] * self.current_dl_file_percent_factor)
                        + self.already_downloaded_percent
                    )
                    * self.global_downloads_factor
                    / 100
                )

                formatted_speed = fn.format_speed(float(queue_result["speed"]))
                formatted_eta = fn.format_eta(float(queue_result["eta"])).format(
                    ln_hour=self.LN.eta_hour,
                    ln_minute=self.LN.eta_minute,
                    ln_second=self.LN.eta_second,
                    ln_left=self.LN.eta_left,
                )
                formatted_size = fn.format_size(float(queue_result["size"]))

                self.install_job_var.set(
                    self.LN.job_dl_install_media
                    + f"\n{self.LN.downloads_number % (self.file_index, self.num_of_files)}"
                    f"\n{self.LN.dl_file_size}: {formatted_size}"
                    f"\n{self.LN.dl_speed}: {formatted_speed}"
                    f"\n{self.LN.dl_timeleft}: {formatted_eta}"
                )

        elif isinstance(queue_result, tuple) and queue_result[0] == "ERR: checksum":
            error_dict = queue_result[1]
            response_queue = self.queue
            print(error_dict)
            response = self.gui_download_hash_handler(self.master, **error_dict)
            response_queue.put(response)
            time.sleep(1)
            # Now exit the front end
            if response["app_quit"]:
                raise SystemExit

    def gui_download_hash_handler(self, master, error, file_hash="", expected_hash=""):
        go_next = False
        cleanup = False
        app_quit = False
        if error == "failed":
            question = tkt.input_pop_up(
                parent=master,
                title_txt=self.LN.job_checksum_failed,
                msg_txt=self.LN.job_checksum_failed_txt,
                primary_btn_str=self.LN.btn_yes,
                secondary_btn_str=self.LN.btn_no,
            )
            if question:
                go_next = True
            else:
                question = tkt.input_pop_up(
                    parent=master,
                    title_txt=self.LN.cleanup_question,
                    msg_txt=self.LN.cleanup_question_txt,
                    primary_btn_str=self.LN.btn_yes,
                    secondary_btn_str=self.LN.btn_no,
                )
                if question:
                    cleanup = True
                app_quit = True
        if error == "mismatch":
            question = tkt.input_pop_up(
                parent=master,
                title_txt=self.LN.job_checksum_mismatch,
                msg_txt=self.LN.job_checksum_mismatch_txt % (file_hash, expected_hash),
                primary_btn_str=self.LN.btn_retry,
                secondary_btn_str=self.LN.btn_abort,
            )
            if not question:
                question = tkt.input_pop_up(
                    parent=master,
                    title_txt=self.LN.cleanup_question,
                    msg_txt=self.LN.cleanup_question_txt,
                    primary_btn_str=self.LN.btn_yes,
                    secondary_btn_str=self.LN.btn_no,
                )
                if question:
                    cleanup = True
                app_quit = True
        return {"go_next": go_next, "cleanup": cleanup, "app_quit": app_quit}
