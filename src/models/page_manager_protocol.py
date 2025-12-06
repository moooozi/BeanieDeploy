from typing import Protocol


class PageManagerProtocol(Protocol):
    """Protocol for page manager interface used by pages."""

    def set_title(self, text: str) -> None: ...

    def set_primary_button(
        self, text: str | None = None, command=None, visible: bool = True
    ) -> None: ...

    def set_secondary_button(
        self, text: str | None = None, command=None, visible: bool = True
    ) -> None: ...
