"""
Collection of modules for visualising products of multi-parameter data.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from .magnetic import visualise_magnetic_field_summary
from .seismic import visualise_seismic_helicorder


__all__ = [
    "visualise_magnetic_field_summary",
    "visualise_seismic_helicorder",
]


def cm_to_in(value_in_cm: float) -> float:
    """Conversion utility from centimetres to inches."""

    return value_in_cm / 2.54
