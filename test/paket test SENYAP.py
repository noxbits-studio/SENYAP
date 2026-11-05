"""Paket test SENYAP.

Menambahkan direktori induk ke sys.path agar modul scraper bisa diimpor datar
(`import config`, `import client`, dan seterusnya) tanpa memasang paket.
"""

import os
import sys

_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
