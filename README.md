Multi-Parameter Volcano Monitoring Toolkit
==========================================
A lightweight toolkit for computing and visualising a suite of time-series products derived from common volcano-monitoring data streams.

The package is organised around two primary modules:

- ``mpvmtk.compute``: computation of time-series products
- ``mpvmtk.visualise``: generation of graphical products

Shared utilities for input/output, configuration handling, and archive access provide a consistent interface for diverse sensor types.

The toolkit is designed to be modular and extensible, with future support planned for SSAM, magnetic field products, environmental sensors, power-system data, and soil-probe measurements.

Installation
------------
Clone the repository:

```console
git clone https://github.com/hemmelig/mpvm-tk
cd mpvm-tk
```

We recommend using ``uv``, a fast Python package and project manager, to set up an isolated virtual environment:

```console
uv venv --python=3.12
source .venv/bin/activate
uv pip install .
```

Package Overview
----------------
MPVM provides a unified command-line interface via ``mpvm`` with two subcommand groups:

1. Compute utilities (``mpvm compute``)
Computation of monitoring-oriented time-series products.

Current functionality includes:
- Real-time Seismic Amplitude Measurements

Planned extensions include:
- SSAM
- Magnetic field data products
- Environmental sensor time-series
- Power-system monitoring data
- Soil-probe signals and derivatives

Example usage:

```console
mpvm compute rsam --config params_rsam.toml
```

1. Visualisation utilities (``mpvm visualise``)
Generation of publication-ready or operational figures.

Current functionality includes:
- Seismic helicorders (drum plots)
- Real-time Seismic Amplitude Measurement visualisation

Each visual product is driven entirely by a user TOML configuration, including:
- Archive location and path formats
- Site metadata (network, station, channels, location)
- Plot layout and stylesheet
- Filter settings
- Output product paths

Roadmap
-------
Planned additions to ``mpvmtk.compute`` and ``mpvmtk.visualise`` include:
- RSAM / SSAM archives and daily summaries
- Spectrogram and PSD products
- Real-time magnetic field visualisation
- Environmental and meteorological dashboards
- Telemetry/power-system status monitoring
- Soil probe time-series diagnostics
- Automatic daily product generation pipelines

Contact
-------
Any comments/questions can be directed to:
* **Conor Bacon** - conor.bacon [ at ] norsar.no

License
-------
This package is written and maintained by Conor A. Bacon. It is distributed under the GPLv3 License. Please see the LICENSE file for a complete description of the rights and freedoms that this provides the user.
