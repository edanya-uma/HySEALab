# Preprocessing Notebooks

Notebooks for preparing the **input data** of a Tsunami-HySEA simulation: topobathymetric grids, nested meshes, buoy and POI (Points Of Interest) coordinates, friction maps and parameter files.

All notebooks are **self-contained**: requirements (Python packages and input data) are listed in the header cell of each notebook. By convention, each notebook reads its input from and writes its output to a `data/` subfolder placed next to it (created automatically on first run).

## Available Notebooks

| Notebook | Description | Input | Output |
|----------|-------------|-------|--------|
| [JN04_Grid_from_GEBCO.ipynb](JN04_Grid_from_GEBCO.ipynb) | Build a single-level bathymetric grid for Tsunami-HySEA from the GEBCO global dataset. Covers clipping, resampling, writing the NetCDF `.grd` file, verification and a template parameter file. No GMT required. | GEBCO GeoTIFF tile ([download.gebco.net](https://download.gebco.net)) | HySEA `.grd` grid + template parameter file |
| [JN12_Format_Conversion.ipynb](JN12_Format_Conversion.ipynb) | Convert DTM files in other formats (GeoTIFF, Surfer Binary v6/v7) to the HySEA NetCDF `.grd` format. Includes format auto-detection, batch conversion, and GMT/GDAL command-line alternatives. Runs out of the box — generates synthetic Surfer test files. | DTM files in GeoTIFF or Surfer format (optional) | HySEA `.grd` grids |
| [JN13_Parameter_File_Builder_and_Validator.ipynb](JN13_Parameter_File_Builder_and_Validator.ipynb) | The reference for the Tsunami-HySEA parameter file: line-by-line explanation of the format (including nested multi-grid layouts), a `build_parfile()` generator, a `validate_parfile()` diagnostic tool with an interactive file picker, and a nested-mesh hierarchy viewer. Runs out of the box — generates its own examples. | Tsunami-HySEA parameter files (optional) | Validated/generated parameter files |
| [JN10_Nested_Grids_nest_down.ipynb](JN10_Nested_Grids_nest_down.ipynb) | Build nested grid hierarchies with `nest_down`: alignment rules, microscopic cell-alignment visualisation, and a hands-on branching 4-level case (Cádiz & Huelva) where two L2 grids share the same L1 parent. | Cádiz/Huelva grid dataset (bundled — see **Data** below) | Aligned nested `.grd` grids |

See the [Python and library requirements](../README.md#-python-and-library-requirements) section of the main README for supported Python versions and the per-notebook library matrix.

## Data

Real bathymetric datasets used by the hands-on notebooks are stored in the [`datasets/`](../datasets/) folder of the repository as compressed archives:

| Dataset | Used by | Location |
|---------|---------|----------|
| Cádiz / Huelva 4-level grid hierarchy (6 `.grd` grids, ~19 MB zip) | JN10 | [`datasets/topobathy_JN10.zip`](../datasets/topobathy_JN10.zip) — **extracted automatically** by the notebook on first run |

Notebooks extract their dataset into a `data/` subfolder next to them on first run. The `data/` folder is git-ignored, so extracted files never end up in the repository.

## Planned Notebooks

- Friction (Manning) map generation
- Buoy / POI coordinate file preparation

*This list grows progressively — check back for updates.*
