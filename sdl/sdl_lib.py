"""sdl_lib.py — helper library for the SDL (CINECA Simulation Data Lake) publishing notebooks.

Consolidates the *non-interactive* logic used to publish a Tsunami-HySEA simulation
project (parfiles / bathy / sim) to the CINECA Simulation Data Lake (https://sdl.hpc.cineca.it),
cleaned from the original ``scripts_SDL`` modules:

* **No hardcoded credentials** — the notebook logs in with a password widget.
* **No ``input()`` prompts** — the interactive flow lives in the notebook.
* **No venv bootstrapping and no delete utilities** — out of scope / unsafe for a shared tool.

The companion notebook (``01_sdl_publish_EN.ipynb``) drives these functions with ipywidgets,
reproducing the 8 phases of the original ``main.py`` pipeline:

    login -> select & validate project -> metadata -> experiment/version
          -> bathymetry plots -> upload (scenario, parfiles, sim) -> README -> visibility/license

Only ``requests`` is required for the upload/API part; the plotting helpers additionally need
``rasterio``, ``numpy``, ``matplotlib`` and ``cmocean``.
"""
from __future__ import annotations

import os
import time
import uuid
from urllib.parse import quote

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

# A chunk size of 50 MiB matches the server's multipart upload expectations.
CHUNK_SIZE = 50 * 1024 * 1024
MAX_UPLOAD_RETRIES = 4   # retries on transient network errors


# Themes accepted by the SDL experiment schema (EPOS TCS domains). The theme decides in
# which EPOS Platform catalogue an experiment appears. "geohazards" is used by default
# for HySEA codes; override it per experiment with `experiment.theme` in the manifest.
SDL_THEMES = ["geohazards", "wavefms", "seismicdata", "volcanoobservatis"]
DEFAULT_THEME = ["geohazards"]


# =============================================================================
# Scientific code registry (keywords / theme used when creating an experiment)
# =============================================================================
CODE_METADATA_REGISTRY = {
    "tsunami_hysea": {
        "display_name": "Tsunami-HySEA",
        "keywords": ["tsunami", "hysea", "shallow-water", "geophysics", "cuda"],
        "description_prefix": (
            "Numerical simulation of tsunami propagation and inundation generated "
            "using the Tsunami-HySEA model."
        ),
        "default_theme": ["geohazards"],
    },
    "landslide_hysea": {
        "display_name": "Landslide-HySEA",
        "keywords": ["tsunami", "landslide", "hysea", "shallow-water", "geophysics", "cuda"],
        "description_prefix": (
            "Numerical simulation of landslide-generated tsunamis (coupled fluid/granular "
            "Savage-Hutter shallow flow) using the Landslide-HySEA model."
        ),
        "default_theme": ["geohazards"],
    },
    "multilayer_hysea": {
        "display_name": "Multilayer-HySEA",
        "keywords": ["tsunami", "hysea", "multilayer", "dispersive", "non-hydrostatic",
                     "shallow-water", "geophysics", "cuda"],
        "description_prefix": (
            "Numerical simulation of tsunami propagation with the dispersive / "
            "non-hydrostatic Multilayer-HySEA model."
        ),
        "default_theme": ["geohazards"],
    },
}


def _load_external_codes():
    """Merge an *editable* YAML code registry over the built-in defaults, if present.

    Lets users add/edit codes without touching this file. Search order:
    ``$SDL_CODES_FILE`` → ``sdl_codes.yml`` next to this module → ``./sdl_codes.yml``.
    Each top-level key is a code id mapping to ``display_name`` / ``keywords`` /
    ``description_prefix`` / ``default_theme``. Failures are ignored (built-ins remain).
    """
    candidates = [os.environ.get("SDL_CODES_FILE"),
                  os.path.join(os.path.dirname(os.path.abspath(__file__)), "sdl_codes.yml"),
                  os.path.join(os.getcwd(), "sdl_codes.yml")]
    for path in candidates:
        if not path or not os.path.exists(path):
            continue
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict):
                        CODE_METADATA_REGISTRY[str(k).lower().strip()] = v
                return path
        except Exception:
            pass
    return None


# Codes loaded from an external file override / extend the built-ins above.
CODE_REGISTRY_FILE = _load_external_codes()


def get_metadata_for_code(code_key):
    """Return the metadata dict for a registered code key (case-insensitive), or {}."""
    return CODE_METADATA_REGISTRY.get(code_key.lower().strip(), {})


def resolve_theme(exp):
    """SDL theme list for a new experiment: ``experiment.theme`` in the manifest, else the
    code's ``default_theme``, else ``DEFAULT_THEME``. Unknown values raise ``ValueError``."""
    code = (exp.get("code") or {}).get("name")
    theme = (exp.get("theme")
             or (get_metadata_for_code(code).get("default_theme") if code else None)
             or DEFAULT_THEME)
    bad = [t for t in theme if t not in SDL_THEMES]
    if bad:
        raise ValueError(f"Unknown SDL theme(s) {bad}; allowed: {SDL_THEMES}")
    return list(theme)


# =============================================================================
# Authentication
# =============================================================================
def get_auth_token(base_url, username, password, timeout=30):
    """Log in against the SDL and return the JWT access token (a raw string).

    Raises ``requests.HTTPError`` on a non-200 response so the caller can show the reason.
    The endpoint may return either the token as a bare JSON string or as
    ``{"access_token": "..."}`` — both are handled.
    """
    res = requests.post(
        f"{base_url}/auth/login",
        json={"username": username, "password": password},
        timeout=timeout,
    )
    res.raise_for_status()
    data = res.json()
    return data if isinstance(data, str) else data.get("access_token")


