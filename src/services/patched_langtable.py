import os

if os.name == 'nt':
    import logging
    original_basicConfig = logging.basicConfig

    def patched_basicConfig(*args, **kwargs):
        if 'filename' in kwargs and kwargs['filename'] == '/dev/null':
            kwargs['filename'] = 'NUL'
        return original_basicConfig(*args, **kwargs)

    logging.basicConfig = patched_basicConfig

import langtable
# Expose langtable's API
__all__ = ['langtable']