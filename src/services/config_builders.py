"""
Configuration builders for Kickstart and GRUB files.
Handles the generation of installation configuration files.
"""
from typing import List

from ..models.kickstart import KickstartConfig, LocaleConfig, PartitioningConfig


def _validate_kickstart_config(kickstart_config: KickstartConfig) -> None:
    """
    Validate the kickstart configuration for required fields and consistency.
    
    Args:
        kickstart_config: The configuration to validate
        
    Raises:
        ValueError: If the configuration is invalid with details about what's wrong
    """
    errors: List[str] = []
    
    # Validate partitioning config
    if not kickstart_config.partitioning.method:
        errors.append("Partitioning method is required")
    elif kickstart_config.partitioning.method not in ["dualboot", "replace_win", "custom"]:
        errors.append(f"Invalid partitioning method: {kickstart_config.partitioning.method}")
    
    if kickstart_config.partitioning.method == "dualboot":
        if not kickstart_config.partitioning.root_guid:
            errors.append("root_guid is required for dualboot partition method")
        if kickstart_config.partitioning.is_encrypted and not kickstart_config.partitioning.boot_guid:
            errors.append("boot_guid is required for dualboot partition method with encryption")
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for dualboot partition method")
    
    if kickstart_config.partitioning.method == "replace_win":
        if not kickstart_config.partitioning.sys_drive_uuid:
            errors.append("sys_drive_uuid is required for replace_win partition method")
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for replace_win partition method")
    
    if kickstart_config.partitioning.is_encrypted:
        if kickstart_config.partitioning.method == "dualboot" and not kickstart_config.partitioning.boot_guid:
            errors.append("boot_guid is required for dualboot partition method with encryption")
        
    # Validate WiFi profiles directory name if specified
    if kickstart_config.wifi_profiles_dir_name and not isinstance(kickstart_config.wifi_profiles_dir_name, str):
        errors.append("wifi_profiles_dir_name must be a string")
    
    if errors:
        raise ValueError(f"Invalid kickstart configuration: {'; '.join(errors)}")


def _build_header() -> List[str]:
    """Build the kickstart file header section."""
    return [
        "# Kickstart file created by BeanieDeploy.",
        "graphical",
        "# removing kickstart files containing sensitive data and",
        "# reverting install media boot options",
        "%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log",
        "rm /run/install/repo/ks.cfg",
        "cp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg",
        "%end"
    ]


def _build_wifi_import(kickstart_config: KickstartConfig) -> List[str]:
    """Build WiFi profiles import section."""
    if not kickstart_config.wifi_profiles_dir_name:
        return []
    
    return [
        "# Importing Wi-Fi profiles",
        "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_wifi.log",
        "mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections",
        f"cp /run/install/repo/{kickstart_config.wifi_profiles_dir_name}/*.* /mnt/sysimage/etc/NetworkManager/system-connections",
        "%end"
    ]


def _build_system_config(locale_config: LocaleConfig) -> List[str]:
    """Build system configuration section."""
    lines = []
    
    # Determine firstboot configuration
    if locale_config.keymap and locale_config.locale and locale_config.timezone:
        firstboot_line = "firstboot --enable"
    else:
        firstboot_line = "firstboot --reconfig"
        if not locale_config.keymap:
            locale_config.keymap = "us"
        if not locale_config.locale:
            locale_config.locale = "en_US.UTF-8"
        if not locale_config.timezone:
            locale_config.timezone = "America/New_York"

    lines.append(firstboot_line)

    # Keyboard configuration
    if locale_config.keymap_type == "vc":
        lines.append(f"keyboard --vckeymap={locale_config.keymap}")
    else:
        lines.append(f"keyboard --xlayouts='{locale_config.keymap}'")
    
    lines.extend([
        f"lang {locale_config.locale}",
        "firewall --use-system-defaults",
        f"timezone {locale_config.timezone} --utc"
    ])
    
    return lines


def _build_install_source(kickstart_config: KickstartConfig) -> List[str]:
    """Build install source configuration section."""
    lines = []
    if kickstart_config.ostree_args:
        lines.append(f"ostreesetup {kickstart_config.ostree_args}")
    if kickstart_config.live_img_url:
        lines.append(f"liveimg --url='{kickstart_config.live_img_url}' --noverifyssl")
    return lines


def _build_partitioning_config(partitioning_config: PartitioningConfig) -> List[str]:
    """Build partitioning configuration section."""
    lines = []
    
    # Validate required parameters for dualboot
    if partitioning_config.method == "dualboot":
        if not partitioning_config.root_guid:
            raise ValueError("root_guid is required for dualboot partition method")
        if partitioning_config.is_encrypted and not partitioning_config.boot_guid:
            raise ValueError("boot_guid is required for dualboot partition method with encryption")
    
    root_partition = "part btrfs.01"
    efi_partition = ""

    if partitioning_config.method == "dualboot":
        efi_partition = f"mount /dev/disk/by-partuuid/{partitioning_config.sys_efi_uuid} /boot/efi "
        root_partition += f" --onpart=/dev/disk/by-partuuid/{partitioning_config.root_guid}"
    elif partitioning_config.method == "replace_win":
        efi_partition = f"part /boot/efi --fstype=efi --label=efi --onpart=/dev/disk/by-partuuid/{partitioning_config.sys_efi_uuid}"
        root_partition += f" --onpart=/dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid}"

    if partitioning_config.is_encrypted:
        # Separate boot partition for encryption
        boot_partition = f"part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-partuuid/{partitioning_config.boot_guid}"
        root_partition += " --encrypted"
        if partitioning_config.passphrase:
            root_partition += f" --passphrase={partitioning_config.passphrase}"
    else:
        # Boot subvolume inside root if encryption is disabled
        boot_partition = "btrfs /boot --subvol --name=boot fedora"

    lines.extend([
        efi_partition,
        root_partition,
        "btrfs none --label=fedora btrfs.01",
        "btrfs / --subvol --name=root fedora",
        "btrfs /home --subvol --name=home fedora",
        "btrfs /var --subvol --name=var fedora",
        boot_partition
    ])
    
    return lines


def build_autoinstall_ks_file(
    kickstart_config: KickstartConfig,
) -> str:
    """
    Build a Kickstart file for automated Fedora installation.
    
    Args:
        kickstart_config: Kickstart configuration object
        
    Returns:
        Generated Kickstart file content
        
    Raises:
        ValueError: If the configuration is invalid
    """
    # Validate configuration
    _validate_kickstart_config(kickstart_config)
    
    kickstart_lines = []
    
    # Build different sections of the kickstart file
    kickstart_lines.extend(_build_header())
    kickstart_lines.extend(_build_wifi_import(kickstart_config))
    kickstart_lines.extend(_build_system_config(kickstart_config.locale))
    kickstart_lines.extend(_build_install_source(kickstart_config))
    kickstart_lines.extend(_build_partitioning_config(kickstart_config.partitioning))
    
    # Final lines
    kickstart_lines.extend(["rootpw --lock", "reboot"])

    return "\n".join(kickstart_lines) + "\n"



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
