"""
Input/output module for working with miniSEED data stored in either:

    - a local filesystem archive with a regular directory path pattern
    - a remote server operating an FDSN webservice for data access

:copyright:
    2026, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta as td
from typing import Any, Mapping, Protocol

import obspy
from obspy.clients.fdsn import Client as FDSNClient
try:
    from seismonpy.norsardb import Client as SeisMonClient

    SEISMON_AVAILABLE = True
except ImportError:
    print("SeisMonPy not available.")
    SEISMON_AVAILABLE = False


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
    path: pathlib.Path
    format: str

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
            glob_path = self.format.format(
                network=network,
                station=station,
                location=location,
                channels=channels,
                datetime=read_from,
                year=read_from.year,
                jday=read_from.timetuple().tm_yday,
            )
            for data_file in self.path.glob(glob_path):
                st += obspy.read(data_file)

            read_from += td(days=1)

        if not st:
            raise ValueError

        st.merge(method=-1)
        st.trim(
            starttime=obspy.UTCDateTime(starttime) - pre_pad,
            endtime=obspy.UTCDateTime(endtime) + post_pad - st[0].stats.delta,
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


@dataclass(slots=True)
class SeismonWaveformClientWrapper:

    db_path: str | None = None
    db_archive_path: str | None = None
    inventories_path: str | None = None
    cache_waveforms: bool | None = None
    load_response: bool | None = None
    inventory_index_path: str | None = None
    noresponse_inventory_path: str | None = None
    response_inventory_path: str | None = None
    static_xml_inventory_path: str | None = None
    index_path: str | None = None

    _client: SeisMonClient = field(init=False)

    def __post_init__(self) -> None:
        if not SEISMON_AVAILABLE:
            raise ImportError("seismonpy is not available in this environment")

        # Build kwargs from dataclass fields that are not None
        kwargs: dict[str, Any] = {
            "db_path": self.db_path,
            "db_archive_path": self.db_archive_path,
            "inventories_path": self.inventories_path,
            "cache_waveforms": self.cache_waveforms,
            "load_response": self.load_response,
            "inventory_index_path": self.inventory_index_path,
            "noresponse_inventory_path": self.noresponse_inventory_path,
            "response_inventory_path": self.response_inventory_path,
            "static_xml_inventory_path": self.static_xml_inventory_path,
            "index_path": self.index_path,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        self._client = SeisMonClient(**kwargs)

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
        Passthrough for the SeisMonPy Client `get_waveforms` method.

        Parameters
        ----------
        network:
            The network code of data to be loaded from the SeisMon Client.
        station:
            The station code of data to be loaded from the SeisMon Client.
        location:
            The location code of data to be loaded from the SeisMon Client.
        channels:
            The FDSN channel codes of data to be loaded from the SeisMon Client.
        starttime:
            First timestamp of data to be loaded from the SeisMon Client.
        endtime:
            Final timestamp of data to be loaded from the SeisMon Client.
        pre_pad:
            Optional time-padding to account for potential tapering.
        post_pad:
            Optional time-padding to account for potential tapering.

        Returns
        -------
        st:
            Stream containing the data that has been loaded from the SeisMon Client.

        """

        starttime = obspy.UTCDateTime(starttime) - pre_pad
        endtime = obspy.UTCDateTime(endtime) + post_pad

        return self._client.get_waveforms(station, channels, starttime, endtime)


def make_waveform_client(config: Mapping[str, Any]) -> WaveformClient:
    """
    Factory function for creating a WaveformClient from a config file.

    Parameters
    ----------
    config:
        The config specifying the waveform data access client.

    Returns
    -------
    client:
        A local, FDSN, or SeisMon waveform client.

    """

    match mode := config["client"]:
        case "local":
            local = config["local"]
            return LocalArchiveClient(
                path=pathlib.Path(local["path"]),
                format=local["format"],
            )
        case "fdsn":
            remote = config["fdsn"]
            return FDSNWaveformClientWrapper(
                base_url=remote["base_url"],
                timeout=int(remote.get("timeout", 60)),
            )
        case "seismon":
            if not SEISMON_AVAILABLE:
                raise RuntimeError("data.client='seismon' but seismonpy is not installed")
            remote = config.get("seismon", {})
            return SeismonWaveformClientWrapper(**remote)
        case _:
            raise ValueError(f"Unknown data.client={mode!r}")
