# LSWF Extract

This repository preserves the original ArcPy/Jupyter-style script files used to extract
Linear Small Woody Features (LSWFs), and adds a workflow layer that reconstructs the
full production process from NAIP imagery through per-county summary statistics.

The workflow layer is intentionally additive: it does not remove or rewrite the original
production scripts. It provides notation, order, dependencies, parameters, inputs,
outputs, and status tracking around the existing work.

## Core Workflow Files

- `workflow/PRODUCTION_WORKFLOW.md` - thesis-grounded narrative workflow with notation,
  stage order, thresholds, and script mapping.
- `workflow/REPO_SCOPE_NOTES.md` - notes on where this repository sits in the overall
  production process, including what it can and cannot represent or execute by itself.
- `workflow/workflow_manifest.json` - machine-readable manifest for all coded and
  manual/external production steps.
- `workflow/lswf_workflow.py` - lightweight tracker and validator for the manifest.
- `workflow/workflow_state.json` - initialized status ledger for the workflow steps.

## Workflow Summary

The full production process is:

1. Define study counties, imagery sources, projections, and NAIP inputs.
2. Mosaic 2022 4-band NAIP imagery and run the U-Net/CNN land-cover classifier.
3. Clip/extract county land-cover rasters.
4. Build continuous-forest masks with the shrink-expand method.
5. Derive Trees Outside Forests (ToF) rasters.
6. Polygonize ToFs and apply the initial size/shape filtering.
7. Generate centerlines and split connected ToF networks.
8. Build Thiessen/Voronoi segments from centerline points.
9. Calculate SNFI, WSI, Euclidean length, and related fields for parent and segmented
   polygons.
10. Select the best parent or Voronoi polygon representation for the final LSWF layer.
11. Export, clean, summarize, validate, and analyze the final county outputs.

See `workflow/PRODUCTION_WORKFLOW.md` for the detailed notation and stage-by-stage map.
See `workflow/REPO_SCOPE_NOTES.md` for the representation/execution boundaries of this
repository.

## Using the Tracker

Run the tracker from the repository root:

```powershell
python workflow/lswf_workflow.py validate
python workflow/lswf_workflow.py init
python workflow/lswf_workflow.py list
python workflow/lswf_workflow.py next
python workflow/lswf_workflow.py show --step-id shrink_expand_forest_mask
python workflow/lswf_workflow.py set --step-id shrink_expand_forest_mask --status in_progress --note "Started county batch"
python workflow/lswf_workflow.py set --step-id shrink_expand_forest_mask --status completed --note "All counties complete"
```

The manifest includes manual/external ArcGIS Pro steps as first-class workflow steps, so
not every step has an associated script in this repository.

## Notes

- Most `.ipynb` files in this repository are plain ArcPy script text saved with notebook
  extensions. The workflow layer treats them as production scripts, not necessarily as
  executable Jupyter notebook JSON.
- The manifest tracks the thesis/Appendix C production logic, including upstream steps
  that were not originally captured as repo scripts.
- Thresholds are recorded in the manifest and workflow document. The current final
  filtering script uses `wsi_threshold = 2.0`, while the thesis/flowchart notation also
  references a WSI value of `3.0`; the workflow records that as a provenance item to
  resolve rather than silently choosing one.
