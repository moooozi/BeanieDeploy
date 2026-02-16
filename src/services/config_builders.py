"""
Configuration builders for Kickstart and GRUB files.
Handles the generation of installation configuration files.
"""

from dataclasses import dataclass

from core.settings import get_config
from models.kickstart import KickstartConfig, PartitioningConfig
from models.partition import PartitioningMethod


def auto_quote(value: str) -> str:
    """Automatically quote a string if it contains spaces."""
    if " " in value:
        return f"'{value}'"
    return value


def load_ks_template(name: str) -> str:
    config_path = get_config().paths
    path = config_path.install_helpers_ks_dir / f"{name}.ks"
    template = path.read_text()
    return template.replace("{log_dir}", config_path.log_dir)


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
    return load_ks_template("header").splitlines()


def _build_wifi_import(kickstart_config: KickstartConfig) -> list[str]:
    """Build WiFi profiles import section."""
    if not kickstart_config.wifi_profiles_dir_name:
        return []
    template = load_ks_template("wifi_import").replace(
        "{wifi_profiles_dir_name}", kickstart_config.wifi_profiles_dir_name
    )
    return template.splitlines()


def _build_clean_disk_pre_install(partitioning_config: PartitioningConfig) -> list[str]:
    """Build pre-install script for CLEAN_DISK method."""
    if not partitioning_config.sys_drive_uuid:
        msg = "sys_drive_uuid is required for clean_disk_pre"
        raise ValueError(msg)
    if not partitioning_config.sys_efi_uuid:
        msg = "sys_efi_uuid is required for clean_disk_pre"
        raise ValueError(msg)
    if not partitioning_config.tmp_part_uuid:
        msg = "tmp_part_uuid is required for clean_disk_pre"
        raise ValueError(msg)

    template = load_ks_template("clean_disk_pre")
    template = template.replace("{sys_drive_uuid}", partitioning_config.sys_drive_uuid)
    template = template.replace("{sys_efi_uuid}", partitioning_config.sys_efi_uuid)
    template = template.replace("{tmp_part_uuid}", partitioning_config.tmp_part_uuid)
    return template.splitlines()


def _build_clean_disk_pre_ramdisk_autopart(
    partitioning_config: PartitioningConfig,
) -> list[str]:
    """Build pre-install script for CLEAN_DISK method with RAMDISK and autopartitioning."""
    if not partitioning_config.sys_disk_uuid:
        msg = "sys_disk_uuid is required for clean_disk_pre_ramdisk_autopart"
        raise ValueError(msg)
    should_encrypt = "yes" if partitioning_config.is_encrypted else "no"
    template = (
        load_ks_template("clean_disk_pre_ramdisk_autopart")
        .replace("{DISK_UUID_PLACEHOLDER}", partitioning_config.sys_disk_uuid)
        .replace("{should_encrypt}", should_encrypt)
    )
    return template.splitlines()


def _build_clean_disk_post_install(
    partitioning_config: PartitioningConfig,
) -> list[str]:
    """Build post-install script for CLEAN_DISK method."""
    if not partitioning_config.tmp_part_uuid:
        msg = "tmp_part_uuid is required for clean_disk_post_install"
        raise ValueError(msg)

    template_name = (
        "clean_disk_post_encrypted"
        if partitioning_config.is_encrypted
        else "clean_disk_post_non_encrypted"
    )

    template = load_ks_template(template_name)
    template = template.replace("{tmp_part_uuid}", partitioning_config.tmp_part_uuid)

    if partitioning_config.is_encrypted:
        if not partitioning_config.sys_drive_uuid:
            msg = "sys_drive_uuid is required for encrypted clean_disk_post_install"
            raise ValueError(msg)
        template = template.replace(
            "{sys_drive_uuid}", partitioning_config.sys_drive_uuid
        )

    return template.splitlines()


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

    # Format keymaps to ensure space before variant if needed
    formatted_keymaps = []
    for k in locale_config.keymaps:
        if "(" in k and " (" not in k:
            k = k.replace("(", " (")
        formatted_keymaps.append(k)
    quoted_keymaps = [auto_quote(k) for k in formatted_keymaps]
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

    user_line = f"user --name={kickstart_config.user_username} --groups=wheel"
    if kickstart_config.user_full_name:
        user_line += f" --gecos={auto_quote(kickstart_config.user_full_name)}"
    user_line += " --password=$y$j9T$GzhAGo.8wPNzc7t2UXYc.1$BKeaQVnM8Kw9qQ3mMujMItANkMtyTmhsXxbebJFQ5xC"

    post_lines = (
        load_ks_template("password_setup_post")
        .replace("{username}", kickstart_config.user_username)
        .splitlines()
    )
    return [user_line, *post_lines]


# DUALBOOT is broken. Disabled in the GUI but still available here.
def _build_partitioning_config(partitioning_config: PartitioningConfig) -> list[str]:
    """Build partitioning configuration section."""
    lines = []

    if partitioning_config.method == PartitioningMethod.CLEAN_DISK_RAMDISK:
        return _build_clean_disk_pre_ramdisk_autopart(partitioning_config)

    if partitioning_config.method == PartitioningMethod.CLEAN_DISK:
        lines.extend(_build_clean_disk_pre_install(partitioning_config))
        lines.extend(_build_clean_disk_post_install(partitioning_config))

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

    boot_partition = f"part /boot --fstype=ext4 --label=fedora_boot --onpart=/dev/disk/by-partuuid/{partitioning_config.boot_guid}"

    if partitioning_config.is_encrypted:
        # Separate boot partition for encryption
        root_partition += " --encrypted"
        if partitioning_config.passphrase:
            root_partition += f" --passphrase={partitioning_config.passphrase}"

    if partitioning_config.method == PartitioningMethod.DUALBOOT:
        lines.extend(
            [
                efi_partition,
                root_partition,
                "btrfs none --label=fedora btrfs.01",
                "btrfs / --subvol --name=root fedora",
                "btrfs /home --subvol --name=home fedora",
                "btrfs /var --subvol --name=var fedora",
                boot_partition,  # Boot partition is added last in dualboot
            ]
        )
    else:
        lines.extend(
            [
                efi_partition,
                root_partition,
                boot_partition,
                "btrfs none --label=fedora btrfs.01",
                "btrfs / --subvol --name=root fedora",
                "btrfs /home --subvol --name=home fedora",
                "btrfs /var --subvol --name=var fedora",
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
    if kickstart_config.user_username:
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


def build_grub_cfg_file(
    root_partition_label: str,
    is_autoinst: bool = False,
    autoinstall_ramdisk: bool = False,
) -> str:
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
        linux_cmd = f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} rd.live.check inst.ks=hd:LABEL={root_partition_label} quiet"
        if autoinstall_ramdisk:
            linux_cmd = linux_cmd.replace(
                " rd.live.check", " rd.live.check rd.live.ram"
            )
        entries.insert(
            0,
            GrubEntry(
                title="Auto Install Fedora",
                prelines=(),
                linux_cmd=linux_cmd,
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
