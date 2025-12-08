"""
Configuration builders for Kickstart and GRUB files.
Handles the generation of installation configuration files.
"""

from dataclasses import dataclass

from models.kickstart import KickstartConfig, PartitioningConfig
from models.partition import PartitioningMethod


def auto_quote(value: str) -> str:
    """Automatically quote a string if it contains spaces."""
    if " " in value:
        return f"'{value}'"
    return value


@dataclass(frozen=True)
class GrubEntry:
    """Represents a GRUB menu entry configuration."""

    title: str
    prelines: tuple[str, ...]
    linux_cmd: str
    initrd_cmd: str
    is_in_submenu: bool


def _build_load_video_function() -> str:
    """Build the GRUB load_video function string."""
    modules = (
        "efi_gop",
        "efi_uga",
        "video_bochs",
        "video_cirrus",
        "all_video",
    )
    lines = ["function load_video {"]
    for module in modules:
        lines.append(f"  insmod {module}")
    lines.append("}")
    return "\n".join(lines)


def _validate_kickstart_config(kickstart_config: KickstartConfig) -> None:
    """
    Validate the kickstart configuration for required fields and consistency.

    Args:
        kickstart_config: The configuration to validate

    Raises:
        ValueError: If the configuration is invalid with details about what's wrong
    """
    errors: list[str] = []

    # Validate partitioning config
    if not kickstart_config.partitioning.method:
        errors.append("Partitioning method is required")
    elif kickstart_config.partitioning.method not in [
        PartitioningMethod.DUALBOOT,
        PartitioningMethod.REPLACE_WIN,
        PartitioningMethod.CLEAN_DISK,
        PartitioningMethod.CUSTOM,
    ]:
        errors.append(
            f"Invalid partitioning method: {kickstart_config.partitioning.method}"
        )

    if kickstart_config.partitioning.method == PartitioningMethod.DUALBOOT:
        if not kickstart_config.partitioning.root_guid:
            errors.append("root_guid is required for dualboot partition method")
        if (
            kickstart_config.partitioning.is_encrypted
            and not kickstart_config.partitioning.boot_guid
        ):
            errors.append(
                "boot_guid is required for dualboot partition method with encryption"
            )
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for dualboot partition method")

    if kickstart_config.partitioning.method == PartitioningMethod.REPLACE_WIN:
        if not kickstart_config.partitioning.sys_drive_uuid:
            errors.append("sys_drive_uuid is required for replace_win partition method")
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for replace_win partition method")

    if kickstart_config.partitioning.method == PartitioningMethod.CLEAN_DISK:
        if not kickstart_config.partitioning.sys_drive_uuid:
            errors.append("sys_drive_uuid is required for clean_disk partition method")
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for clean_disk partition method")
        if not kickstart_config.partitioning.tmp_part_uuid:
            errors.append("tmp_part_uuid is required for clean_disk partition method")

    if kickstart_config.partitioning.is_encrypted and (
        kickstart_config.partitioning.method == PartitioningMethod.DUALBOOT
        and not kickstart_config.partitioning.boot_guid
    ):
        errors.append(
            "boot_guid is required for dualboot partition method with encryption"
        )

    if errors:
        msg = f"Invalid kickstart configuration: {'; '.join(errors)}"
        raise ValueError(msg)


def _build_header() -> list[str]:
    """Build the kickstart file header section."""
    return [
        "# Kickstart file created by BeanieDeploy.",
        "graphical",
        "# removing kickstart files containing sensitive data and",
        "# reverting install media boot options",
        "%post --nochroot --logfile=/mnt/sysimage/root/ks-post.log",
        "rm /run/install/repo/ks.cfg",
        "cp /run/install/repo/EFI/BOOT/BOOT.cfg /run/install/repo/EFI/BOOT/grub.cfg",
        "%end",
    ]


