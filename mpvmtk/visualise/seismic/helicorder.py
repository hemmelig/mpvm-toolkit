"""
Helicorder visualisation for mpvm.

The helicorder has no compute stage: it reads raw waveform data, applies optional
filtering, then renders the drum plot.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
import sys
from datetime import datetime as dt, timedelta as td, UTC

import matplotlib.pyplot as plt
import numpy as np
import obspy
from matplotlib.ticker import MultipleLocator

from mpvmtk.io import read_miniseed_archive


def visualise_seismic_helicorder(config: dict, date: str | None) -> None:
    """
    Public entrypoint used by CLI.

    Parameters
    ----------
    config:
        Dictionary containing visualisation configuration.
    date:
        YYYY-MM-DD string, or None (meaning today).

    """

    plt.style.use(config["stylesheet"])

    network = config["site"]["network"]
    station = config["site"]["station"]
    location = config["site"]["location"]
    channels = config["site"]["channels"]

    if date is None:
        starttime = dt.combine(dt.now(UTC).date(), dt.min.time())
    else:
        starttime = dt.strptime(date, "%Y-%m-%d")
    endtime = starttime + td(days=1)

    archive_path = pathlib.Path(config["products"]) / config["products_format"].format(
        stream="seismic/helicorders",
        network=network,
        station=station,
    )
    archive_path.mkdir(parents=True, exist_ok=True)

    print(
        f"Building helicorder:\n  Network: {network}\n"
        f"  Station: {station}\n"
        f"     Date: {starttime.date()}"
    )

    print("   ...loading waveform data from archive...", end="")
    st = read_miniseed_archive(
        network,
        station,
        location,
        channels,
        starttime=starttime,
        endtime=endtime,
        archive=pathlib.Path(config["archive"]),
        archive_fmt=config["archive_format"],
    )

    if not st:
        print("no data available. Exiting.")
        sys.exit(1)

    print("success!")

    if "detrend" in config["preprocess"].keys():
        for mode in config["preprocess"]["detrend"]:
            st.detrend(mode)

    tmp_st = st.copy()
    if "filters" in config["preprocess"].keys():
        for _, params in config["preprocess"]["filters"].items():
            tmp_st = tmp_st.filter(**params)
    filtered_st = tmp_st

    fig, ax = plt.subplots(1, figsize=(9, 11), constrained_layout=True)
    ax = _plot_helicorder(ax, filtered_st, config)

    fig.suptitle("")
    fname = (
        f"{filtered_st[0].id}-{starttime.strftime('%Y-%m-%d')}"
        "_seismic-helicorder.png"
    )
    fig.savefig(archive_path / fname, dpi=400)

    print(f"complete.")


def _plot_helicorder(ax: plt.Axes, st: obspy.Stream, config: dict) -> plt.Axes:
    """
    Constructs a figure depicting the helicorder for a given station on a given day.

    Parameters
    ----------
    ax:
        The Matplotlib axes on which to plot the helicorder.
    st:
        ObsPy Stream object containing the data that has been loaded from the archive.
    config:
        The config file for the visualisation.

    Returns
    -------
     :
        A Matplotlib Axes object depicting the requested helicorder plot.

    """

    print("   ...constructing helicorder plot...", end="")
    norm_factor = config["norm_factor"]
    current_max = 0
    for tr in st:
        max_val = max(abs(tr.data))
        current_max = max(current_max, max_val)
    norm_factor = current_max / norm_factor

    interval = config["interval"]  # In minutes
    lines = int((24 * 60) / interval)
    starttime = obspy.UTCDateTime(st[0].stats.starttime.date)

    clrs = iter(plt.cm.magma(np.linspace(0, lines, lines + 1) % 4 / 4))
    for y_offset, clr in zip(range(lines, -1, -1), clrs):
        interval_s = interval * 60
        stream_line = st.slice(
            starttime=starttime,
            endtime=starttime + interval_s,
        )
        for tr in stream_line:
            ax.plot(
                tr.times(reftime=starttime) / 60,
                tr.data / norm_factor + y_offset,
                color=clr,
                linewidth=1,
            )
        starttime += interval_s

    ax.set_xlim([0, interval])
    ax.set_xlabel("Time in minutes")
    ax.xaxis.set_major_locator(MultipleLocator(interval / 15))
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    ax.set_ylim([0, lines + 1])
    ax.set_yticks(range(int(60 / interval), lines + 1, int(60 / interval)))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ylabels = [f"{hour:02}:00" for hour in range(23, -1, -1)]
    ax.set_yticklabels(ylabels)

    ax.set_title(f"{st[0].id} - {st[0].stats.starttime.date}")

    return ax
