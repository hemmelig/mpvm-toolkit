"""
Magnetic field summary visualisation for mpvm.

Plots the three magnetic-field vector components and the total field intensity
for a given station over a requested time span.

:copyright:
    2026, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

import pathlib
import sys
from datetime import UTC, datetime as dt, timedelta as td

import matplotlib.pyplot as plt
import numpy as np
import obspy

from mpvmtk.io import make_waveform_client


CORRECTION_FACTORS = {
    "IRIS": 10 * (20 / 2**23),
    "IMF": 1 / 10000,
}


def visualise_magnetic_field_summary(
    config: dict,
    starttime: str,
    endtime: str,
) -> None:
    """
    Public entrypoint used by CLI.

    Parameters
    ----------
    config:
        Dictionary containing visualisation configuration.
    starttime:
        YYYY-MM-DD string.
    endtime:
        YYYY-MM-DD string.

    """

    plt.style.use(config["stylesheet"])

    network = config["site"]["network"]
    station = config["site"]["station"]
    location = config["site"].get("location", "")
    channels = config["site"].get("channels", "*F*")
    partial_seed_id = ".".join(network, station, location)
    correction_name = config["magnetic"]["correction_factor"]

    if starttime is None or endtime is None:
        raise ValueError("must provide both --starttime and --endtime.")
    start_dt = dt.strptime(starttime, "%Y-%m-%d").replace(tzinfo=UTC)
    end_dt = dt.strptime(endtime, "%Y-%m-%d").replace(tzinfo=UTC) + td(days=1)

    archive_path = pathlib.Path(config["products"]) / config["products_format"].format(
        stream="magnetic/summary",
        network=network,
        station=station,
    )
    archive_path.mkdir(parents=True, exist_ok=True)

    print(
        "Building magnetic field summary:\n"
        f" Network: {network}\n"
        f" Station: {station}\n"
        f"   Start: {start_dt.date()}\n"
        f"     End: {end_dt.date()}"
    )

    client = make_waveform_client(config["data"])
    print(" ...loading magnetic field data...", end="")
    st = client.get_waveforms(
        network,
        station,
        location,
        channels,
        start_dt,
        end_dt,
    )

    if not st:
        print("no data available. Exiting.")
        sys.exit(1)

    print("success!")

    fig, axes = plt.subplots(
        ncols=1,
        nrows=4,
        figsize=(17.5 / 2.54, 17 / 2.54),
        sharex=True,
        constrained_layout=True,
    )
    axes = dict(zip(["Z", "N", "E", "INTENSITY"], axes, strict=True))

    axes = _plot_magnetic_field_summary(
        axes,
        st=st,
        correction_factor=CORRECTION_FACTORS[correction_name],
    )

    fig.suptitle(
        f"Magnetic field strength - {partial_seed_id} "
        f"for {start_dt.date()} to {(end_dt - td(days=1)).date()}"
    )

    fname_ext = (
        f"{start_dt.year}.{start_dt.timetuple().tm_yday:03d}-"
        f"{end_dt.year}.{end_dt.timetuple().tm_yday:03d}"
    )
    filename = f"{partial_seed_id}_{fname_ext}_magnetic-field.png"
    fig.savefig(archive_path / filename, dpi=400)
    print("complete.")


def _plot_magnetic_field_summary(
    axes: list[plt.Axes],
    st: obspy.Stream,
    correction_factor: float,
) -> plt.Axes:
    """
    Construct a figure with the three vector components and total intensity between two
    timestamps.

    Parameters
    ----------
    axes:
        Matplotlib Axes on which to visualise magnetic field summary.
    st:
        Magnetic waveform data to be visualised.
    correction_factor:
        Conversion from raw counts to microTesla.

    Returns
    -------
    axes:
        Matplotlib Axes with magnetic field summary visualised.

    """

    component_limits = None

    for component, c in zip("ZNE", ["#089099", "#089099", "#089099"]):
        ax = axes[component]
        st_tmp = st.select(component=component)
        for tr in st_tmp:
            data = np.asarray(tr.data, dtype=float) * correction_factor
            data[data > 999] = np.nan
            data[data < -999] = np.nan
            ax.plot(tr.times("matplotlib"), data, c=c)

        min_starttime = min(tr.stats.starttime for tr in st_tmp).datetime
        max_endtime = max(tr.stats.endtime for tr in st_tmp).datetime
        component_limits = (min_starttime, max_endtime)

        ax.text(
            0.015,
            0.08,
            f"{component}-component",
            ha="left",
            va="center",
            transform=ax.transAxes,
            fontweight="bold",
            color=c,
        )
        ax.set_ylabel(r"Magnetic field strength / $\mu$T")

    st = st.copy()
    st.merge(method=0, fill_value=0)

    ax = axes["INTENSITY"]
    intensity = np.array(
        [
            correction_factor * (x**2 + y**2 + z**2) ** 0.5
            if x != 0 and y != 0 and z != 0
            else 0
            for x, y, z in zip(
                st.select(component="E")[0].data,
                st.select(component="N")[0].data,
                st.select(component="Z")[0].data,
            )
        ]
    )
    intensity[intensity == 0] = np.nan
    intensity[intensity > 100] = np.nan
    intensity[intensity < 20] = np.nan

    ax.plot(st[0].times("matplotlib"), intensity, c="#045275")
    ax.set_ylabel(r"Total field intensity / $\mu$T")
    if component_limits is not None:
        ax.set_xlim(component_limits)
    ax.set_xlabel("Datetime")

    return axes
