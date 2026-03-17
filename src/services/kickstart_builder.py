"""Kickstart document and builder utilities.

This module encapsulates Kickstart generation as composable documents with
explicit include relationships, avoiding manual newline and file append logic.
"""

from __future__ import annotations

import posixpath
from pathlib import Path
from typing import TYPE_CHECKING

from core.settings import get_config
from models.partition import PartitioningMethod

if TYPE_CHECKING:
    from collections.abc import Iterable

    from models.kickstart import KickstartConfig, PartitioningConfig


def auto_quote(value: str) -> str:
    """Automatically quote a string if it contains spaces."""
    if " " in value:
        return f"'{value}'"
    return value


class KickstartDocument:
    """Represents one Kickstart file with optional include dependencies."""

    def __init__(self, relative_path: Path | str) -> None:
        self.relative_path = Path(relative_path)
        self._lines: list[str] = []
        self._includes: list[KickstartDocument] = []

    @classmethod
    def create_main(cls) -> KickstartDocument:
        return cls("ks.cfg")

    @classmethod
    def create_entry(cls, name: str) -> KickstartDocument:
        return cls(name)

    @classmethod
    def create_include(cls, name: str) -> KickstartDocument:
        return cls(Path("ks_includes") / f"{name}.ks")

    def add(self, *parts: str | Iterable[str]) -> KickstartDocument:
        for part in parts:
            if isinstance(part, str):
                self._lines.extend(part.splitlines())
            else:
                self._lines.extend(str(line) for line in part)
        return self

    def add_line(self, line: str) -> KickstartDocument:
        self._lines.append(line)
        return self

    def include(self, document: KickstartDocument) -> KickstartDocument:
        self._includes.append(document)

        # Entry files (ks.cfg, autoinstall.ks) use absolute paths for reliable execution
        # when copied to different paths by the runtime. Nested files within ks_includes
        # continue using relative paths.
        is_entry_file = self.relative_path.parent == Path()

        if is_entry_file:
            # Entry files use absolute paths to ensure reliable execution
            include_path = f"/run/install/repo/{document.relative_path.as_posix()}"
        else:
            # Nested includes within ks_includes use relative paths
            parent_dir = self.relative_path.parent.as_posix() or "."
            include_path = posixpath.relpath(
                document.relative_path.as_posix(),
                start=parent_dir,
            )

        self.add_line(f"%include {include_path}")
        return self

    def render(self) -> str:
        return "\n".join(self._lines) + "\n"

    def write(self, base_path: Path) -> None:
        self.write_recursive(base_path, seen=set())

    def write_recursive(self, base_path: Path, seen: set[Path]) -> None:
        absolute_path = (base_path / self.relative_path).resolve()
        if absolute_path in seen:
            return
        seen.add(absolute_path)

        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(self.render(), encoding="utf-8", newline="")

        for include_doc in self._includes:
            include_doc.write_recursive(base_path, seen)


