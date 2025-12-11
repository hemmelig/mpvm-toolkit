"""
Visualisation subcommands for mpvm.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib

import typer

from mpvmtk.utils import read_config
from mpvmtk.visualise.seismic import visualise_seismic_helicorder


app = typer.Typer(help="Generate visual products for multi-parameter data.")


@app.command("seismic-helicorder")
def helicorder_cmd(
    config_path: pathlib.Path = typer.Option(
        ..., "--config", "-c", help="TOML config file."
    ),
    date: str = typer.Option(
        None, "--date", "-d", help="YYYY-MM-DD, defaults to today."
    ),
):
    """
    Top-level dispatch command for building seismic helicorder visualisations.

    Parameters
    ----------
    config_path:
        Path to the TOML configuration file.
    date:
        The date for which to produce the helicorder visualisation.

    """

    config = read_config(config_path)

    visualise_seismic_helicorder(config=config, date=date)
