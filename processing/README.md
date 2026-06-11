# Processing Notebooks

Notebooks for **setting up, launching and monitoring** Tsunami-HySEA simulations: load balancing, single and nested-grid runs, and real-time job monitoring.

> ⚠️ **Note:** unlike the [preprocessing](../preprocessing/) notebooks, the notebooks in this folder generally need to run **on the compute machine itself** — the Jupyter kernel must live on the host with the GPU(s) and the Tsunami-HySEA installation, since the launch commands (`mpirun`, `TsunamiHySEA`) are executed locally by the kernel.

## Available Notebooks

| Notebook | Description | Requirements |
|----------|-------------|--------------|
| [JN_Launch_Computation.ipynb](JN_Launch_Computation.ipynb) | Interactive launcher for Tsunami-HySEA: browse to the simulation folder, select/inspect/edit the parfile, plot the domain and all nesting levels, run GPU load balancing, launch the run with `mpirun` and monitor the log in real time with a progress bar and a stop button. Includes a startup environment check (✓/✗) for every external dependency. | Kernel on the GPU machine, with Tsunami-HySEA binaries, MPI and CUDA. Paths configured in the first code cell. |

See the [Python and library requirements](../README.md#-python-and-library-requirements) section of the main README for supported Python versions and the per-notebook library matrix.

## Planned Notebooks

- Batch / ensemble execution of multiple scenarios
- SLURM job submission and monitoring

*This list grows progressively — check back for updates.*
