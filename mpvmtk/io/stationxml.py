"""
Input/output module for working with stationXML files data stored in either:

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
from typing import Any, Iterable, Mapping, Protocol
from dataclasses import dataclass, field

import obspy
from obspy.clients.fdsn import Client as FDSNClient
try:
    from seismonpy.norsardb import Client as SeisMonClient

    SEISMON_AVAILABLE = True
except ImportError:
    print("SeisMonPy not available.")
    SEISMON_AVAILABLE = False


class ResponseClient(Protocol):
    def get_inventory(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
    ) -> obspy.Inventory: ...


@dataclass(slots=True)
class StationXMLResponseClient:
    paths: tuple[pathlib.Path, ...]
    cache: bool = True
    _inventory: obspy.Inventory | None = field(init=False, default=None)
    _inventory_cache: dict[tuple, obspy.Inventory] = field(init=False, default_factory=dict)

    def _load(self) -> obspy.Inventory:
        """Load and merge all stationXML files once."""

        if self._inventory is None:
            self._inventory = _merge_inventories(
                [obspy.read_inventory(p) for p in self.paths]
            )

        return self._inventory

    def get_inventory(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
    ) -> obspy.Inventory:
        """
        Fetch station response inventory from a local StationXML file.

        Parameters
        ----------
        network:
            FDSN network code.
        station:
            FDSN station code.
        location:
            FDSN location code.
        channels:
            FDSN channel codes or pattern.
        starttime:
            Optional start time used to constrain metadata selection.
        endtime:
            Optional end time used to constrain metadata selection.

        Returns
        -------
        selected:
            Inventory matching the requested selection.

        """

        key = (network, station, location, channels)
        if self.cache and key in self._inventory_cache:
            return self._inventory_cache[key]

        inventory = self._load()

        inventory = inventory.select(
            network=network,
            station=station,
            location=location,
            channel=channels,
        )

        if self.cache:
            self._inventory_cache[key] = inventory

        return inventory

    def clear_cache(self) -> None:
        self._inventory_cache.clear()
        self._inventory = None


@dataclass(slots=True)
class FDSNResponseClient:
    base_url: str
    timeout: int = 60
    cache: bool = True
    _client: FDSNClient = field(init=False)
    _inventory_cache: dict[tuple, obspy.Inventory] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self._client = FDSNClient(self.base_url, timeout=self.timeout)

    def get_inventory(
        self,
        network: str,
        station: str,
        location: str,
        channels: str,
    ) -> obspy.Inventory:
        """
        Fetch station response inventory from a remote FDSN station service.

        Parameters
        ----------
        network:
            FDSN network code.
        station:
            FDSN station code.
        location:
            FDSN location code.
        channels:
            FDSN channel codes or pattern.
        starttime:
            Optional start time used to constrain metadata selection.
        endtime:
            Optional end time used to constrain metadata selection.

        Returns
        -------
        selected:
            Inventory matching the requested selection.

        """

        key = (network, station, location, channels)
        if self.cache and key in self._inventory_cache:
            return self._inventory_cache[key]

        inventory = self._client.get_stations(
            network=network,
            station=station,
            location=location,
            channel=channels,
            level="response",
        )

        if self.cache:
            self._inventory_cache[key] = inventory

        return inventory

    def clear_cache(self) -> None:
        self._inventory_cache.clear()


def _merge_inventories(inventories: Iterable[obspy.Inventory]) -> obspy.Inventory:
    """
    Merge multiple ObsPy Inventory objects.

    Networks and stations are merged by code. Channels are merged by
    (location_code, channel_code, start_date, end_date) so that distinct
    epochs are preserved.

    Parameters
    ----------
    inventories
        Iterable of Inventory objects to merge.

    Returns
    -------
    Inventory
        Merged inventory containing all unique networks, stations, and
        channel epochs.

    """

    merged_networks = {}

    for inventory in inventories:
        for network in inventory.networks:
            if network.code not in merged_networks:
                merged_networks[network.code] = network.copy()
                continue

            target_network = merged_networks[network.code]

            existing_stations = {
                station.code: station for station in target_network.stations
            }

            for station in network.stations:
                if station.code not in existing_stations:
                    target_network.stations.append(station.copy())
                    continue

                target_station = existing_stations[station.code]

                existing_channels = {
                    (
                        ch.location_code,
                        ch.code,
                        ch.start_date,
                        ch.end_date,
                    ): ch
                    for ch in target_station.channels
                }

                for channel in station.channels:
                    key = (
                        channel.location_code,
                        channel.code,
                        channel.start_date,
                        channel.end_date,
                    )

                    if key not in existing_channels:
                        target_station.channels.append(channel.copy())

    return obspy.Inventory(
        networks=list(merged_networks.values()),
        source=inventory.source,
    )


def make_response_client(config: Mapping[str, Any]) -> ResponseClient:
    """
    Factory function for creating a ResponseClient from a config file.

    Parameters
    ----------
    config:
        The config specifying the response data access client.

    Returns
    -------
    client:
        A local, FDSN, or SeisMon response client.

    """

    match mode := config["client"]:
        case "stationxml":
            return StationXMLResponseClient(**config["stationxml"])
        case "fdsn":
            return FDSNResponseClient(**config["fdsn"])
        case _:
            raise ValueError(f"Unknown response.client={mode!r}")
