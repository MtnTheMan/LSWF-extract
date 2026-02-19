# LSWF Extract - Cohesive Workflow Layer

This repository already contains the full set of notebooks used for the Linear Small Woody Features (LSWF) workflow. To make those pieces operate as **one trackable flow** (without removing any existing code), this repo now includes a workflow layer in `workflow/`:

- `workflow/workflow_manifest.json`: canonical ordered map of workflow phases/steps -> existing notebooks.
- `workflow/lswf_workflow.py`: CLI to validate coverage and track progress across all steps.
- `workflow/workflow_state.json`: generated state file that records status (`pending`, `in_progress`, `completed`) and notes per step.

## Workflow phases (aligned to your full process chart)

1. **Sub-Meter Land Cover Classification**
2. **Default Trees Outside Forests (ToF) Filtering**
3. **Voronoi Segmentation and Centerline Processing**
4. **Best Polygon Selection + Final Exports**
5. **Summary Statistics + Post-processing (per-county counting basis)**

## Why this helps

- Preserves all notebooks and historical variants exactly as-is.
- Adds one explicit execution order across sections/folders.
- Ensures every notebook in the repo is represented in the unified method.
- Adds progress/state tracking so runs are reproducible and auditable.

## Usage

```bash
# 1) Verify every notebook is mapped into the unified workflow
python workflow/lswf_workflow.py validate

# 2) Initialize a tracking file
python workflow/lswf_workflow.py init

# 3) See all stages + step status + mapped notebooks
python workflow/lswf_workflow.py list

# 4) Move a step to in-progress/completed with notes
python workflow/lswf_workflow.py set --step-id county_extract_and_buffer --status in_progress --note "Started 2026 run"
python workflow/lswf_workflow.py set --step-id county_extract_and_buffer --status completed --note "All counties extracted"

# 5) Show the next not-yet-complete step
python workflow/lswf_workflow.py next
```

## Notes

- The script is intentionally lightweight and standard-library only.
- If you add new notebooks later, rerun `validate` and update `workflow_manifest.json`.