class KickstartBuilder:
    """Builds Kickstart files using structured document composition."""

    def __init__(self, kickstart_config: KickstartConfig) -> None:
        self.kickstart_config = kickstart_config
        self.config_paths = get_config().paths

    def load_template(self, name: str) -> str:
        path = self.config_paths.install_helpers_ks_dir / f"{name}.ks"
        template = path.read_text()
        return template.replace("{log_dir}", self.config_paths.log_dir)

    def load_python_script(
        self,
        name: str,
        mode: str,
        options: tuple[str, ...] = (),
        template_vars: dict[str, str] | None = None,
    ) -> str:
        """Load a Python helper script and wrap it as a Kickstart script block."""
        if mode not in {"pre", "post"}:
            msg = f"Invalid kickstart script mode: {mode}"
            raise ValueError(msg)

        script_name = name if name.endswith(".py") else f"{name}.py"
        path = self.config_paths.install_helpers_scripts_dir / script_name
        script_content = path.read_text()

        header = (
            f"%{mode} --interpreter=/usr/bin/python3 "
            f"--logfile={self.config_paths.log_dir}/post_{path.stem}"
        )
        if options:
            header = f"{header} {' '.join(options)}"

        if template_vars:
            for key, value in template_vars.items():
                script_content = script_content.replace(f"{{{key}}}", value)

        return "\n".join((header, script_content, "%end"))

    def _validate_config(self) -> None:
        errors: list[str] = []

        if not self.kickstart_config.partitioning.method:
            errors.append("Partitioning method is required")

        partitioning = self.kickstart_config.partitioning
        if partitioning.method == PartitioningMethod.CLEAN_DISK:
            if not partitioning.sys_drive_uuid:
                errors.append(
                    "sys_drive_uuid is required for clean_disk partition method"
                )
            if not partitioning.sys_efi_uuid:
                errors.append(
                    "sys_efi_uuid is required for clean_disk partition method"
                )
            if not partitioning.tmp_part_uuid:
                errors.append(
                    "tmp_part_uuid is required for clean_disk partition method"
                )

        if errors:
            msg = f"Invalid kickstart configuration: {'; '.join(errors)}"
            raise ValueError(msg)

    def _build_clean_disk_pre_install(
        self, partitioning_config: PartitioningConfig
    ) -> list[str]:
        if not partitioning_config.sys_disk_uuid:
            msg = "sys_disk_uuid is required for clean_disk_pre"
            raise ValueError(msg)
        if not partitioning_config.tmp_part_uuid:
            msg = "tmp_part_uuid is required for clean_disk_pre"
            raise ValueError(msg)

        lines = self.load_python_script(
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
        self,
        partitioning_config: PartitioningConfig,
        is_ostree: bool,
    ) -> list[str]:
        if not partitioning_config.tmp_part_uuid:
            msg = "tmp_part_uuid is required for clean_disk_post_install"
            raise ValueError(msg)

        template = self.load_template("partition_resize_tool")
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

    def _build_user_config(self) -> list[str]:
        is_ostree = "yes" if self.kickstart_config.ostree_args.strip() else "no"
        lines = []

        lines.extend(
            self.load_template("user_creation_tool")
            .replace("{username}", self.kickstart_config.user_username)
            .replace("{fullname}", self.kickstart_config.user_full_name)
            .replace("{is_ostree}", is_ostree)
            .splitlines()
        )
        return lines

    def _build_system_config(self) -> list[str]:
        lines: list[str] = []
        locale_config = self.kickstart_config.locale_settings

        if locale_config.keymaps and locale_config.locale and locale_config.timezone:
            if self.kickstart_config.should_use_native_firstboot:
                firstboot_line = "firstboot --enable"
            else:
                firstboot_line = "firstboot --disable"
                lines.extend(self._build_user_config())
        else:
            firstboot_line = "firstboot --reconfig"
            if not locale_config.keymaps:
                locale_config.keymaps = ["us"]
            if not locale_config.locale:
                locale_config.locale = "en_US.UTF-8"
            if not locale_config.timezone:
                locale_config.timezone = "America/New_York"

        lines.append(firstboot_line)

        formatted_keymaps = []
        for keymap in locale_config.keymaps:
            if "(" in keymap and " (" not in keymap:
                keymap = keymap.replace("(", " (")
            formatted_keymaps.append(keymap)
        quoted_keymaps = [auto_quote(keymap) for keymap in formatted_keymaps]
        lines.append(f"keyboard --xlayouts={','.join(quoted_keymaps)}")

        lines.extend(
            [
                f"lang {locale_config.locale}",
                "firewall --use-system-defaults",
                f"timezone {locale_config.timezone} --utc",
            ]
        )

        return lines

    def _build_install_source(self) -> list[str]:
        lines = []
        if self.kickstart_config.ostree_args:
            lines.append(f"ostreesetup {self.kickstart_config.ostree_args}")
        if self.kickstart_config.live_img_url:
            lines.append(
                f"liveimg --url='{self.kickstart_config.live_img_url}' --noverifyssl"
            )
        return lines

    def _build_autoinstall_content_lines(self) -> list[str]:
        method = self.kickstart_config.partitioning.method

        lines: list[str] = []
        lines.extend(self._build_system_config())
        lines.extend(["rootpw --lock", "reboot"])

        if method == PartitioningMethod.CLEAN_DISK:
            lines.extend(
                self._build_clean_disk_pre_install(self.kickstart_config.partitioning)
            )
            lines.extend(
                self._build_clean_disk_post_install(
                    self.kickstart_config.partitioning,
                    bool(self.kickstart_config.ostree_args),
                )
            )

        lines.extend(self.load_template("final_post").splitlines())
        return lines

    def _build_base_content_lines(self, include_autoinstall: bool) -> list[str]:
        lines: list[str] = []
        if include_autoinstall:
            lines.extend(self.load_template("header_autoinst").splitlines())
        else:
            lines.extend(self.load_template("header_custom").splitlines())
        lines.extend(self._build_install_source())
        return lines

    def _create_nested_include(
        self,
        parent_include_name: str,
        section_name: str,
        content: str | Iterable[str],
    ) -> KickstartDocument:
        nested_path = (
            Path("ks_includes") / f"{parent_include_name}_incl" / f"{section_name}.ks"
        )
        doc = KickstartDocument(nested_path)
        doc.add(content)
        return doc

    def build_autoinstall_document(
        self, include_name: str = "autoinstall"
    ) -> KickstartDocument:
        self._validate_config()

        method = self.kickstart_config.partitioning.method
        doc = KickstartDocument.create_include(include_name)

        doc.include(
            self._create_nested_include(
                include_name,
                "system",
                self._build_system_config(),
            )
        )
        doc.include(
            self._create_nested_include(
                include_name,
                "boot_actions",
                ["rootpw --lock", "reboot"],
            )
        )

        if method == PartitioningMethod.CLEAN_DISK:
            doc.include(
                self._create_nested_include(
                    include_name,
                    "clean_disk_pre",
                    self._build_clean_disk_pre_install(
                        self.kickstart_config.partitioning
                    ),
                )
            )
            doc.include(
                self._create_nested_include(
                    include_name,
                    "clean_disk_post",
                    self._build_clean_disk_post_install(
                        self.kickstart_config.partitioning,
                        bool(self.kickstart_config.ostree_args),
                    ),
                )
            )

        doc.include(
            self._create_nested_include(
                include_name,
                "final_post",
                self.load_template("final_post"),
            )
        )
        return doc

    def build_base_document(
        self,
        relative_path: str,
        include_autoinstall: bool,
    ) -> KickstartDocument:
        doc = KickstartDocument.create_entry(relative_path)
        doc.add(self._build_base_content_lines(include_autoinstall))
        if include_autoinstall:
            doc.include(self.build_autoinstall_document())
        return doc

    def build_documents(self) -> list[KickstartDocument]:
        method = self.kickstart_config.partitioning.method
        is_autoinstall = method != PartitioningMethod.CUSTOM

        if is_autoinstall:
            return [
                self.build_base_document(
                    relative_path="ks.cfg",
                    include_autoinstall=False,
                ),
                self.build_base_document(
                    relative_path="autoinstall.ks",
                    include_autoinstall=True,
                ),
            ]
        return [
            self.build_base_document(
                relative_path="ks.cfg",
                include_autoinstall=False,
            )
        ]

    def build_document_tree(self) -> KickstartDocument:
        return self.build_base_document(
            relative_path="ks.cfg",
            include_autoinstall=False,
        )

    def write_files(self, base_path: Path) -> None:
        for document in self.build_documents():
            document.write(base_path)

    def render_autoinstall_content(self) -> str:
        self._validate_config()
        return "\n".join(self._build_autoinstall_content_lines()) + "\n"

    def render_base_content(self) -> str:
        method = self.kickstart_config.partitioning.method
        is_autoinstall = method != PartitioningMethod.CUSTOM
        return "\n".join(self._build_base_content_lines(is_autoinstall)) + "\n"


def build_autoinstall_ks_file(kickstart_config: KickstartConfig) -> str:
    """Build only autoinstall Kickstart file content for compatibility."""
    return KickstartBuilder(kickstart_config).render_autoinstall_content()


def build_base_ks_file(kickstart_config: KickstartConfig) -> str:
    """Build base Kickstart file content for compatibility."""
    return KickstartBuilder(kickstart_config).render_base_content()


def write_ks_files(kickstart_config: KickstartConfig, base_path: Path) -> None:
    """Write Kickstart file tree to disk.

    When autoinstall is enabled, writes both entry files:
    - `autoinstall.ks` (autoinstall entry)
    - `ks.cfg` (non-autoinstall fallback entry)
    """
    KickstartBuilder(kickstart_config).write_files(base_path)
