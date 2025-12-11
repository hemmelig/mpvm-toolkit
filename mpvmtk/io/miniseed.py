"""
Input/output module for working with miniSEED data stored in a filesystem archive with a
regular directory path pattern.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

import pathlib
from datetime import datetime as dt, timedelta as td

import obspy


def read_archive(
    network: str,
    station: str,
    location: str,
    channels: str,
    starttime: dt,
    endtime: dt,
    archive: pathlib.Path,
    archive_fmt: str,
    pre_pad: float = 0,
    post_pad: float = 0,
) -> obspy.Stream:
    """
    Read data from a waveform archive.

    Parameters
    ----------
    station:
        The station code of data to be loaded from the archive.
    network:
        The network code of data to be loaded from the archive.
    location:
        The location code of data to be loaded from the archive.
    channels:
        The FDSN channel codes of data to be loaded from the archive.
    starttime:
        First timestamp of data to be loaded from the archive.
    endtime:
        Final timestamp of data to be loaded from the archive.
    archive:
        Path to the data archive.
    archive_fmt:
        Path structure of the archive from which data is to be loaded.

    Returns
    -------
    st:
        ObsPy Stream object containing the data that has been loaded from the archive.

    """

    st = obspy.Stream()
    read_from = starttime - td(seconds=pre_pad)
    while read_from.date() <= (endtime + td(seconds=post_pad)).date():
        glob_path = archive_fmt.format(
            network=network,
            station=station,
            location=location,
            channels=channels,
            datetime=read_from,
            year=read_from.year,
            jday=read_from.timetuple().tm_yday,
        )
        data_files = archive.glob(glob_path)
        for data_file in data_files:
            st += obspy.read(data_file)

        read_from += td(days=1)

    st.merge(method=-1)
    st.trim(
        starttime=obspy.UTCDateTime(starttime.date()) - pre_pad,
        endtime=obspy.UTCDateTime(endtime.date()) + post_pad - st[0].stats.delta,
    )

    return st
