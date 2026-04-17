"""
Custom exceptions for mpvm.

:copyright:
    2026, Conor A. Bacon.
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

class ArchiveEmpty(Exception):
    """Raised when the archive is completely empty for a requested time period."""

    def __init__(self) -> None:
        super().__init__("archive empty for requested period")
