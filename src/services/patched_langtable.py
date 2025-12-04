import os

if os.name == "nt":
    import logging

    original_basic_config = logging.basicConfig

    def patched_basic_config(*args, **kwargs):
        if "filename" in kwargs and kwargs["filename"] == "/dev/null":
            kwargs["filename"] = "NUL"
        return original_basic_config(*args, **kwargs)

    logging.basicConfig = patched_basic_config

import langtable  # type: ignore
from langtable.langtable import _keyboards_db as keyboards_db  # type: ignore

# Expose langtable's API
langtable.keyboards_db = keyboards_db  # type: ignore
__all__ = ["langtable"]
