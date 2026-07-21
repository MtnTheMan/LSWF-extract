# Repository Scope Notes

This note explains where `LSWF-extract` sits within the full Linear Small Woody Feature
(LSWF) production process and what the repository can and cannot do by itself.

## Short Version

This repository is best understood as a production-method reconstruction and script
ledger for the LSWF extraction workflow. It preserves the ArcPy scripts and adds
workflow notation around them, but it is not a self-contained, push-button pipeline from
raw NAIP imagery to final LSWF outputs.

The full production process spans:

1. Source imagery preparation.
2. CNN land-cover classification.
3. ArcGIS raster processing and shrink-expand forest masking.
4. ToF polygon extraction.
5. Centerline and Voronoi segmentation.
6. Shape-metric calculation.
7. Best-polygon selection.
8. Final exports, summaries, QA, validation, and analysis.

The repository represents many of steps 3 through 8 as ArcPy scripts, and it documents
steps 1, 2, and portions of QA/validation that occurred outside the repo.

## Where the Repo Sits in the Process

The repo begins to become directly executable after classified county land-cover rasters
exist. The upstream land-cover creation process is required, but it is represented here
as documented/manual workflow steps rather than runnable code.

In practical terms:

- The repo assumes county-level classified land-cover rasters or derived ToF rasters
  already exist in the expected GIS workspace.
- The repo contains scripts that help isolate ToFs, polygonize ToFs, calculate shape
  metrics, generate centerlines, split complex ToF networks, create Voronoi segments,
  choose best polygons, and create summary outputs.
- The repo now includes a workflow manifest that records upstream and manual steps, even
  when no script exists for those steps.

## What the Repo Can Do

The repository can:

- Preserve the original production scripts and historical variants without removing
  provenance.
- Map every `.ipynb` ArcPy script file into a documented workflow stage.
- Track workflow status across coded and non-coded steps using `workflow_state.json`.
- Validate whether all `.ipynb` script files are represented in `workflow_manifest.json`.
- Describe the order of operations from source imagery through final summaries.
- Record inputs, outputs, parameters, thresholds, and known provenance questions.
- Distinguish manual/external ArcGIS Pro steps from script-backed steps.
- Serve as a method notebook for future re-runs, audits, or refactoring.
- Help identify missing or uncertain production pieces, such as the CNN classification
  step and county-code coverage checks.

With the right ArcGIS Pro environment, licenses, extensions, source data, model files,
and filesystem paths, many of the script-backed stages could be run or adapted from this
repo.

## What the Repo Cannot Do by Itself

The repository cannot, by itself:

- Download or stage the 2022 NAIP imagery.
- Recreate the county NAIP mosaics unless the source imagery and ArcGIS environment are
  already present.
- Run the U-Net/CNN land-cover model, because the model package and full ArcGIS image
  classification workflow are not included as repo code.
- Guarantee all original `X:\...` production paths exist on another machine.
- Provide the file geodatabases, shapefiles, rasters, validation datasets, or final
  production outputs that were generated outside Git.
- Replace ArcGIS Pro, Spatial Analyst, Topographic Production tools, or other licensed
  ArcGIS capabilities used by the scripts.
- Guarantee that the `.ipynb` files are valid Jupyter notebooks; most are plain ArcPy
  script text saved with `.ipynb` extensions.
- Resolve manual QA decisions, one-off ArcGIS corrections, or visual validation steps
  without the original analyst context and data.
- Confirm the canonical final WSI threshold without a provenance decision, because the
  thesis/flowchart documentation references `3.0` while the current final filtering
  script uses `2.0`.

## Representation vs Execution

The workflow files have two related but different roles:

- `workflow/PRODUCTION_WORKFLOW.md` describes the full scientific/production workflow in
  human-readable form.
- `workflow/workflow_manifest.json` expresses that workflow in machine-readable form for
  validation and status tracking.
- `workflow/lswf_workflow.py` validates script coverage and manages step status.

Those files make the process auditable, but they do not make every step executable. A
manual/external step in the manifest is a real production dependency, not a script that
the tracker can run.

## Practical Use Cases

Use this repo when you need to:

- Understand how the LSWF product was produced.
- See which scripts correspond to each section of the thesis workflow.
- Reconstruct the order of operations for a future production run.
- Track progress across counties or workflow stages.
- Identify which steps require ArcGIS Pro/manual execution.
- Prepare a future refactor into `.py` modules, ArcGIS notebooks, or a more formal
  pipeline.

Do not treat this repo as a complete packaged application unless the missing upstream
data, ArcGIS model assets, geodatabases, workspace paths, and QA procedures have been
supplied and checked.

## Known Boundary Items

The following items are intentionally called out so they are not hidden in the workflow:

- CNN land-cover classification is documented as a required upstream process but is not
  present as a repo script.
- The shrink-expand and ToF scripts depend on classified land-cover rasters, especially
  the tree canopy class.
- The current workflow records both the thesis/flowchart WSI value of `3.0` and the
  script value of `2.0`; this should be resolved or documented as a production change.
- `FilteringPolygons/CenterlineWorking/PolygonToCenterline.ipynb` appears to omit
  `W2OH` from its centerline input list, while downstream all-county scripts include it.
- The workflow is intentionally additive and does not rename, delete, or convert the
  historical scripts.

## Best Next Refactor, If Desired

A future refactor could make the repo more executable by:

1. Converting plain-text `.ipynb` scripts to `.py` modules or valid ArcGIS notebooks.
2. Moving hard-coded paths and county lists into config files.
3. Adding a data manifest for required rasters, shapefiles, geodatabases, model files,
   and expected output directories.
4. Creating dry-run checks that verify ArcGIS extensions, source paths, and county
   coverage before long production jobs begin.
5. Adding explicit provenance notes for final threshold choices and one-off manual
   corrections.
