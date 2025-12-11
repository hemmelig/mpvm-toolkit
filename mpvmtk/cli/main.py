"""
Top-level CLI for mpvm.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import typer

from .compute import app as compute_app
from .visualise import app as visualise_app


app = typer.Typer(help="MPVM Toolkit: multi-parameter volcano monitoring toolkit.")

app.add_typer(compute_app, name="compute")
app.add_typer(visualise_app, name="visualise")


def entrypoint():
    app()
