"""
Input/output module for working with miniSEED data stored in either:

    - a local filesystem archive with a regular directory path pattern
    - a remote server operating an FDSN webservice for data access

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from typing import Protocol

import obspy
from obspy.clients.fdsn import Client as FDSNClient


class WaveformClient(Protocol):
    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream: ...


@dataclass(slots=True)
class LocalArchiveClient:
    archive: pathlib.Path
    archive_format: str

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Read data from a local waveform archive.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the archive.
        station:
            The station code of data to be loaded from the archive.
        location:
            The location code of data to be loaded from the archive.
        channels:
            The FDSN channel codes of data to be loaded from the archive.
        starttime:
            First timestamp of data to be loaded from the archive.
        endtime:
            Final timestamp of data to be loaded from the archive.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the archive.

        """

        st = obspy.Stream()
        read_from = starttime - td(seconds=pre_pad)
        while read_from.date() <= (endtime + td(seconds=post_pad)).date():
            glob_path = self.archive_fmt.format(
                network=network,
                station=station,
                location=location,
                channels=channels,
                datetime=read_from,
                year=read_from.year,
                jday=read_from.timetuple().tm_yday,
            )
            data_files = self.archive.glob(glob_path)
            for data_file in data_files:
                st += obspy.read(data_file)

            read_from += td(days=1)

        st.merge(method=-1)
        st.trim(
            starttime=obspy.UTCDateTime(starttime.date()) - pre_pad,
            endtime=obspy.UTCDateTime(endtime.date()) + post_pad - st[0].stats.delta,
        )

        return st


@dataclass(slots=True)
class FDSNWaveformClientWrapper:
    base_url: str
    timeout: int = 60
    _client: FDSNClient = field(init=False)

    def __post_init__(self) -> None:
        self._client = FDSNClient(self.base_url, timeout=self.timeout)

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        pre_pad: float = 0.0,
        post_pad: float = 0.0,
    ) -> obspy.Stream:
        """
        Passthrough for the ObsPy FDSN Client `get_waveforms` method.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the remote FDSN server.
        station:
            The station code of data to be loaded from the remote FDSN server.
        location:
            The location code of data to be loaded from the remote FDSN server.
        channels:
            The FDSN channel codes of data to be loaded from the remote FDSN server.
        starttime:
            First timestamp of data to be loaded from the remote FDSN server.
        endtime:
            Final timestamp of data to be loaded from the remote FDSN server.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the remote FDSN server.

        """

        starttime = obspy.UTCDateTime(starttime) - pre_pad
        endtime = obspy.UTCDateTime(endtime) + post_pad

        return self._client.get_waveforms(
            network, station, location, channels, starttime, endtime
        )


def make_waveform_client(config: dict) -> WaveformClient:
    """
    Factory function for creating a WaveformClient from a config file.

    Parameters
    ----------
    config:
        The config specifying the waveform data access client.

    Returns
    -------
    client:
        A local or FDSN waveform client.

    """

    mode = config["client"]

    if mode == "local":
        local = config["local"]
        return LocalArchiveClient(
            archive=pathlib.Path(local["archive"]),
            archive_format=local["archive_format"],
        )

    if mode == "fdsn":
        remote = config["fdsn"]
        return FDSNWaveformClientWrapper(
            base_url=remote["base_url"],
            timeout=int(remote.get("timeout", 60)),
        )

    raise ValueError(f"Unknown data.client={mode!r}")