def auth_headers(token):
    """Build the standard JSON + Bearer headers used by every /api call."""
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# =============================================================================
# Tsunami-HySEA parameter-file scanner (heuristic, stateless)
# =============================================================================
def scan_hysea_parfile(file_path, verbose=False):
    """Pure heuristic token scanner for Tsunami_HySEA parameter files.

    Returns a dict with the simulation name (``id_nombre``), the input grids
    (``id_bathymetry_file`` / ``id_batimetry_file_N``) and the output NetCDF prefixes
    (``id_NetCDF_prefix_N``). Completely stateless: no line pointers, no versions.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    data = {}
    if not lines:
        return data

    # Rule 1: the first clean line is the primary simulation identifier.
    sim_name = lines[0].strip().strip("'").strip('"')
    data["id_nombre"] = sim_name

    bathy_count = 0
    prefix_count = 0
    for line in lines:
        for token in line.split():
            tok = token.strip().strip("'").strip('"')
            if not tok:
                continue
            # Rule 2: input grid files end with .grd / .nc
            if tok.lower().endswith((".grd", ".nc")):
                filename = os.path.basename(tok)
                if bathy_count == 0:
                    data["id_bathymetry_file"] = filename
                data[f"id_batimetry_file_{bathy_count}"] = filename
                bathy_count += 1
            # Rule 3: output prefixes are plain strings (>2 chars, not numeric, no dot/slash)
            elif len(tok) > 2 and not tok.replace(".", "", 1).isdigit():
                if "." not in tok and "/" not in tok and "\\" not in tok and tok != sim_name:
                    data[f"id_NetCDF_prefix_{prefix_count}"] = tok
                    prefix_count += 1

    if verbose:
        print(f"[HYSEA SCANNER] {os.path.basename(file_path)}: "
              f"name='{sim_name}', grids={bathy_count}, prefixes={prefix_count}")
    return data


class TsunamiHySeaParser:
    """Thin stateless wrapper around :func:`scan_hysea_parfile`."""

    def __init__(self, file_path, version=None, verbose=False):
        self.file_path = file_path
        self.verbose = verbose
        self.data = {}

    def parse(self):
        self.data = scan_hysea_parfile(self.file_path, self.verbose)
        return self.data

    def get_simulation_identifiers(self):
        prefixes = [v for k, v in self.data.items() if k.startswith("id_NetCDF_prefix")]
        return {"simulation_name": self.data.get("id_nombre"), "output_prefixes": prefixes}


# =============================================================================
# Payload sanitiser (mirrors the constraints of the Cineca API)
# =============================================================================
def clean_for_post(obj, endpoint):
    """Strip / fix fields so an object fetched from the API is accepted back on POST/PATCH."""
    if not isinstance(obj, dict):
        return obj

    clean_obj = {k: v for k, v in obj.items() if k not in ("id",)}

    for field in ("ror", "leiCode", "url", "logoUrl", "website", "identifier"):
        if field in clean_obj:
            val = clean_obj[field]
            if val is None or (isinstance(val, str) and not val.strip()):
                del clean_obj[field]

    if endpoint == "organizations":
        clean_obj["isFunding"] = clean_obj.get("isFunding", False)
        clean_obj["isCreator"] = clean_obj.get("isCreator", False)
        if clean_obj.get("telephone") is None:
            clean_obj["telephone"] = []
        if clean_obj.get("emails") is None:
            clean_obj["emails"] = []
        if not clean_obj.get("leiCode"):
            clean_obj["leiCode"] = "00000000000000000000"

    if endpoint == "projects":
        clean_obj["isFunding"] = clean_obj.get("isFunding", False)
        clean_obj.pop("funderIdentifierType", None)

    return clean_obj


# =============================================================================
# Spatial coverage (largest bathymetry grid -> WGS84 bounding polygon)
# =============================================================================
def get_largest_spatial_coverage(bathy_dir):
    """Return a ``{"geometry": {"coordinates": [...]}}`` polygon for the widest grid.

    Reprojects to EPSG:4326 when needed. Returns ``None`` (and prints a warning) when the
    coordinates fall outside the valid geographic range (e.g. local/metric meshes).
    """
    import rasterio
    from rasterio.warp import transform_bounds

    largest_area = 0
    best_wgs_bounds = None
    if not os.path.exists(bathy_dir):
        return None

    for f in os.listdir(bathy_dir):
        if not f.endswith((".grd", ".nc")):
            continue
        try:
            with rasterio.open(os.path.join(bathy_dir, f)) as src:
                b = src.bounds
                area = abs((b.right - b.left) * (b.top - b.bottom))
                if area > largest_area:
                    largest_area = area
                    if src.crs and src.crs.to_string() != "EPSG:4326":
                        try:
                            best_wgs_bounds = transform_bounds(
                                src.crs, "EPSG:4326", b.left, b.bottom, b.right, b.top
                            )
                        except Exception:
                            best_wgs_bounds = (b.left, b.bottom, b.right, b.top)
                    else:
                        best_wgs_bounds = (b.left, b.bottom, b.right, b.top)
        except Exception:
            continue

    if not best_wgs_bounds:
        return None

    wl, wb, wr, wt = best_wgs_bounds
    if (-180.0 <= wl <= 180.0 and -180.0 <= wr <= 180.0
            and -90.0 <= wb <= 90.0 and -90.0 <= wt <= 90.0):
        return {
            "geometry": {
                "coordinates": [
                    [float(wl), float(wt)], [float(wl), float(wb)],
                    [float(wr), float(wb)], [float(wr), float(wt)],
                    [float(wl), float(wt)],
                ]
            }
        }
    print("[WARN] Mesh coordinates are out of geographic range "
          f"(L={wl}, R={wr}, B={wb}, T={wt}); omitting spatialCoverage.")
    return None


# =============================================================================
# Chunked upload + dataset / simulation registration
# =============================================================================
def _post_json_retry(url, headers, json_body, log=print, what="request"):
    """POST a small JSON body, retrying on transient network errors. Returns the Response."""
    for attempt in range(1, MAX_UPLOAD_RETRIES + 1):
        try:
            return requests.post(url, headers=headers, json=json_body, timeout=(30, 120))
        except requests.exceptions.RequestException as e:
            if attempt >= MAX_UPLOAD_RETRIES:
                raise
            log(f"  ⚠ {what}: {type(e).__name__}; retry {attempt}/{MAX_UPLOAD_RETRIES - 1} ...")
            time.sleep(min(2 ** attempt, 30))


def full_upload_flow(base_url, token, experiment_id, version_name, file_path,
                     remote_path, log=print, progress=True):
    """Upload one local file to ``remote_path`` using the init -> chunked upload -> complete flow.

    ``log`` is a callable used for human-readable messages (defaults to ``print``); when
    ``progress`` is true a tqdm bar is shown (``tqdm.auto`` -> notebook bar inside Jupyter).
    Returns ``True`` on success.
    """
    filesize = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    remote_path_url = quote(remote_path, safe="")
    hdr = auth_headers(token)

    init_url = (f"{base_url}/api/experiments/{experiment_id}/versions/{version_name}"
                f"/init-upload/{remote_path_url}")
    res_init = _post_json_retry(init_url, hdr, {"fileSize": filesize}, log=log,
                                what=f"init-upload {filename}")
    if res_init.status_code not in (200, 201):
        log(f"  ❌ init-upload failed for {filename}: {res_init.status_code} {res_init.text[:200]}")
        return False
    upload_id = res_init.json().get("uploadId")

    upload_url = f"{base_url}/api/experiments/{experiment_id}/versions/{version_name}/upload"
    total_chunks = (filesize + CHUNK_SIZE - 1) // CHUNK_SIZE
    parts_summary = []

    bar = None
    if progress:
        try:
            from tqdm.auto import tqdm
            bar = tqdm(total=filesize, unit="B", unit_scale=True, unit_divisor=1024,
                       desc=f"⬆ {filename[:22]}")
        except Exception:
            bar = None

    with open(file_path, "rb") as f:
        for chunk_idx in range(total_chunks):
            chunk_data = f.read(CHUNK_SIZE)
            chunk_start = bar.n if bar is not None else 0
            for attempt in range(1, MAX_UPLOAD_RETRIES + 1):
                if bar is not None:
                    bar.n = chunk_start
                    bar.refresh()
                last = [0]

                def _cb(monitor, _last=last, _bar=bar):
                    if _bar is not None:
                        _bar.update(monitor.bytes_read - _last[0])
                        _last[0] = monitor.bytes_read

                encoder = MultipartEncoder(fields={
                    "isChunked": "true",
                    "uploadId": str(upload_id),
                    "partNumber": str(chunk_idx + 1),
                    "key": remote_path,
                    "file": (filename, chunk_data, "application/octet-stream"),
                })
                monitor = MultipartEncoderMonitor(encoder, _cb)
                status, err = None, None
                try:
                    res_up = requests.post(
                        upload_url, data=monitor,
                        headers={"Authorization": f"Bearer {token}",
                                 "Content-Type": monitor.content_type},
                        timeout=(30, 600),
                    )
                    status = res_up.status_code
                except requests.exceptions.RequestException as e:
                    err = e
                if status in (200, 201, 204):
                    break
                why = f"HTTP {status}" if status is not None else type(err).__name__
                if attempt >= MAX_UPLOAD_RETRIES:
                    if bar is not None:
                        bar.close()
                    log(f"  ❌ chunk {chunk_idx + 1}/{total_chunks} failed for {filename} "
                        f"after {attempt} attempts ({why})")
                    return False
                log(f"  ⚠ chunk {chunk_idx + 1}/{total_chunks} for {filename}: {why}; "
                    f"retry {attempt}/{MAX_UPLOAD_RETRIES - 1} ...")
                time.sleep(min(2 ** attempt, 30))
            parts_summary.append({"partNumber": chunk_idx + 1})

    if bar is not None:
        bar.close()

    complete_url = (f"{base_url}/api/experiments/{experiment_id}/versions/{version_name}"
                    f"/complete-upload/{upload_id}/{remote_path_url}")
    res_complete = _post_json_retry(complete_url, hdr, {"parts": parts_summary}, log=log,
                                    what=f"complete-upload {filename}")
    ok = res_complete.status_code in (200, 201, 204)
    log(f"  {'✅' if ok else '❌'} {remote_path}")
    return ok


def create_scenario_dataset(base_url, headers, exp_id, version, spatial_coverage,
                            dataset_name="event_data"):
    """Register the 'loose' scenario dataset (holds the spatial bounds). Returns its path."""
    dataset_path = f"scenario/{dataset_name}"
    payload = {
        "description": "Main scenario dataset containing spatial boundaries.",
        "license": "cc-by-4.0",
        "name": dataset_name,
        "parameters": None,
        "path": dataset_path,
        "relatedPublications": [],
        "relationship": [],
        "shared": False,
        "simulationPaths": [],
        "spatialCoverage": spatial_coverage,
        "temporalCoverage": None,
        "type": "input_parameter",
    }
    url = f"{base_url}/api/experiments/{exp_id}/versions/{version}/datasets/loose"
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code in (200, 201, 409):
        return dataset_path
    print(f"[ERR] create_scenario_dataset: {res.status_code} {res.text[:200]}")
    return None


def create_simulation_flow(base_url, headers, exp_id, version, sim_name, description,
                           dataset_path):
    """Register a simulation container linked to the scenario dataset. Returns its folder path."""
    folder_path = f"simulation/{sim_name}/"
    payload = {
        "datasetPaths": [f"/{dataset_path}"] if dataset_path else [],
        "description": description,
        "facilities": [],
        "name": sim_name,
        "path": folder_path,
        "softwares": [],
        "workflow": None,
    }
    url = f"{base_url}/api/experiments/{exp_id}/versions/{version}/simulations"
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code in (200, 201, 409):
        return folder_path
    return None


# =============================================================================
# Experiment / version / catalog helpers (thin wrappers over the REST API)
# =============================================================================
def list_experiments(base_url, headers):
    res = requests.get(f"{base_url}/api/experiments", headers=headers)
    return res.json() if res.status_code == 200 else []


def list_versions(base_url, headers, exp_id):
    res = requests.get(f"{base_url}/api/experiments/{exp_id}/versions-list", headers=headers)
    return res.json() if res.status_code == 200 else []


def list_catalog(base_url, headers, endpoint):
    """GET a simple catalog endpoint (organizations / projects). Returns a list."""
    res = requests.get(f"{base_url}/api/{endpoint}", headers=headers)
    return res.json() if res.status_code == 200 else []


# =============================================================================
# Download (retrieve published files back, e.g. for postprocessing)
# =============================================================================
def list_files(base_url, headers, exp_id, version):
    """List the stored files of an experiment version.

    Returns a list of S3-style records ``{"Key": ..., "Size": ..., "LastModified": ...}``.
    """
    res = requests.get(
        f"{base_url}/api/experiments/{exp_id}/versions/{version}/files", headers=headers)
    return res.json() if res.status_code == 200 else []


def download_file(base_url, headers, exp_id, version, key, dest_path,
                  log=print, progress=True, chunk_size=1024 * 1024, timeout=600):
    """Download one stored file (by its ``Key``) to ``dest_path``, streaming.

    Uses ``GET /api/experiments/{id}/versions/{v}/file/stream?path=<key>``. Creates parent
    directories as needed. Returns the number of bytes written.
    """
    url = f"{base_url}/api/experiments/{exp_id}/versions/{version}/file/stream"
    res = requests.get(url, headers=headers, params={"path": key}, stream=True, timeout=timeout)
    res.raise_for_status()
    total = int(res.headers.get("content-length") or 0)
    parent = os.path.dirname(os.path.abspath(dest_path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    bar = None
    if progress:
        try:
            from tqdm.auto import tqdm
            bar = tqdm(total=total or None, unit="B", unit_scale=True, unit_divisor=1024,
                       desc="⬇ " + os.path.basename(key)[:22])
        except Exception:
            bar = None
    written = 0
    with open(dest_path, "wb") as f:
        for ch in res.iter_content(chunk_size):
            if ch:
                f.write(ch)
                written += len(ch)
                if bar is not None:
                    bar.update(len(ch))
    if bar is not None:
        bar.close()
    log(f"  ⬇ {key} -> {dest_path} ({written} bytes)")
    return written


def list_persons(base_url, headers, page_size=100, max_pages=100):
    """Page through /api/persons and return every author record."""
    out = []
    page = 1
    while page <= max_pages:
        res = requests.get(f"{base_url}/api/persons?page={page}&size={page_size}", headers=headers)
        if res.status_code != 200:
            break
        chunk = res.json()
        if not chunk:
            break
        out.extend(chunk)
        page += 1
    return out


def create_person(base_url, headers, given_name, family_name, email="", qualifications="Researcher"):
    """Create a new scientific author profile. Returns the server record (dict)."""
    payload = {
        "identifiers": [{"scheme": "uuid", "value": str(uuid.uuid4())}],
        "givenName": given_name, "familyName": family_name,
        "emails": [email] if email else [],
        "qualifications": qualifications or "Researcher",
        "phones": [], "address": "",
    }
    res = requests.post(f"{base_url}/api/persons", json=payload, headers=headers)
    if res.status_code in (200, 201):
        body = res.json()
        return body if isinstance(body, dict) else {"id": res.text.strip(), **payload}
    raise requests.HTTPError(f"create_person failed: {res.status_code} {res.text[:200]}")


def create_catalog_item(base_url, headers, endpoint, name):
    """Create an organization / project by its display name. Returns the cleaned object.

    Organizations need more than a bare ``legalName`` (the API answers HTTP 400),
    so we send the same defaults ``clean_for_post`` enforces for an org
    (``isFunding`` / ``isCreator`` / ``telephone`` / ``emails`` / ``leiCode``).
    """
    if endpoint == "organizations":
        # The create endpoint requires leiCode (a bare legalName -> HTTP 400) but
        # rejects isFunding/isCreator as unknown fields (those only apply when
        # re-posting an existing org inside an experiment payload).
        payload = {
            "legalName": name,
            "telephone": [],
            "emails": [],
            "leiCode": "00000000000000000000",   # 20-char placeholder LEI (required)
        }
    elif endpoint == "projects":
        payload = {"title": name}
    else:
        payload = {"name": name}
    res = requests.post(f"{base_url}/api/{endpoint}", json=payload, headers=headers)
    if res.status_code not in (200, 201):
        raise requests.HTTPError(
            f"create_catalog_item({endpoint}) failed: {res.status_code} {res.text[:300]}")
    try:
        body = res.json()
    except ValueError:
        key = "legalName" if endpoint == "organizations" else "title"
        return {"id": res.text.strip(), key: name}
    return clean_for_post(body, endpoint)


def create_experiment(base_url, headers, name, description, themes, authors, keywords,
                      organizations, projects, request_doi=True):
    """POST a new experiment. Returns the new experiment id (or raises with the server error)."""
    payload = {
        "name": name, "description": description, "theme": themes, "requestDOI": request_doi,
        "authors": authors, "keywords": keywords,
        "organizations": organizations, "projects": projects,
    }
    res = requests.post(f"{base_url}/api/experiments", json=payload, headers=headers)
    if res.status_code in (200, 201):
        body = res.json()
        return body.get("id") if isinstance(body, dict) else body
    raise requests.HTTPError(f"create_experiment failed: {res.status_code} {res.text}")


def create_version(base_url, headers, exp_id, version_name, request_doi=True):
    """Create a new version container under an experiment."""
    url = f"{base_url}/api/experiments/{exp_id}/versions"
    payload = {"version": version_name, "experimentId": int(exp_id), "requestDOI": request_doi}
    res = requests.post(url, json=payload, headers=headers)
    return res.status_code in (200, 201)


def set_version_visibility(base_url, headers, exp_id, version_name, is_public, license_id=None,
                           request_doi=True):
    """PATCH the version visibility/license. Returns the requests.Response."""
    payload = {"experimentId": int(exp_id), "version": version_name, "requestDOI": request_doi}
    if is_public:
        payload["isPublic"] = True
        payload["openAccess"] = True
        payload["license"] = license_id
    else:
        payload["isPublic"] = False
        payload["openAccess"] = False
    url = f"{base_url}/api/experiments/{exp_id}/versions/{version_name}"
    return requests.patch(url, json=payload, headers=headers)


# Creative-Commons licenses offered when publishing a version publicly.
LICENSES = {
    "cc0-1.0": "CC0 1.0 (Public Domain)",
    "cc-by-4.0": "CC BY 4.0 (Attribution)",
    "cc-by-sa-4.0": "CC BY-SA 4.0 (Attribution-ShareAlike)",
    "cc-by-nc-4.0": "CC BY-NC 4.0 (Attribution-NonCommercial)",
    "cc-by-nd-4.0": "CC BY-ND 4.0 (Attribution-NoDerivs)",
    "cc-by-nc-sa-4.0": "CC BY-NC-SA 4.0 (Attribution-NonCommercial-ShareAlike)",
    "cc-by-nc-nd-4.0": "CC BY-NC-ND 4.0 (Attribution-NonCommercial-NoDerivs)",
}


# =============================================================================
# Bathymetry hillshade plots (Overview + individual panels)
# =============================================================================
LEVEL_COLORS = ["#e74c3c", "#e67e22", "#27ae60", "#2980b9",
                "#8e44ad", "#16a085", "#c0392b", "#f39c12"]


def _custom_colormap(base_cmap, start_cut=0.0, end_cut=1.0):
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    if isinstance(base_cmap, str):
        try:
            original = plt.colormaps.get_cmap(base_cmap)
        except AttributeError:
            original = plt.cm.get_cmap(base_cmap)
    else:
        original = base_cmap
    return ListedColormap(original(np.linspace(start_cut, end_cut, 256)))


def _read_grd_data(path):
    import numpy as np
    import rasterio
    with rasterio.open(path) as src:
        data = np.flipud(src.read(1))
        x = np.linspace(src.bounds.left, src.bounds.right, src.width)
        y = np.linspace(src.bounds.bottom, src.bounds.top, src.height)
        res_x = abs(x[1] - x[0]) if x.size > 1 else 0
        res_y = abs(y[1] - y[0]) if y.size > 1 else 0
        return x, y, data, src.bounds, res_x, res_y


def _grid_area(path):
    import rasterio
    with rasterio.open(path) as src:
        b = src.bounds
        return (b.right - b.left) * (b.top - b.bottom)


def _hillshade_rgb(var_data):
    import numpy as np
    import cmocean
    from matplotlib.colors import LightSource
    abs_max = np.nanmax(np.abs(var_data)) + 1e-8
    sea = var_data < 0
    land = var_data >= 0
    img = np.zeros(var_data.shape + (3,), dtype=np.float32)

    cmap_land = _custom_colormap(cmocean.cm.turbid_r, 0.3, 0.7)
    cmap_sea = _custom_colormap("YlGnBu", 0.5, 1.0)
    if np.any(sea):
        img[sea] = cmap_sea(1.0 - ((var_data[sea] + abs_max) / abs_max))[:, :3]
    if np.any(land):
        img[land] = cmap_land(1.0 - (var_data[land] / abs_max))[:, :3]

    ls = LightSource(azdeg=315, altdeg=45)
    if np.any(land):
        elev = np.zeros_like(var_data); elev[land] = var_data[land]
        hill = 0.5 + 0.5 * ls.hillshade(elev, vert_exag=1.0, dx=1, dy=1)
        img[land] *= hill[land, None]
    if np.any(sea):
        elev = np.zeros_like(var_data); elev[sea] = -var_data[sea]
        hill = 0.5 + 0.5 * ls.hillshade(elev, vert_exag=1.0, dx=1, dy=1)
        img[sea] *= hill[sea, None]
    return img


def save_bathymetry_plots(parfile_path, output_dir):
    """Generate ``domain_overview.png`` and ``individual_grids.png`` from the parfile grids.

    Returns the list of written file paths (empty if no grids were found).
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    parser = TsunamiHySeaParser(parfile_path)
    parser.parse()

    grid_names = []
    if parser.data.get("id_bathymetry_file") not in (None, "0"):
        grid_names.append(os.path.basename(parser.data["id_bathymetry_file"]))
    for key, value in parser.data.items():
        if key.startswith("id_batimetry_file") and value and value != "0":
            name = os.path.basename(value)
            if name not in grid_names:
                grid_names.append(name)

    project_root = os.path.dirname(os.path.dirname(parfile_path))
    bathy_dir = os.path.join(project_root, "bathy")

    grids = []
    for name in grid_names:
        path = os.path.join(bathy_dir, name)
        if os.path.exists(path):
            grids.append({"name": name, "path": path, "area": _grid_area(path)})
    if not grids:
        print("[WARN] No bathymetry grids found for rendering.")
        return []

    grids.sort(key=lambda g: g["area"], reverse=True)
    n = len(grids)
    written = []

    # --- Overview: coarsest grid + nested-grid footprints ---
    _, _, cz, b0, _, _ = _read_grd_data(grids[0]["path"])
    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
    ax.imshow(_hillshade_rgb(cz), extent=[b0.left, b0.right, b0.bottom, b0.top],
              origin="lower", interpolation="nearest")
    ax.set_xlim(b0.left, b0.right); ax.set_ylim(b0.bottom, b0.top)
    for lvl, item in enumerate(grids):
        if lvl == 0:
            continue
        _, _, _, bb, _, _ = _read_grd_data(item["path"])
        col = LEVEL_COLORS[lvl % len(LEVEL_COLORS)]
        ax.add_patch(mpatches.Rectangle(
            (bb.left, bb.bottom), bb.right - bb.left, bb.top - bb.bottom,
            linewidth=2.5, edgecolor=col, facecolor="none", zorder=10))
    ax.set_title(f"Domain Overview: {os.path.basename(parfile_path)}", fontsize=8)
    p_ov = os.path.join(output_dir, "domain_overview.png")
    plt.savefig(p_ov, bbox_inches="tight", pad_inches=0.1)
    plt.close()
    written.append(p_ov)

    # --- Individual panels ---
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), dpi=300, squeeze=False)
    for idx, item in enumerate(grids):
        x, y, z, bb, res_x, res_y = _read_grd_data(item["path"])
        axes[0, idx].imshow(_hillshade_rgb(z), extent=[bb.left, bb.right, bb.bottom, bb.top],
                            origin="lower", interpolation="nearest", aspect="auto")
        axes[0, idx].set_title(f"L{idx}: {item['name']}", fontsize=7, fontweight="bold")
        axes[0, idx].text(0.02, 0.04, f"Spacing:\nX : {res_x:.4f}\nY : {res_y:.4f}",
                          transform=axes[0, idx].transAxes, fontsize=5, color="white",
                          ha="left", va="bottom",
                          bbox=dict(facecolor="black", alpha=0.6, pad=1.5))
        axes[0, idx].tick_params(axis="both", which="both", labelsize=4, length=2, pad=1)
    p_ind = os.path.join(output_dir, "individual_grids.png")
    plt.savefig(p_ind, bbox_inches="tight", pad_inches=0.1)
    plt.close()
    written.append(p_ind)

    print(f"✅ Bathymetry plots generated: {', '.join(os.path.basename(p) for p in written)}")
    return written


