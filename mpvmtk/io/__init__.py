"""
Input/output module containing utilities for reading multi-parameter datastreams.

:copyright:
    2025, Conor A. Bacon
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, TYPE_CHECKING

import obspy

from .miniseed import make_waveform_client, WaveformClient
from .stationxml import make_response_client, ResponseClient


if TYPE_CHECKING:
    from datetime import datetime as dt


__all__ = ["make_response_client", "make_waveform_client"]


@dataclass(slots=True)
class WaveformReadResult:
    stream: obspy.Stream
    inventory: obspy.Inventory | None = None


@dataclass(slots=True)
class WaveformReader:
    waveform_client: WaveformClient
    response_client: ResponseClient | None = None

    def get_waveforms(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
        starttime: dt,
        endtime: dt,
        *,
        with_inventory: bool = False,
    ) -> WaveformReadResult:
        """
        Read waveform data, optionally alongside matching response metadata.

        Parameters
        ----------
        network:
            FDSN network code.
        station:
            FDSN station code.
        location:
            FDSN location code.
        channels:
            FDSN channel code or pattern.
        starttime:
            Start of waveform request as a stdlib datetime.
        endtime:
            End of waveform request as a stdlib datetime.
        with_inventory:
            If True, also fetch matching instrument metadata.

        Returns
        -------
        WaveformReadResult
            Result containing the waveform Stream and, optionally, an Inventory.
        """

        stream = self.waveform_client.get_waveforms(
            network=network,
            station=station,
            location=location,
            channels=channels,
            starttime=obspy.UTCDateTime(starttime),
            endtime=obspy.UTCDateTime(endtime),
        )

        inventory: obspy.Inventory | None = None
        if with_inventory:
            if self.response_client is None:
                raise ValueError(
                    "with_inventory=True but no response_client is configured",
                )

            inventory = self.response_client.get_inventory(
                network=network,
                station=station,
                location=location,
                channels=channels,
                starttime=starttime,
                endtime=endtime,
            )

        return WaveformReadResult(stream=stream, inventory=inventory)


def make_waveform_reader(config: Mapping[str, Any]) -> WaveformReader:
    waveform_client = make_waveform_client(config["waveform"])

    response_client = None
    if "response" in config:
        response_client = make_response_client(config["response"])

    return WaveformReader(
        waveform_client=waveform_client,
        response_client=response_client,
    )
