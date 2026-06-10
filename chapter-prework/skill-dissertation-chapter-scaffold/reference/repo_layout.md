# PhD chapter project repo layout

The repo is initialized in Stage 3 of the workflow, before any analysis or scaffold generation. It hosts everything the chapter produces — code, data references, decisions log, scaffold .docx, bibliography, monthly How-Tos.

## Standard layout

```
chapter-<slug>/
├── README.md                           # one-page chapter overview
├── environment.yml                     # conda env spec (Python chapters)
├── renv.lock                           # OR R environment spec (R chapters)
├── .gitignore                          # excludes data/, results/, __pycache__
├── data/
│   ├── raw/                            # immutable, never modified
│   ├── interim/                        # cleaned, time-aligned
│   └── processed/                      # feature sets for modeling
├── scripts/                            # numbered, runnable Python (or R) scripts
│   ├── 01_eda.py
│   ├── 02_<analysis_step>.py
│   ├── 03_<analysis_step>.py
│   └── ...                             # one per analysis step, in run order
├── src/                                # stable importable package
│   ├── __init__.py
│   ├── io_data.py                      # one reader/writer entry point per source
│   ├── features.py                     # feature engineering
│   ├── models/                         # one file per model family
│   │   └── __init__.py
│   └── eval.py                         # evaluation protocol
├── results/                            # plots, tables, model artifacts (gitignored)
│   ├── figures/
│   ├── tables/
│   └── models/
├── docs/                               # all chapter documents live here
│   ├── chapter-scaffold.docx           # output of Stage 4
│   ├── chapter-references.bib          # output of Stage 6
│   ├── reference-manager-import.docx   # output of Stage 6 (if used)
│   ├── month-1-howto.docx              # output of Stage 7
│   ├── month-2-howto.docx
│   ├── month-3-howto.docx
│   ├── predecessor-notes.md            # structured notes from reading predecessor work
│   ├── decisions.md                    # running log of methodological decisions
│   └── data-requests.md                # tracking of data acquisitions
└── tests/                              # optional, for src/ functions
```

## Setup commands

Replace `<slug>` with a short identifier for the chapter (e.g. `flood-anomaly`, `social-network`, `material-fatigue`).

```bash
mkdir -p chapter-<slug>/{data/{raw,interim,processed},scripts,src/models,results/{figures,tables,models},docs,tests}
cd chapter-<slug>
git init
touch src/__init__.py src/models/__init__.py
```

`.gitignore`:

```
data/raw/
data/interim/
data/processed/
results/
__pycache__/
*.pyc
.ipynb_checkpoints/
.DS_Store
.env
*.egg-info/
```

`README.md` (initial):

```markdown
# Chapter: <chapter title>

**Claim**: <one-sentence claim from Stage 2>

**Methodological frame**: <named methods>

**Data window** (if applicable): <dates>

**Predecessor work** (if any): <citations>

## How to reproduce

1. conda env create -f environment.yml && conda activate chapter-<slug>
2. Run scripts in order: `python scripts/01_eda.py` through `python scripts/N_*.py`
3. Outputs land in `results/` and `data/processed/`

## Repo structure

(brief description of the directory layout)
```

`docs/decisions.md` (initial entry):

```markdown
# Decisions log

## 2026-MM-DD — Chapter claim

<one-sentence claim>

Alternatives considered: <if any>
Reasoning: <why this framing>
```

## Environment specs per methodological family

### Anomaly detection / time-series ML (Python)

```yaml
name: chapter-<slug>
channels: [conda-forge, defaults]
dependencies:
  - python=3.11
  - numpy, pandas, scipy
  - matplotlib, seaborn
  - statsmodels       # ARIMA family, stationarity tests
  - scikit-learn      # Isolation Forest, regression baselines
  - pip
  - pip:
      - filterpy      # Kalman filters
      - ipython       # REPL only, no notebooks
```

### General statistical modelling (Python)

```yaml
name: chapter-<slug>
channels: [conda-forge, defaults]
dependencies:
  - python=3.11
  - numpy, pandas, scipy
  - matplotlib, seaborn
  - statsmodels
  - pingouin          # statistical tests beyond scipy
  - pymc              # Bayesian (if needed)
  - pip:
      - ipython
```

### Spatial / geospatial (Python)

```yaml
name: chapter-<slug>
channels: [conda-forge, defaults]
dependencies:
  - python=3.11
  - numpy, pandas, scipy
  - geopandas, rasterio, xarray, rioxarray
  - matplotlib, contextily
  - shapely, fiona, pyproj
  - pip:
      - ipython
```

### R-based (statistical or biostatistical chapters)

```r
# In R: install.packages("renv"); renv::init()
# Then renv will track the libraries used in scripts/
```

Suggested core packages: `tidyverse`, `lme4` or `brms`, `survival`, `pwr`, `here`, `targets`.

### Qualitative / theoretical

Minimal `environment.yml` (Python for any text processing) plus a pointer to the reference manager. The repo's center of gravity is `docs/` rather than `scripts/`.

## File naming conventions

- Scripts: `NN_<verb>_<noun>.py` (zero-padded, underscores). Order matters and is documented.
- Data files in `raw/`: descriptive names with source and date (`worm-discharge-wver-2025-2026.csv`)
- Results: parallel to script names (`results/figures/02_barometric_baseline_residuals.png`)
- Docs: kebab-case (`predecessor-notes.md`)

## When the user has an existing repo

If the user already has a project repo (from earlier work or a prior chapter), the skill should adapt rather than overwrite. Confirm:
- Existing directory layout — adopt it if reasonable
- Existing environment — extend rather than replace
- Existing decisions log — append to it
- Existing `docs/` — generated outputs land alongside whatever's there

The skill is opinionated about structure but pragmatic about disruption — never wipe an existing repo to impose this layout.