def _build_wifi_import(kickstart_config: KickstartConfig) -> list[str]:
    """Build WiFi profiles import section."""
    if not kickstart_config.wifi_profiles_dir_name:
        return []

    return [
        "# Importing Wi-Fi profiles",
        "%post --nochroot --logfile=/mnt/sysimage/root/ks-post_wifi.log",
        "mkdir -p /mnt/sysimage/etc/NetworkManager/system-connections",
        f"cp /run/install/repo/{kickstart_config.wifi_profiles_dir_name}/*.* /mnt/sysimage/etc/NetworkManager/system-connections",
        "%end",
    ]


def _build_clean_disk_pre_install(partitioning_config: PartitioningConfig) -> list[str]:
    """Build pre-install script for CLEAN_DISK method."""
    return [
        "# Pre-install script for CLEAN_DISK: Delete all partitions except specified ones",
        "%pre --logfile=/tmp/ks-pre-clean.log",
        "# Find the disk containing the sys_drive_uuid partition",
        f"DISK=$(lsblk -no pkname /dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid})",
        "# List all partitions on the disk",
        'PARTITIONS=$(lsblk -no name /dev/$DISK | grep -E "^${DISK}p?[0-9]+$")',
        "# Partitions to keep",
        f"KEEP_PARTS='/dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid} /dev/disk/by-partuuid/{partitioning_config.sys_efi_uuid} /dev/disk/by-partuuid/{partitioning_config.tmp_part_uuid}'",
        "# Delete partitions not in keep list",
        "for PART in $PARTITIONS; do",
        "    PART_UUID=$(blkid -s PARTUUID -o value /dev/$PART)",
        '    if [[ ! " $KEEP_PARTS " =~ " /dev/disk/by-partuuid/$PART_UUID " ]]; then',
        '        echo "Deleting partition /dev/$PART"',
        "        parted /dev/$DISK rm $(echo $PART | sed 's/.*[a-z]//')",
        "    fi",
        "done",
        "%end",
    ]


def _build_clean_disk_post_install(
    partitioning_config: PartitioningConfig,
) -> list[str]:
    """Build post-install script for CLEAN_DISK method."""
    lines = [
        "# Post-install script for CLEAN_DISK: Clean up tmp partition and extend root",
        "%post --logfile=/mnt/sysimage/root/ks-post-clean.log",
        "# Force unmount and erase tmp partition",
        f"umount /dev/disk/by-partuuid/{partitioning_config.tmp_part_uuid} 2>/dev/null || true",
        f"wipefs -a /dev/disk/by-partuuid/{partitioning_config.tmp_part_uuid}",
        f"parted $(lsblk -no pkname /dev/disk/by-partuuid/{partitioning_config.tmp_part_uuid}) rm $(lsblk -no partn /dev/disk/by-partuuid/{partitioning_config.tmp_part_uuid})",
    ]

    if partitioning_config.is_encrypted:
        # Extend LUKS partition first
        lines.extend(
            [
                "# Extend LUKS partition to fill disk",
                f"LUKS_DEV=$(lsblk -no name /dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid})",
                "parted /dev/$(lsblk -no pkname /dev/$LUKS_DEV) resizepart $(lsblk -no partn /dev/$LUKS_DEV) 100%",
                "# Resize LUKS container",
                f"cryptsetup resize /dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid}",
            ]
        )

    # Extend Btrfs filesystem
    lines.extend(
        [
            "# Extend Btrfs filesystem to fill partition",
            "btrfs filesystem resize max /",
            "%end",
        ]
    )

    return lines


