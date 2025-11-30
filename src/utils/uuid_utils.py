class PartitionUuid:
    """
    Utility class for normalizing partition UUID/GUID formats.

    Provides static methods to convert UUIDs between different representations.
    """

    @staticmethod
    def to_raw(uuid: str) -> str:
        """
        Convert UUID to raw format (without braces).

        Args:
            uuid: UUID string (with or without braces)

        Returns:
            UUID without braces
        """
        return uuid.strip("{}")

    @staticmethod
    def to_bracketed(uuid: str) -> str:
        """
        Convert UUID to bracketed format (with braces).

        Args:
            uuid: UUID string (with or without braces)

        Returns:
            UUID with braces
        """
        raw = PartitionUuid.to_raw(uuid)
        return f"{{{raw}}}"

    @staticmethod
    def to_volume_path(uuid: str) -> str:
        """
        Convert UUID to volume path format.

        Args:
            uuid: UUID string (with or without braces)

        Returns:
            Volume path like \\\\?\\Volume{UUID}\\
        """
        bracketed = PartitionUuid.to_bracketed(uuid)
        return f"\\\\?\\Volume{bracketed}\\"
