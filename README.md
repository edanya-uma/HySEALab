# HySEALab

**A collection of Jupyter Notebooks for preprocessing, processing and post-processing activities for the HySEA family of codes.**

Developed by the [EDANYA Research Group](https://www.uma.es/edanya) — Universidad de Málaga.

HySEALab provides a set of **self-contained, fully documented Jupyter Notebooks** covering the complete workflow of a [Tsunami-HySEA](https://edanya.uma.es/hysea/) simulation study:

- **Preprocessing** — preparation of input data: bathymetric/topographic grids, nested meshes, buoy and POI (Points Of Interest) coordinates, friction maps, parameter files…
- **Processing** — simulation setup, launching and monitoring of Tsunami-HySEA runs.
- **Postprocessing** — analysis and visualization of simulation outputs: propagation maps, time series at POIs, inundation maps, animations…

## 📂 Repository Structure

```
HySEALab/
├── preprocessing/        Notebooks for input data preparation
│   ├── JN04_Grid_from_GEBCO.ipynb
│   ├── JN10_Nested_Grids_nest_down.ipynb
│   ├── JN12_Format_Conversion.ipynb
│   └── JN13_Parameter_File_Builder_and_Validator.ipynb
├── processing/           Notebooks for simulation setup and execution
│   └── JN_Launch_Computation.ipynb
├── postprocessing/       Notebooks for analysis and visualization of results
│   ├── JN08_Inundation_Maps.ipynb
│   └── 01_map_viewer_standalone.ipynb   (beta)
├── datasets/             Bundled datasets for the hands-on notebooks (zip)
│   └── topobathy_JN10.zip
├── deprecated/           ⚠️ Legacy Epsilon library (no longer maintained)
├── CITATION.cff          Citation metadata
├── LICENSE               GPL-3.0 license
└── README.md             This file
```

Each folder contains its own `README.md` with the list of available notebooks and their purpose. New notebooks are added progressively to each category.

## 🚀 Getting Started

The notebooks are **self-contained**: each one declares its own requirements (Python packages and input data) in its header cell, and only needs to be executed on a computer with access to the relevant Tsunami-HySEA files:

- **Input files**: topobathymetric grids (e.g. GEBCO), buoy/POI coordinates, friction maps, parameter files…
- **Output files**: NetCDF results produced by Tsunami-HySEA simulations.

No additional library or package from this repository is required — just open a notebook in JupyterLab and follow it cell by cell.

> ⚠️ **Exception:** the notebooks in [processing/](processing/) launch Tsunami-HySEA directly, so their kernel must run **on the compute machine** that hosts the GPU(s) and the Tsunami-HySEA installation (see [processing/README.md](processing/README.md)).

## 🐍 Python and Library Requirements

### Python version

- **Recommended: Python ≥ 3.10** (tested with 3.11).
- The notebooks themselves use no syntax newer than f-strings (Python 3.6), so the
  effective minimum is set by the libraries: recent releases of `xarray` and
  `cartopy` require **Python ≥ 3.10**. Python 3.9 still works for the notebooks
  that do not use them (see the matrix below), but is not recommended for new
  environments.

### Full environment (covers every notebook)

```bash
conda create -n hysealab python=3.11
conda activate hysealab
conda install -c conda-forge jupyterlab numpy scipy matplotlib pillow netcdf4 xarray cartopy ipywidgets psutil
pip install hdf5plugin ipyfilechooser        # optional extras
```

### Libraries used by each notebook

● = required ○ = optional (the notebook degrades gracefully without it)

| Library | JN04 | JN10 | JN12 | JN13 | JN_Launch | JN08 | map_viewer |
|---------|:----:|:----:|:----:|:----:|:---------:|:----:|:----------:|
| `numpy` | ● | ● | ● | | ● | ● | ● |
| `scipy` | ● | ● | | | | | |
| `matplotlib` | ● | ● | ● | ● | ● | ● | ● |
| `netCDF4` | ● | ● | ● | ○ | ● | ● | ● |
| `pillow` (PIL) | ● | | ● | | | ● | ● |
| `ipywidgets` | | | | ○ | ● | ● | ● |
| `xarray` | | | | | | | ● |
| `cartopy` | | | | | | ● | |
| `psutil` | | | | | ○ | | |
| `hdf5plugin` | | | | | | ○ | ○ |
| `h5netcdf` | | | | | | | ○ |
| `ipyfilechooser` | | | | | ○ | | |

Notebooks: JN04, JN10, JN12, JN13 in [preprocessing/](preprocessing/); JN_Launch_Computation in [processing/](processing/); JN08 and 01_map_viewer_standalone in [postprocessing/](postprocessing/).

**Non-Python requirements:**

- **JN12** (Sections F–G only): GMT 6 and GDAL command-line tools (optional alternatives).
- **JN_Launch_Computation**: Tsunami-HySEA binaries, an MPI installation, CUDA-capable GPU(s) and the HDF5/NetCDF runtime libraries on the compute machine.
- **JN04**: a GEBCO GeoTIFF tile downloaded from [download.gebco.net](https://download.gebco.net).
- **JN08** (Step 4 only): internet access for satellite base tiles.

The **Requirements** section at the top of each notebook is the authoritative list for that notebook, including install one-liners.

### Running a notebook

```bash
git clone https://github.com/edanya-uma/HySEALab.git
cd HySEALab/preprocessing        # or processing/ | postprocessing/
jupyter lab JN04_Grid_from_GEBCO.ipynb
```

## 📓 Available Notebooks

### Preprocessing

| Notebook | Description |
|----------|-------------|
| [JN04_Grid_from_GEBCO.ipynb](preprocessing/JN04_Grid_from_GEBCO.ipynb) | Build a single-level bathymetric grid (`.grd`) for Tsunami-HySEA from the freely available GEBCO global dataset — no GMT required. |
| [JN12_Format_Conversion.ipynb](preprocessing/JN12_Format_Conversion.ipynb) | Convert DTM files (GeoTIFF, Surfer Binary v6/v7) to the HySEA NetCDF `.grd` format, with auto-detection, batch mode and GMT/GDAL alternatives. |
| [JN13_Parameter_File_Builder_and_Validator.ipynb](preprocessing/JN13_Parameter_File_Builder_and_Validator.ipynb) | The Tsunami-HySEA parameter file explained line by line, plus tools to build new files and validate existing ones (interactive picker and nested-mesh hierarchy viewer included). |
| [JN10_Nested_Grids_nest_down.ipynb](preprocessing/JN10_Nested_Grids_nest_down.ipynb) | Build nested grid hierarchies with `nest_down`, with a hands-on branching 4-level case (Cádiz & Huelva). The grid dataset is bundled in [datasets/](datasets/) and extracted automatically. |

### Processing

| Notebook | Description |
|----------|-------------|
| [JN_Launch_Computation.ipynb](processing/JN_Launch_Computation.ipynb) | Interactive launcher for Tsunami-HySEA: inspect the parfile and domain, run GPU load balancing, launch with `mpirun` and monitor progress in real time. ⚠️ Must run on the machine hosting the GPU(s) and the Tsunami-HySEA installation. |

### Postprocessing

| Notebook | Description |
|----------|-------------|
| [JN08_Inundation_Maps.ipynb](postprocessing/JN08_Inundation_Maps.ipynb) | Compute and map the on-land inundation depth of any scenario: offline and satellite-tile maps, flooded-area statistics, run-up diagram. Works with any grid resolution. |
| [01_map_viewer_standalone.ipynb](postprocessing/01_map_viewer_standalone.ipynb) 🧪 | **(beta)** Interactive viewer for all output variables: 2D maps with configurable colour scales, isochrone mode for arrival times, PNG export and GIF animations. |

## ⚠️ Deprecation Notice — Epsilon Library

Earlier releases of this repository were built around the **Epsilon** Python library (`epsilon.py`) for visualizing Tsunami-HySEA results. **Epsilon is now deprecated and no longer maintained.** Its functionality is being progressively replaced by the self-contained notebooks in this collection.

The legacy files (library, manual and setup scripts) are kept in the [deprecated/](deprecated/) folder for reference only — see [deprecated/README.md](deprecated/README.md).

## 📖 Citing HySEALab

If you use HySEALab, please cite it using the metadata in [CITATION.cff](CITATION.cff) (GitHub shows a *"Cite this repository"* button on the sidebar).

## 💶 Funding

This work was funded by **EPOS ERIC** through the **EPOS TCS Tsunami Multi-Year Collaboration Agreement (MYCA) 2024–2028** (UMA internal ref. OTRI 8.06.UE/54.9074 – EPOS TCS Tsunami).

## 🤝 Contributing

If you find errors or have suggestions, please open an issue on GitHub.

## 📧 Contact

EDANYA Research Group — Universidad de Málaga · t_hysea@uma.es

## 📄 License

This project is licensed under the [GNU GPL-3.0](LICENSE) license.
