"""
Configuration builders for Kickstart and GRUB files.
Handles the generation of installation configuration files.
"""
from typing import Optional, List


def build_autoinstall_ks_file(
    keymap: Optional[str] = None,
    keymap_type: str = "vc",
    locale: Optional[str] = None,
    timezone: Optional[str] = None,
    ostree_args: Optional[str] = None,
    wifi_profiles_dir_name: Optional[str] = None,
    is_encrypted: bool = False,
    passphrase: Optional[str] = None,
    tpm_auto_unlock: bool = True,
    live_img_url: str = "",
    additional_repos: bool = True,
    sys_drive_uuid: Optional[str] = None,
    sys_efi_uuid: Optional[str] = None,
    partition_method: Optional[str] = None,
    additional_rpm_dir: Optional[str] = None,
) -> str:
    """
    Build a Kickstart file for automated Fedora installation.
    
    Args:
        keymap: Keyboard layout
        keymap_type: Type of keymap ("vc" or "xlayouts")
        locale: System locale
        timezone: System timezone
        ostree_args: OSTree arguments for immutable systems
        wifi_profiles_dir_name: Directory containing WiFi profiles
        is_encrypted: Whether to enable disk encryption
        passphrase: Encryption passphrase
        tpm_auto_unlock: Whether to enable TPM auto-unlock
        live_img_url: URL to live image
        additional_repos: Whether to add additional repositories
        sys_drive_uuid: System drive UUID
        sys_efi_uuid: EFI partition UUID
        partition_method: Partitioning method ("dualboot", "replace_win", "custom")
        additional_rpm_dir: Directory containing additional RPM packages
        
    Returns:
        Generated Kickstart file content
    """
    kickstart_lines = []
    
    # Header
    kickstart_lines.extend([
        "# Kickstart file created by BeanieDeploy.",
        "graphical",
        "# removing kickstart files containing sensitive data and",
        "# reverting install media boot options",
        "%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log",
        "rm /run/install/repo/ks.cfg",
        "cp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg",
        "%end"
    ])

    # WiFi profiles import
    if wifi_profiles_dir_name:
        kickstart_lines.extend([
            "# Importing Wi-Fi profiles",
            "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_wifi.log",
            "mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections",
            f"cp /run/install/repo/{wifi_profiles_dir_name}/*.* /mnt/sysimage/etc/NetworkManager/system-connections",
            "%end"
        ])

    # Additional packages installation
    if additional_rpm_dir:
        install_command = "rpm-ostree install" if ostree_args else "dnf install"
        kickstart_lines.extend([
            "# Installing additional packages",
            "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_additional_rpm1.log",
            "mkdir -p /mnt/sysimage/root/tmp_rpm",
            f"cp /run/install/repo/{additional_rpm_dir}/*.rpm /mnt/sysimage/root/tmp_rpm",
            "%end",
            "%post --logfile=/root/ks-post_additional_rpm2.log",
            f"{install_command} /root/tmp_rpm/*.rpm -y",
            "rm -rf /root/tmp_rpm",
            "%end"
        ])

    # TPM auto-unlock for encryption
    if is_encrypted and passphrase and tpm_auto_unlock:
        kickstart_lines.extend([
            "# Activating encryption auto-unlock using TPM2 chip",
            "%post  --logfile=/root/ks-post_tmp2_unlock.log",
            f"PASSWORD={passphrase} systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7+8 $device",
            "sed -ie '/^luks-/s/$/,tpm2-device=auto/' /etc/crypttab",
            "dracut -f",
            "%end"
        ])

    # System configuration
    _add_system_configuration(kickstart_lines, keymap, keymap_type, locale, timezone)
    
    # Install source configuration
    if ostree_args:
        kickstart_lines.append(f"ostreesetup {ostree_args}")
    if live_img_url:
        kickstart_lines.append(f"liveimg --url='{live_img_url}' --noverifyssl")

    # Partitioning configuration
    _add_partitioning_configuration(
        kickstart_lines, partition_method, sys_drive_uuid, sys_efi_uuid, 
        is_encrypted, passphrase
    )
    
    kickstart_lines.extend(["rootpw --lock", "reboot"])

    return "\n".join(kickstart_lines) + "\n"