# =============================================================================
# Project README (HTML)
# =============================================================================
def _bathymetry_metadata(filepath):
    import rasterio
    try:
        with rasterio.open(filepath) as src:
            b = src.bounds
            res_x, _ = src.res
            return {
                "name": os.path.basename(filepath),
                "cells": f"{src.width} × {src.height}",
                "lon": f"{b.left:.4f} / {b.right:.4f}",
                "lat": f"{b.bottom:.4f} / {b.top:.4f}",
                "dx": f"{res_x:.6f}",
            }
    except Exception:
        return None


def generate_project_html(project_root, exp_name, description, output_filename="README.html"):
    """Write a styled README.html describing the experiment and its bathymetry grids."""
    bathy_dir = os.path.join(project_root, "bathy")
    rows = ""
    if os.path.exists(bathy_dir):
        for f in sorted(os.listdir(bathy_dir)):
            if f.endswith((".grd", ".nc")):
                meta = _bathymetry_metadata(os.path.join(bathy_dir, f))
                if meta:
                    rows += (f"<tr><td><code>{meta['name']}</code></td><td>{meta['cells']}</td>"
                             f"<td>{meta['lon']}</td><td>{meta['lat']}</td><td>{meta['dx']}</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .header-subtitle {{ color: #7f8c8d; font-style: italic; margin-bottom: 20px; }}
        .desc-box {{ background: #fdfdfd; border: 1px solid #e1e1e1; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .card {{ background: #f8f9fa; border-left: 5px solid #3498db; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th {{ background: #3498db; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border: 1px solid #ddd; }}
        tr:nth-child(even) {{ background: #f2f2f2; }}
        code {{ background: #eee; padding: 2px 5px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <h1>Experiment: {exp_name}</h1>
    <p class="header-subtitle">Project Documentation &amp; Bathymetric Specifications</p>
    <div class="desc-box">
        <h2>📝 Experiment Description</h2>
        <p>{description}</p>
    </div>
    <h2>📂 Folder Structure</h2>
    <div class="card">
        <code>/parfiles/</code> - Execution configuration files<br>
        <code>/scenario/</code> - Static bathymetry grids and spatial datasets<br>
        <code>/simulation/</code> - Dynamic output simulation runs
    </div>
    <h2>📊 Bathymetry Specifications</h2>
    <table>
        <tr><th>File</th><th>Cells (WxH)</th><th>Lon Range</th><th>Lat Range</th><th>dx</th></tr>
        {rows}
    </table>
</body>
</html>"""

    output_path = os.path.join(project_root, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ README written to: {output_path}")
    return output_path


# =============================================================================
# Manifest-driven (non-interactive / batch) publishing
# =============================================================================
# A YAML "manifest" holds only the human metadata (title, description, authors,
# organizations, projects, version, licence...). Everything technical (simulation
# name, grids, output prefixes, spatial coverage) is auto-derived from the parfile
# and the bathymetry grids at publish time. Credentials are NEVER stored in the
# manifest (passed as args or via SDL_USERNAME / SDL_PASSWORD).

SERVERS = {"prod": "https://sdl.hpc.cineca.it", "dev": "https://sdl-dev.hpc.cineca.it"}

MANIFEST_SCHEMA = {
    "type": "object",
    "required": ["experiment", "version", "publication"],
    "properties": {
        "sdl": {"type": "object",
                "properties": {"server": {"enum": ["prod", "dev"]}}},
        "experiment": {
            "type": "object", "required": ["mode"],
            "properties": {
                "mode": {"enum": ["new", "existing"]},
                "id": {"type": ["integer", "string", "null"]},
                "real_event": {"type": "object"},
                "title": {"type": ["string", "null"]},
                "description": {"type": ["string", "null"]},
                "code": {"type": "object"},
                "keywords": {"type": "array"},
                "authors": {"type": "array"},
                "organizations": {"type": "array"},
                "projects": {"type": "array"},
                "theme": {"type": "array", "items": {"enum": SDL_THEMES}},
                "requestDOI": {"type": "boolean"},
            },
        },
        "version": {
            "type": "object", "required": ["name"],
            "properties": {"name": {"type": "string"},
                           "create_if_missing": {"type": "boolean"}},
        },
        "publication": {
            "type": "object", "required": ["visibility"],
            "properties": {"visibility": {"enum": ["private", "public"]},
                           "license": {"type": ["string", "null"]}},
        },
        "project": {"type": "object"},
    },
}


def load_manifest(path):
    """Load + validate a YAML manifest, returning the dict (raises a clear error if invalid)."""
    import yaml
    import jsonschema
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Manifest is empty or not a YAML mapping.")
    jsonschema.validate(data, MANIFEST_SCHEMA)
    exp = data["experiment"]
    if exp["mode"] == "existing" and not exp.get("id"):
        raise ValueError("experiment.mode=existing requires experiment.id")
    pub = data["publication"]
    if pub["visibility"] == "public" and not pub.get("license"):
        raise ValueError("publication.visibility=public requires a 'license'")
    return data


def generate_manifest(project_dir, out_path=None):
    """Scan a project (parfiles/bathy/sim) and write an annotated YAML manifest skeleton.

    Auto-fills the technical fields and leaves the human fields as TODO. Returns the path.
    """
    root = os.path.abspath(project_dir)
    for d in ("parfiles", "bathy", "sim"):
        if not os.path.isdir(os.path.join(root, d)):
            raise FileNotFoundError(f"Missing /{d}/ in {root}")
    txts = sorted(f for f in os.listdir(os.path.join(root, "parfiles")) if f.lower().endswith(".txt"))
    if not txts:
        raise FileNotFoundError("No .txt parameter file in /parfiles/")
    parfile = txts[0]
    meta = scan_hysea_parfile(os.path.join(root, "parfiles", parfile))
    sim_name = meta.get("id_nombre", "")
    grids = list(dict.fromkeys(v for k, v in meta.items() if k.startswith("id_batimetry_file")))
    try:
        cov = get_largest_spatial_coverage(os.path.join(root, "bathy"))
        bbox = str(cov["geometry"]["coordinates"]) if cov else "(could not compute)"
    except Exception as e:
        bbox = f"(not computed: {type(e).__name__})"

    out_path = out_path or os.path.join(root, "sdl_manifest.yml")
    template = """# SDL manifest (auto-generated skeleton). Fill in the TODO fields, then publish with:
#   python sdl_publish_manifest.py publish __OUTNAME__
# Credentials are NOT stored here: set SDL_USERNAME / SDL_PASSWORD (or you are prompted).
#
# Auto-detected from the project:
#   parfile          : __PARFILE__
#   simulation name  : __SIMNAME__
#   bathymetry grids : __GRIDS__
#   spatial coverage : __BBOX__

sdl:
  server: prod                       # prod | dev

experiment:
  mode: new                          # new | existing
  id:                                # <-- required only if mode=existing
  real_event:
    is_real: false                   # true for a real-world event
    name: ""                         # e.g. Marques de Pombal
    date: ""                         # YYYY-MM-DD
  title: ""                          # empty -> "<event> (<date>)" or the parfile name
  description: "TODO: scientific description of the scenario"
  code:
    name: tsunami_hysea
    version: "TODO"                  # e.g. 4.3.0
  keywords: []                       # extra keywords (merged with the code's defaults)
  # authors / organizations / projects: by stable 'id' (recommended) or by 'name'
  # (the publisher searches by name and creates it if missing). Examples:
  #   authors:       [ {id: 58}, {name: {given: Jorge, family: Macias}, email: j@x} ]
  #   organizations: [ {id: 12} ]   or   [ {name: "University of Malaga"} ]
  #   projects:      [ {id: 7} ]    or   [ {name: "Geo-INQUIRE"} ]
  authors: []                        # TODO: at least one author for a new experiment
  organizations: []
  projects: []
  # theme: [geohazards]              # EPOS catalogue: geohazards | wavefms | seismicdata | volcanoobservatis
  requestDOI: true

version:
  name: "1.0.0"
  create_if_missing: true

publication:
  visibility: private                # private | public
  license: cc-by-4.0                 # required only if visibility=public

project:
  root: "."                          # relative to this manifest; folder with parfiles/ bathy/ sim/
  parfile: __PARFILE__               # auto-detected; change if there are several
  spatial_coverage: auto             # auto = bounding box of the largest grid -> EPSG:4326
"""
    text = (template
            .replace("__OUTNAME__", os.path.basename(out_path))
            .replace("__PARFILE__", parfile)
            .replace("__SIMNAME__", sim_name)
            .replace("__GRIDS__", ", ".join(grids) or "(none found)")
            .replace("__BBOX__", bbox))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Manifest skeleton written: {out_path}")
    return out_path


def _resolve_refs(base, headers, refs, endpoint, persons_cache=None):
    """Resolve manifest refs ({id} or {name...}) into cleaned objects for an experiment payload."""
    out = []
    if endpoint == "persons":
        pool = persons_cache if persons_cache is not None else list_persons(base, headers)
        by_id = {str(p.get("id")): p for p in pool}
        for ref in refs:
            if ref.get("id") is not None:
                obj = by_id.get(str(ref["id"]))
                if obj is None:
                    raise ValueError(f"Author id {ref['id']} not found on the server")
                cleaned = clean_for_post(obj, "persons")
            else:
                nm = ref.get("name", {}) or {}
                given, family = nm.get("given", ""), nm.get("family", "")
                match = next((p for p in pool
                              if p.get("givenName", "") == given and p.get("familyName", "") == family), None)
                if match:
                    cleaned = clean_for_post(match, "persons")
                else:
                    rec = create_person(base, headers, given, family,
                                        ref.get("email", ""), ref.get("qualifications", "Researcher"))
                    pool.append(rec)
                    cleaned = clean_for_post(rec, "persons")
            if cleaned.get("qualifications") is None:
                cleaned["qualifications"] = "Researcher"
            if cleaned.get("address") is None:
                cleaned["address"] = "Not Available"
            # the experiment-create endpoint rejects null emails/phones on authors
            if cleaned.get("emails") is None:
                cleaned["emails"] = []
            if cleaned.get("phones") is None:
                cleaned["phones"] = []
            out.append(cleaned)
        return out

    # organizations / projects
    pool = list_catalog(base, headers, endpoint)
    name_key = {"organizations": "legalName", "projects": "title"}[endpoint]
    by_id = {str(o.get("id")): o for o in pool}
    for ref in refs:
        if ref.get("id") is not None:
            obj = by_id.get(str(ref["id"]))
            if obj is None:
                raise ValueError(f"{endpoint[:-1]} id {ref['id']} not found on the server")
            cleaned = clean_for_post(obj, endpoint)
        else:
            nm = ref.get("name", "")
            match = next((o for o in pool if (o.get(name_key) or o.get("name")) == nm), None)
            cleaned = clean_for_post(match, endpoint) if match else create_catalog_item(base, headers, endpoint, nm)
        if endpoint == "projects":
            for k, dv in (("description", "No description provided"), ("funderName", "N/A"),
                          ("funderIdentifier", "N/A"), ("awardNumber", "N/A")):
                if cleaned.get(k) is None:
                    cleaned[k] = dv
        out.append(cleaned)
    return out


def publish_from_manifest(manifest_path, username=None, password=None, base_url=None,
                          token=None, headers=None, log=print):
    """Publish a Tsunami-HySEA project to the SDL fully from a YAML manifest (no interaction).

    Reproduces the 8 phases of the interactive notebook. Returns a summary dict.
    Pass an existing ``token`` + ``headers`` (and ``base_url``) to reuse a session
    (e.g. the notebook login) instead of logging in again.
    """
    m = load_manifest(manifest_path)
    base = base_url or SERVERS.get((m.get("sdl") or {}).get("server", "prod"), SERVERS["prod"])
    if token and headers:
        log(f"Using existing session on {base}")
    else:
        username = username or os.environ.get("SDL_USERNAME")
        password = password or os.environ.get("SDL_PASSWORD")
        if not username or not password:
            raise ValueError("No credentials: pass username/password, token+headers, or set SDL_USERNAME / SDL_PASSWORD.")
        token = get_auth_token(base, username, password)
        headers = auth_headers(token)
        log(f"Login OK on {base}")

    mdir = os.path.dirname(os.path.abspath(manifest_path))
    proj = m.get("project") or {}
    root = os.path.abspath(os.path.join(mdir, proj.get("root", ".")))
    par_dir = os.path.join(root, "parfiles")
    bathy_dir = os.path.join(root, "bathy")
    sim_dir = os.path.join(root, "sim")
    parfile = proj.get("parfile")
    if not parfile:
        parfile = sorted(f for f in os.listdir(par_dir) if f.lower().endswith(".txt"))[0]
    parfile_path = os.path.join(par_dir, parfile)

    exp = m["experiment"]
    if exp["mode"] == "existing":
        exp_id = exp["id"]
        title = f"Experiment {exp_id}"
        log(f"Using existing experiment {exp_id}")
    else:
        re_ = exp.get("real_event") or {}
        if re_.get("is_real"):
            title = (f"{re_.get('name', '').strip()} ({re_.get('date', '').strip()})").strip()
        else:
            title = (exp.get("title") or "").strip() or os.path.splitext(parfile)[0]
        keywords = list(exp.get("keywords") or [])
        theme, note = resolve_theme(exp), ""
        code = exp.get("code") or {}
        if code.get("name"):
            cm = get_metadata_for_code(code["name"])
            keywords = list(dict.fromkeys(keywords + cm.get("keywords", [])))
            note = (f"\n\n---\nGenerated with: {cm.get('display_name')} "
                    f"({code.get('version', 'unknown')})\nConfiguration file: {parfile}")
        description = ((exp.get("description") or "").strip() + note).strip()
        persons_cache = list_persons(base, headers)
        authors = _resolve_refs(base, headers, exp.get("authors") or [], "persons", persons_cache)
        if not authors:
            raise ValueError("A new experiment needs at least one author.")
        orgs = _resolve_refs(base, headers, exp.get("organizations") or [], "organizations")
        projs = _resolve_refs(base, headers, exp.get("projects") or [], "projects")
        exp_id = create_experiment(base, headers, title, description, theme, authors, keywords, orgs, projs,
                                   request_doi=exp.get("requestDOI", True))
        log(f"Created experiment {exp_id}: {title}")

    # version
    ver = m["version"]["name"]
    existing = {v.get("version") for v in list_versions(base, headers, exp_id)}
    if ver not in existing:
        if not m["version"].get("create_if_missing", True):
            raise ValueError(f"Version {ver} does not exist and create_if_missing is false.")
        if not create_version(base, headers, exp_id, ver, request_doi=exp.get("requestDOI", True)):
            raise RuntimeError(f"The server rejected version name '{ver}'. "
                               f"Use a valid semantic version, e.g. 1.0.0.")
        # Confirm the version is queryable before uploading into it (the API can return 2xx
        # on the POST yet not persist a malformed version name -> later 404 'version not found').
        if ver not in {v.get("version") for v in list_versions(base, headers, exp_id)}:
            raise RuntimeError(f"Version '{ver}' is not found after creation; aborting before "
                               f"upload. Check the version name is a valid semantic version.")
        log(f"Created version {ver}")
    else:
        log(f"Using existing version {ver}")

    # --- scenario dataset + bathymetry: uploaded ONCE. When 'reuse_scenario' is set (adding
    # more simulations to an existing experiment) the bathymetry/plots are NOT re-uploaded;
    # the new simulations just link to the already-existing scenario dataset path. ---
    reuse = bool(proj.get("reuse_scenario", False))
    scen_name = proj.get("scenario_name", "event_data")
    if reuse:
        scen = "scenario/" + scen_name
        log(f"Reusing existing scenario dataset: {scen} (bathymetry NOT re-uploaded)")
    else:
        save_bathymetry_plots(parfile_path, root)
        sc = proj.get("spatial_coverage", "auto")
        cov = get_largest_spatial_coverage(bathy_dir) if sc == "auto" else sc
        scen = create_scenario_dataset(base, headers, exp_id, ver, cov, scen_name)
        log(f"Scenario dataset: {scen}")
        statics = [os.path.join(bathy_dir, f) for f in os.listdir(bathy_dir) if f.endswith((".grd", ".nc"))]
        for g in ("domain_overview.png", "individual_grids.png"):
            p = os.path.join(root, g)
            if os.path.exists(p):
                statics.append(p)
        for fp in statics:
            full_upload_flow(base, token, exp_id, ver, fp, "scenario/" + os.path.basename(fp), log=log)
    for f in os.listdir(par_dir):
        if f.endswith((".txt", ".par")):
            full_upload_flow(base, token, exp_id, ver, os.path.join(par_dir, f), "parfiles/" + f, log=log)
    for p_file in os.listdir(par_dir):
        if not p_file.endswith((".par", ".txt")):
            continue
        pm = scan_hysea_parfile(os.path.join(par_dir, p_file))
        s_name = pm.get("id_nombre")
        prefixes = [v for k, v in pm.items() if k.startswith("id_NetCDF_prefix")]
        if not s_name or not prefixes:
            continue
        matches = [os.path.join(r, f) for r, _, fl in os.walk(sim_dir)
                   for f in fl if any(f.startswith(px) for px in prefixes)]
        if not matches:
            continue
        sp = create_simulation_flow(base, headers, exp_id, ver, s_name, "Sim run: " + p_file, scen)
        if sp:
            for mf in matches:
                full_upload_flow(base, token, exp_id, ver, mf, sp + os.path.relpath(mf, sim_dir), log=log)

    # README + visibility/licence (skipped in append mode: only adding simulations,
    # so the existing README and publication state are left untouched).
    if not reuse:
        readme = generate_project_html(root, title, (exp.get("description") or ""))
        full_upload_flow(base, token, exp_id, ver, readme, "README.html", log=log)
        pub = m["publication"]
        is_pub = pub["visibility"] == "public"
        res = set_version_visibility(base, headers, exp_id, ver, is_pub,
                                     pub.get("license") if is_pub else None,
                                     request_doi=exp.get("requestDOI", True))
        state = ("PUBLIC (" + str(pub.get("license")) + ")") if is_pub else "PRIVATE"
        log(f"Visibility: {state} -> HTTP {res.status_code}")
    else:
        log("Append mode: scenario, README and visibility left untouched.")
    log(f"Done. Experiment {exp_id} version {ver} -> {base}/app/")
    return {"experiment_id": exp_id, "version": ver, "base_url": base}
