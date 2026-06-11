# Postprocessing Notebooks

Notebooks for **analyzing and visualizing** the output of Tsunami-HySEA simulations: maximum wave height and propagation maps, time series at buoys/POIs, inundation maps, comparisons between simulations and animations.

All notebooks are **self-contained**: requirements (Python packages and input data) are listed in the header cell of each notebook. They only need to be executed on a computer with access to the NetCDF output files produced by Tsunami-HySEA.

## Available Notebooks

| Notebook | Description | Input | Output |
|----------|-------------|-------|--------|
| [JN08_Inundation_Maps.ipynb](JN08_Inundation_Maps.ipynb) | Compute and map the on-land inundation depth of any Tsunami-HySEA scenario: graphical file selector, sign-convention guide, quick offline map, satellite-tile map (Esri World Imagery), and statistics (flooded area by depth class, run-up diagram, depth histogram). Works with any grid resolution. | Tsunami-HySEA NetCDF output with `max_height` + `original_bathy` | Inundation maps (PNG) + statistics figures |
| [01_map_viewer_standalone.ipynb](01_map_viewer_standalone.ipynb) 🧪 **beta** | Self-contained viewer for all the variables of a Tsunami-HySEA output: graphical file selector, interactive 2D map viewer (colour scales, downsampling, isochrone mode for `arrival_times`), PNG export and GIF animation over a time range. *Beta version under active development — will be updated shortly.* | Any Tsunami-HySEA NetCDF output | Maps (PNG) + animations (GIF) |

See the [Python and library requirements](../README.md#-python-and-library-requirements) section of the main README for supported Python versions and the per-notebook library matrix.

## Planned Notebooks

- Updated (stable) version of the map viewer
- Propagation / maximum wave height maps
- Time-series viewer at buoys and POIs
- Simulation comparison tools

*This list grows progressively — check back for updates.*
