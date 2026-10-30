# SDL — publishing HySEA simulations to the CINECA Simulation Data Lake

Tools to publish Tsunami-HySEA (and other HySEA codes) simulation experiments to the
**CINECA Simulation Data Lake** ([SDL@CINECA](https://sdl.hpc.cineca.it), developed within the
Geo-INQUIRE project), and to download published data back for post-processing.

All notebooks are thin interactive front-ends (ipywidgets) on top of one library,
[`sdl_lib.py`](sdl_lib.py), which talks to the SDL REST API. The same library drives a headless
command-line publisher, [`sdl_publish_manifest.py`](sdl_publish_manifest.py), for batch use.
On the HySEALab platform these tools are available from the **Simulation Data Lake (SDL)
Management** menu.

## How a HySEA study maps onto the SDL data model

The user keeps each experiment in a folder with three fixed sub-folders. The tools find every
file from this layout and derive the technical metadata automatically.

```
my_experiment/
├── parfiles/   *.txt     one Tsunami-HySEA parameter file per simulation run
├── bathy/      *.grd/.nc topo-bathymetry shared by all runs
└── sim/                  outputs; each file starts with the NetCDF prefix of its parameter file
```

| Project content | SDL entity |
|---|---|
| The folder | one **Experiment**, with a **Version** (default `1.0.0`) |
| `bathy/` grids | one common input dataset of the version (`scenario/event_data`), uploaded once; its bounding box gives the spatial coverage |
| each `parfiles/*.txt` | one **Simulation Run**, with the parameter file as its input |
| `sim/<prefix>*` | the outputs of the run whose parameter file declares that NetCDF prefix |
| bathymetry plots and an HTML README | data products, generated automatically |

For reproducibility, every published experiment contains the parameter files, the
topo-bathymetry and the results. The SDL assigns DataCite DOIs to published experiments and to
each of their versions: request one with `experiment.requestDOI: true`, then publish and manage
the DOI from the SDL web portal.

**Parameter files:** the first non-comment line must be the unique simulation name, with no
inline comment and different from the NetCDF output prefix; the prefix must have no path. Do not
put other `.txt` files (e.g. gauge lists) in `parfiles/`: each one becomes a simulation run.

## Tools

| Notebook | What it does |
|---|---|
| [`sdl_publishing_guide_EN.ipynb`](sdl_publishing_guide_EN.ipynb) | Step-by-step guide, with an optional check of the project folder |
| [`code_registry_manager_EN.ipynb`](code_registry_manager_EN.ipynb) | View/add/edit the simulation codes in [`sdl_codes.yml`](sdl_codes.yml) (keywords, theme) |
| [`catalogue_manager_EN.ipynb`](catalogue_manager_EN.ipynb) | Search or create persons, organizations and projects in the SDL catalogue |
| [`sdl_generate_publish_EN.ipynb`](sdl_generate_publish_EN.ipynb) | Form → generates the manifest → publishes a new experiment |
| [`sdl_append_simulations_EN.ipynb`](sdl_append_simulations_EN.ipynb) | Adds new simulation runs to an existing experiment version, reusing its common input |
| [`sdl_publish_manifest_EN.ipynb`](sdl_publish_manifest_EN.ipynb) | Publishes an existing manifest, with per-file and global progress bars |
| [`sdl_browse_fetch_EN.ipynb`](sdl_browse_fetch_EN.ipynb) | Lists experiments and downloads their files for post-processing |

## Headless publishing with a YAML manifest

A manifest (`sdl_manifest.yml`) holds only the human metadata: title, description, authors,
organizations, projects, code and version, licence, visibility and theme. Everything technical
is derived from the folder. See [`sdl_manifest.example.yml`](sdl_manifest.example.yml).

```bash
# 1) generate an annotated skeleton from a project folder
python sdl_publish_manifest.py generate my_experiment/

# 2) fill in the TODO fields, then publish
SDL_USERNAME=you@example.org SDL_PASSWORD=... \
    python sdl_publish_manifest.py publish my_experiment/sdl_manifest.yml
```

To **add runs** to an experiment that is already published, use `experiment.mode: existing`
with its `id` and `project.reuse_scenario: true`. The common input is linked, not uploaded
again. This only works for an existing version; a new version needs its `bathy/` folder.

**Theme:** the theme decides the EPOS Platform catalogue in which the experiment appears. The
SDL accepts `geohazards`, `wavefms`, `seismicdata` and `volcanoobservatis`. HySEA codes default
to `geohazards`; set `experiment.theme` in the manifest to change it.

## Requirements

- Python ≥ 3.10 (tested in the HySEALab environment) and the packages `requests`, `requests_toolbelt`, `pyyaml`, `jsonschema`, `tqdm`;
  `rasterio`, `numpy`, `matplotlib` and `cmocean` for the spatial coverage and the bathymetry
  plots; `ipywidgets` for the notebooks.
- `sdl_lib.py` and `sdl_codes.yml` in the same folder as the notebooks.
- An SDL account (request it from sdl@cineca.it). The tools work with the production server
  (`sdl.hpc.cineca.it`) and the development server (`sdl-dev.hpc.cineca.it`); catalogue ids
  (persons, organizations, projects) differ between them.

**Credentials are never stored.** The notebooks ask for the password in a widget and keep it in
memory only; the command-line publisher reads `SDL_USERNAME` / `SDL_PASSWORD` or prompts for
them.
