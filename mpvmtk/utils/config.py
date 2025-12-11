"""
Utilities for reading configuration information.

:copyright:
    2025, Conor A. Bacon.
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
import tomllib


def read_config(config_file: pathlib.Path) -> dict:
    """Utility function to read in configuration for the node/hub."""

    if not config_file.is_file():
        raise FileNotFoundError

    with config_file.open("rb") as f:
        config = tomllib.load(f)

    return config