def _build_system_config(kickstart_config: KickstartConfig) -> list[str]:
    """Build system configuration section."""
    lines = []

    locale_config = kickstart_config.locale_settings

    # Determine firstboot configuration
    if locale_config.keymaps and locale_config.locale and locale_config.timezone:
        if kickstart_config.user_username:
            firstboot_line = "firstboot --disable"
        else:
            firstboot_line = "firstboot --enable"
    else:
        firstboot_line = "firstboot --reconfig"
        if not locale_config.keymaps:
            locale_config.keymaps = ["us"]
        if not locale_config.locale:
            locale_config.locale = "en_US.UTF-8"
        if not locale_config.timezone:
            locale_config.timezone = "America/New_York"

    lines.append(firstboot_line)

    # Keyboard configuration
    if locale_config.keymap_type == "vc":
        lines.append(f"keyboard --vckeymap={locale_config.keymaps[0]}")
    else:
        quoted_keymaps = [auto_quote(k) for k in locale_config.keymaps]
        lines.append(f"keyboard --xlayouts={','.join(quoted_keymaps)}")

    lines.extend(
        [
            f"lang {locale_config.locale}",
            "firewall --use-system-defaults",
            f"timezone {locale_config.timezone} --utc",
        ]
    )

    return lines


def _build_install_source(kickstart_config: KickstartConfig) -> list[str]:
    """Build install source configuration section."""
    lines = []
    if kickstart_config.ostree_args:
        lines.append(f"ostreesetup {kickstart_config.ostree_args}")
    if kickstart_config.live_img_url:
        lines.append(f"liveimg --url='{kickstart_config.live_img_url}' --noverifyssl")
    return lines


def _build_user_config(kickstart_config: KickstartConfig) -> list[str]:
    """Build user configuration section."""
    if not kickstart_config.user_username:
        return []

    user_line = f"user --name={kickstart_config.user_username} --groups=wheel"
    if kickstart_config.user_full_name:
        user_line += f" --gecos={auto_quote(kickstart_config.user_full_name)}"
    user_line += " --password=$y$j9T$Evvlldu/nejcJnjF9gj0.1$8TJcd0fh0754UQ5PhSwyZJq1gBCA431uk2sfZqtqGb7"

    return [user_line]


