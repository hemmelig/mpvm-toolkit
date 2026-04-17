"""
Helicorder visualisation for mpvm.

The helicorder has no compute stage: it reads raw waveform data, applies optional
preprocessing, then renders the drum plot.

:copyright:
    2026, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
import sys
from datetime import date as _date, datetime as dt, timedelta as td, UTC
from importlib.resources import files
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import obspy
from matplotlib.ticker import MultipleLocator

from mpvmtk.io import make_waveform_client
from mpvmtk.utils.exceptions import ArchiveEmpty


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

    if config.get("stylesheet"):
        plt.style.use(config["stylesheet"])
    else:
        plt.style.use(files("mpvmtk.styles") / "helicorder.mplstyle")

    network = config["site"]["network"]
    station = config["site"]["station"]
    location = config["site"]["location"]
    channels = config["site"]["channels"]
    seed_id = ".".join([network, station, location, channels])

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
        f"Building helicorder:\n"  
        f"  Network: {network}\n"
        f"  Station: {station}\n"
        f"     Date: {starttime.date()}"
    )

    client = make_waveform_client(config["waveforms"])
    print("   ...loading waveform data...", end="")
    try:
        st = client.get_waveforms(
            network, station, location, channels, starttime, endtime
        )
    except ArchiveEmpty as e:
        print(f"{e}. Exiting.")
        sys.exit(1)
    print("success!")

    preprocessed_st = st.copy()
    preprocess = config.get("preprocess", {})

    if "detrend" in preprocess:
        for mode in config["preprocess"]["detrend"]:
            preprocessed_st.detrend(mode)

    if "filters" in preprocess:
        for _, params in preprocess["filters"].items():
            preprocessed_st = preprocessed_st.filter(**params)

    response_removal_config = preprocess.get("remove_response")
    if response_removal_config:
        inventory = obspy.read_inventory(response_removal_config["inventory"])
        preprocessed_st.remove_response(
            inventory=inventory,
            output=response_removal_config.get("output", "VEL"),
            water_level=response_removal_config.get("water_level"),
            pre_filt=response_removal_config.get("pre_filt"),
            zero_mean=response_removal_config.get("zero_mean", True),
            taper=response_removal_config.get("taper", True),
            taper_fraction=response_removal_config.get("taper_fraction", 0.05),
        )

    fig, ax = plt.subplots()
    ax = _plot_helicorder(ax, preprocessed_st, starttime.date(), config)

    fig.suptitle("")
    fname = f"{seed_id}-{starttime.date().isoformat()}_seismic-helicorder.png"
    fig.savefig(archive_path / fname)
    print("complete.")


def _plot_helicorder(
    ax: plt.Axes, st: obspy.Stream, date: _date, config: dict
) -> plt.Axes:
    """
    Constructs a figure depicting the helicorder for a given station on a given day.

    Parameters
    ----------
    ax:
        The Matplotlib axes on which to plot the helicorder.
    st:
        ObsPy Stream object containing the data that has been loaded from the archive.
    date:
        The date being visualised.
    config:
        The config file for the visualisation.

    Returns
    -------
     :
        A Matplotlib Axes object depicting the requested helicorder plot.

    """

    print("   ...constructing helicorder plot...", end="")

    interval = config.get("interval", 15)  # In minutes
    lines = int((24 * 60) / interval)
    starttime = obspy.UTCDateTime(date)

    amplitude_config = config.get("amplitude", {})
    velocity_scale = amplitude_config.get("velocity_scale_mps", 1e-6)
    clip_lines = amplitude_config.get("clip_lines", 3.0)
    mode = amplitude_config.get("mode", "soft")

    if velocity_scale <= 0:
        raise ValueError("amplitude.velocity_scale_mps must be > 0")

    clrs = iter(plt.cm.magma(np.linspace(0, lines, lines + 1) % 4 / 4))
    for y_offset, clr in zip(range(lines, -1, -1), clrs):
        interval_s = interval * 60
        stream_line = st.slice(
            starttime=starttime,
            endtime=starttime + interval_s,
        )
        for tr in stream_line:
            scaled = _scale_amplitude(
                tr.data,
                velocity_scale_mps=velocity_scale,
                clip_lines=clip_lines,
                mode=mode,
            )
            ax.plot(
                tr.times(reftime=starttime) / 60,
                scaled + y_offset,
                color=clr,
                # linewidth=1,
            )
        starttime += interval_s

    ax.set_xlim([0, interval])
    ax.set_xlabel(
        f"Time in minutes  |  +/-1 line = {velocity_scale * 1e6:.1f} µm/s"
    )
    ax.xaxis.set_major_locator(MultipleLocator(interval / 15))
    ax.xaxis.set_minor_locator(MultipleLocator(1))

    ax.set_ylim([0, lines + 1])
    ax.set_yticks(range(int(60 / interval), lines + 1, int(60 / interval)))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ylabels = [f"{hour:02}:00" for hour in range(23, -1, -1)]
    ax.set_yticklabels(ylabels)

    title = f"{st[0].id} - {date}"
    if config.get("preprocess", {}).get("remove_response"):
        title += " (ground velocity)"
    ax.set_title(title)

    return ax


def _scale_amplitude(
    data: np.ndarray,
    velocity_scale_mps: float,
    clip_lines: float | None = None,
    mode: Literal["none", "soft", "hard"] = "soft",
) -> np.ndarray:
    """
    Convert ground velocity (m/s) to helicorder line units.

    Parameters
    ----------
    data:
        Input trace data (in m/s).
    velocity_scale_mps:
        Reference amplitude for +/-1 line height.
    clip_lines:
        Maximum excursion in line units (None = no clipping).
    mode:
        "none", "hard", or "soft".

    Returns
    -------
    scaled_data:
        Scaled data in line units.

    """

    amp = data / velocity_scale_mps

    if clip_lines is None or mode == "none":
        return amp

    if mode == "hard":
        return np.clip(amp, -clip_lines, clip_lines)

    if mode == "soft":
        return clip_lines * np.tanh(amp / clip_lines)

    raise ValueError(f"Unknown amplitude scaling mode: {mode}")