def _add_system_configuration(
    kickstart_lines: List[str], 
    keymap: Optional[str], 
    keymap_type: str,
    locale: Optional[str], 
    timezone: Optional[str], 
) -> None:
    """Add system configuration to kickstart file."""
    # Determine firstboot configuration
    if keymap and locale and timezone:
        firstboot_line = "firstboot --enable"
    else:
        firstboot_line = "firstboot --reconfig"
        if not keymap:
            keymap = "us"
        if not locale:
            locale = "en_US.UTF-8"
        if not timezone:
            timezone = "America/New_York"

    kickstart_lines.append(firstboot_line)

    # Keyboard configuration
    if keymap_type == "vc":
        kickstart_lines.append(f"keyboard --vckeymap={keymap}")
    else:
        kickstart_lines.append(f"keyboard --xlayouts='{keymap}'")
    
    kickstart_lines.extend([
        f"lang {locale}",
        "firewall --use-system-defaults",
        f"timezone {timezone} --utc"
    ])


def _add_partitioning_configuration(
    kickstart_lines: List[str],
    partition_method: Optional[str],
    sys_drive_uuid: Optional[str],
    sys_efi_uuid: Optional[str],
    is_encrypted: bool,
    passphrase: Optional[str]
) -> None:
    """Add partitioning configuration to kickstart file."""
    root_partition = "part btrfs.01"
    efi_partition = ""

    if partition_method == "dualboot":
        efi_partition = f"mount /dev/disk/by-partuuid/{sys_efi_uuid} /boot/efi "
        root_partition += " --onpart=/dev/disk/by-label/ALLOC-ROOT"
    elif partition_method == "replace_win":
        efi_partition = f"part /boot/efi --fstype=efi --label=efi --onpart=/dev/disk/by-partuuid/{sys_efi_uuid}"
        root_partition += f" --onpart=/dev/disk/by-partuuid/{sys_drive_uuid}"

    if is_encrypted:
        # Separate boot partition for encryption
        boot_partition = "part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-label/ALLOC-BOOT"
        root_partition += " --encrypted"
        if passphrase:
            root_partition += f" --passphrase={passphrase}"
    else:
        # Boot subvolume inside root if encryption is disabled
        boot_partition = "btrfs /boot --subvol --name=boot fedora"

    kickstart_lines.extend([
        efi_partition,
        root_partition,
        "btrfs none --label=fedora btrfs.01",
        "btrfs / --subvol --name=root fedora",
        "btrfs /home --subvol --name=home fedora",
        "btrfs /var --subvol --name=var fedora",
        boot_partition
    ])


def build_grub_cfg_file(root_partition_label: str, is_autoinst: bool = False) -> str:
    """
    Build a GRUB configuration file for the installer.
    
    Args:
        root_partition_label: Label of the root partition
        is_autoinst: Whether to include auto-install menu entry
        
    Returns:
        Generated GRUB configuration file content
    """
    grub_lines = [
        "### Grub configuration generated by BeanieDeploy ###",
        'set default="0"',
        """function load_video {
            insmod efi_gop
            insmod efi_uga
            insmod video_bochs
            insmod video_cirrus
            insmod all_video
        }""",
        "load_video",
        "set gfxpayload=keep",
        "insmod gzio",
        "insmod part_gpt",
        "insmod ext2",
        "set timeout=5",
        f"search --no-floppy --set=root -l '{root_partition_label}'",
    ]

    # Menu entries configuration
    menu_entries = [
        (
            "Install Fedora",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Install Fedora (RAM-Boot)",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check rd.live.ram quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Install Fedora in basic graphics mode",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% nomodeset quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
        (
            "Rescue a Fedora system",
            "linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% inst.rescue quiet",
            "initrdefi /images/pxeboot/initrd.img",
        ),
    ]

    # Auto-install entry (if enabled)
    if is_autoinst:
        grub_lines.append(
            """menuentry 'Auto Install Fedora' --class fedora --class gnu-linux --class gnu --class os {
                linuxefi /images/pxeboot/vmlinuz inst.stage2=hd:LABEL=%root_label% rd.live.check inst.ks=hd:LABEL=%root_label% quiet
                initrdefi /images/pxeboot/initrd.img
            }"""
        )

    # Main menu entries
    for title, linux_cmd, initrd_cmd in menu_entries[:2]:
        grub_lines.append(
            f"""menuentry '{title}' --class fedora --class gnu-linux --class gnu --class os {{
                {linux_cmd}
                {initrd_cmd}
            }}"""
        )

    # Troubleshooting submenu
    grub_lines.append("submenu 'Troubleshooting -->' {")
    for title, linux_cmd, initrd_cmd in menu_entries[2:]:
        grub_lines.append(
            f"""    menuentry '{title}' --class fedora --class gnu-linux --class gnu --class os {{
                {linux_cmd}
                {initrd_cmd}
            }}"""
        )
    grub_lines.append("}")

    return "\n".join(grub_lines).replace("%root_label%", root_partition_label)