def _build_partitioning_config(partitioning_config: PartitioningConfig) -> list[str]:
    """Build partitioning configuration section."""
    lines = []

    # Validate required parameters for dualboot
    if partitioning_config.method == PartitioningMethod.DUALBOOT:
        if not partitioning_config.root_guid:
            msg = "root_guid is required for dualboot partition method"
            raise ValueError(msg)
        if partitioning_config.is_encrypted and not partitioning_config.boot_guid:
            msg = "boot_guid is required for dualboot partition method with encryption"
            raise ValueError(msg)

    root_partition = "part btrfs.01"
    efi_partition = ""

    if partitioning_config.method == PartitioningMethod.DUALBOOT:
        efi_partition = (
            f"mount /dev/disk/by-partuuid/{partitioning_config.sys_efi_uuid} /boot/efi "
        )
        root_partition += (
            f" --onpart=/dev/disk/by-partuuid/{partitioning_config.root_guid}"
        )
    elif partitioning_config.method in [
        PartitioningMethod.REPLACE_WIN,
        PartitioningMethod.CLEAN_DISK,
    ]:
        efi_partition = f"part /boot/efi --fstype=efi --label=efi --onpart=/dev/disk/by-partuuid/{partitioning_config.sys_efi_uuid}"
        root_partition += (
            f" --onpart=/dev/disk/by-partuuid/{partitioning_config.sys_drive_uuid}"
        )

    if partitioning_config.is_encrypted:
        # Separate boot partition for encryption
        boot_partition = f"part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-partuuid/{partitioning_config.boot_guid}"
        root_partition += " --encrypted"
        if partitioning_config.passphrase:
            root_partition += f" --passphrase={partitioning_config.passphrase}"
    else:
        # Boot subvolume inside root if encryption is disabled
        boot_partition = "btrfs /boot --subvol --name=boot fedora"

    lines.extend(
        [
            efi_partition,
            root_partition,
            "btrfs none --label=fedora btrfs.01",
            "btrfs / --subvol --name=root fedora",
            "btrfs /home --subvol --name=home fedora",
            "btrfs /var --subvol --name=var fedora",
            boot_partition,
        ]
    )

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
    kickstart_lines.extend(_build_system_config(kickstart_config))
    kickstart_lines.extend(_build_user_config(kickstart_config))
    kickstart_lines.extend(_build_install_source(kickstart_config))
    kickstart_lines.extend(_build_partitioning_config(kickstart_config.partitioning))

    # Add CLEAN_DISK scripts if applicable
    if kickstart_config.partitioning.method == PartitioningMethod.CLEAN_DISK:
        kickstart_lines.extend(
            _build_clean_disk_pre_install(kickstart_config.partitioning)
        )
        kickstart_lines.extend(
            _build_clean_disk_post_install(kickstart_config.partitioning)
        )

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
    # Define GRUB entries
    entries = [
        GrubEntry(
            title="Install Fedora",
            prelines=(),
            linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} rd.live.check quiet",
            initrd_cmd="initrd /images/pxeboot/initrd.img",
            is_in_submenu=False,
        ),
        GrubEntry(
            title="Install Fedora (RAM-Boot)",
            prelines=(),
            linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} rd.live.check rd.live.ram quiet",
            initrd_cmd="initrd /images/pxeboot/initrd.img",
            is_in_submenu=False,
        ),
        GrubEntry(
            title="Install Fedora in basic graphics mode",
            prelines=(),
            linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} nomodeset quiet",
            initrd_cmd="initrd /images/pxeboot/initrd.img",
            is_in_submenu=True,
        ),
        GrubEntry(
            title="Rescue a Fedora system",
            prelines=(),
            linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} inst.rescue quiet",
            initrd_cmd="initrd /images/pxeboot/initrd.img",
            is_in_submenu=True,
        ),
    ]

    # Add auto-install entry if enabled
    if is_autoinst:
        entries.insert(
            0,
            GrubEntry(
                title="Auto Install Fedora",
                prelines=(),
                linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} rd.live.check inst.ks=hd:LABEL={root_partition_label} quiet",
                initrd_cmd="initrd /images/pxeboot/initrd.img",
                is_in_submenu=False,
            ),
        )

    # Build GRUB lines
    grub_lines = [
        "### Grub configuration generated by BeanieDeploy ###",
        'set default="0"',
        _build_load_video_function(),
        "load_video",
        "set gfxpayload=keep",
        "insmod gzio",
        "insmod part_gpt",
        "insmod ext2",
        "set timeout=5",
        f"search --no-floppy --set=root -l '{root_partition_label}'",
    ]

    # Separate entries into main and submenu
    main_entries = [entry for entry in entries if not entry.is_in_submenu]
    submenu_entries = [entry for entry in entries if entry.is_in_submenu]

    # Add main menu entries
    for entry in main_entries:
        menu_lines = [
            f"""menuentry '{entry.title}' --class fedora --class gnu-linux --class gnu --class os {{"""
        ]
        menu_lines.extend(f"    {line}" for line in entry.prelines)
        menu_lines.append(f"    {entry.linux_cmd}")
        menu_lines.append(f"    {entry.initrd_cmd}")
        menu_lines.append("}")
        grub_lines.extend(menu_lines)

    # Add troubleshooting submenu if there are submenu entries
    if submenu_entries:
        grub_lines.append("submenu 'Troubleshooting -->' {")
        for entry in submenu_entries:
            menu_lines = [
                f"""    menuentry '{entry.title}' --class fedora --class gnu-linux --class gnu --class os {{"""
            ]
            menu_lines.extend(f"        {line}" for line in entry.prelines)
            menu_lines.append(f"        {entry.linux_cmd}")
            menu_lines.append(f"        {entry.initrd_cmd}")
            menu_lines.append("    }")
            grub_lines.extend(menu_lines)
        grub_lines.append("}")

    return "\n".join(grub_lines)
