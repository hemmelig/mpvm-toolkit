"""
Input/output module containing utilities for reading multi-parameter datastreams.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from .miniseed import make_waveform_client


__all__ = [make_waveform_client]
