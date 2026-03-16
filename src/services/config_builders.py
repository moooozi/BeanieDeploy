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


def load_ks_python_script(
    name: str,
    mode: str,
    options: tuple[str, ...] = (),
    template_vars: dict[str, str] | None = None,
) -> str:
    """Load a Python helper script and wrap it as a Kickstart script block."""
    if mode not in {"pre", "post"}:
        msg = f"Invalid kickstart script mode: {mode}"
        raise ValueError(msg)

    config_path = get_config().paths
    script_name = name if name.endswith(".py") else f"{name}.py"
    path = config_path.install_helpers_scripts_dir / script_name
    script_content = path.read_text()

    header = (
        f"%{mode} --interpreter=/usr/bin/python3 "
        f"--logfile={config_path.log_dir}/post_{path.stem}"
    )
    if options:
        header = f"{header} {' '.join(options)}"

    if template_vars:
        for key, value in template_vars.items():
            script_content = script_content.replace(f"{{{key}}}", value)

    return "\n".join((header, script_content, "%end"))


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

    if kickstart_config.partitioning.method == PartitioningMethod.CLEAN_DISK:
        if not kickstart_config.partitioning.sys_drive_uuid:
            errors.append("sys_drive_uuid is required for clean_disk partition method")
        if not kickstart_config.partitioning.sys_efi_uuid:
            errors.append("sys_efi_uuid is required for clean_disk partition method")
        if not kickstart_config.partitioning.tmp_part_uuid:
            errors.append("tmp_part_uuid is required for clean_disk partition method")

    if errors:
        msg = f"Invalid kickstart configuration: {'; '.join(errors)}"
        raise ValueError(msg)


def _build_header() -> list[str]:
    """Build the kickstart file header section."""
    return load_ks_template("header").splitlines()


def _build_clean_disk_pre_install(partitioning_config: PartitioningConfig) -> list[str]:
    """Build pre-install script for CLEAN_DISK method."""
    if not partitioning_config.sys_disk_uuid:
        msg = "sys_disk_uuid is required for clean_disk_pre"
        raise ValueError(msg)
    if not partitioning_config.tmp_part_uuid:
        msg = "tmp_part_uuid is required for clean_disk_pre"
        raise ValueError(msg)

    lines = load_ks_python_script(
        "partition",
        "pre",
        template_vars={
            "disk_path_or_uuid": partitioning_config.sys_disk_uuid,
            "should_delete_all": "yes",
            "delete_all_except": partitioning_config.tmp_part_uuid,
        },
    ).splitlines()

    lines.append(r"%include /tmp/wingone_vars/partitioning_ks")
    return lines


def _build_clean_disk_post_install(
    partitioning_config: PartitioningConfig,
    is_ostree: bool,
) -> list[str]:
    """Build post-install script for CLEAN_DISK method."""
    if not partitioning_config.tmp_part_uuid:
        msg = "tmp_part_uuid is required for clean_disk_post_install"
        raise ValueError(msg)

    template_name = "partition_resize_tool"
    template = load_ks_template(template_name)
    template = template.replace(
        "{tmp_part_uuid}", partitioning_config.tmp_part_uuid
    ).replace("{is_ostree}", "yes" if is_ostree else "no")

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
        if True:  # kickstart_config.should_use_native_firstboot:
            firstboot_line = "firstboot --enable"
        else:
            # KDE has no firstboot tool and Fedora's tool sucks. We use our own firstboot service instead
            firstboot_line = "firstboot --disable"
            lines.extend(_build_user_config(kickstart_config))

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
    """Build user configuration section with first-boot password setup."""

    is_ostree = "yes" if kickstart_config.ostree_args.strip() else "no"
    lines = [
        "user --name=temp --password='123' --plaintext --groups=wheel",
    ]

    lines.extend(
        load_ks_template("user_creation_tool")
        .replace("{username}", kickstart_config.user_username)
        .replace("{fullname}", kickstart_config.user_full_name)
        .replace("{is_ostree}", is_ostree)
        .splitlines()
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
    kickstart_lines.extend(_build_system_config(kickstart_config))
    kickstart_lines.extend(_build_install_source(kickstart_config))

    # Add CLEAN_DISK scripts if applicable
    if kickstart_config.partitioning.method == PartitioningMethod.CLEAN_DISK:
        kickstart_lines.extend(
            _build_clean_disk_pre_install(kickstart_config.partitioning)
        )
        kickstart_lines.extend(
            _build_clean_disk_post_install(
                kickstart_config.partitioning, bool(kickstart_config.ostree_args)
            )
        )

    # Final lines
    kickstart_lines.extend(["rootpw --lock", "reboot"])

    # Add final post section
    kickstart_lines.extend(load_ks_template("final_post").splitlines())

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
            is_in_submenu=True,
        ),
        GrubEntry(
            title="Install Fedora (RAM-Boot)",
            prelines=(),
            linux_cmd=f"linux /images/pxeboot/vmlinuz inst.stage2=hd:LABEL={root_partition_label} rd.live.check rd.live.ram quiet",
            initrd_cmd="initrd /images/pxeboot/initrd.img",
            is_in_submenu=True,
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
        "### Grub configuration generated by WinGone ###",
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
        grub_lines.append("submenu 'Other Options -->' {")
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
