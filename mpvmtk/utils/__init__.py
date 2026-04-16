"""
Module containing various utilities for mpvm.

:copyright:
    2025, Conor A. Bacon.
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from .config import read_config
from .datetime_generator import iter_time_chunks


__all__ = ["iter_time_chunks", "read_config"]
