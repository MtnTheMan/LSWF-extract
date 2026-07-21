#!/usr/bin/env python3
"""Track and validate the LSWF production workflow.

The workflow manifest is intentionally broader than the repo's scripts: it includes
manual/external ArcGIS Pro steps, prototype scripts, export steps, validation, and
summary-statistics work. Existing production scripts are preserved and mapped into a
single ordered ledger.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "workflow" / "workflow_manifest.json"
DEFAULT_STATE = REPO_ROOT / "workflow" / "workflow_state.json"
VALID_STATUSES = ("pending", "in_progress", "completed")


@dataclass(frozen=True)
class WorkflowStep:
    stage_id: str
    stage_title: str
    step_id: str
    step_title: str
    execution_type: str
    notebooks: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    documentation_refs: List[str] = field(default_factory=list)


def normalize_repo_path(path: str) -> str:
    """Normalize manifest/discovered paths for cross-platform validation."""
    return path.replace("\\", "/")


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_steps(manifest: Dict[str, Any]) -> Iterable[WorkflowStep]:
    for stage in manifest["stages"]:
        for step in stage["steps"]:
            yield WorkflowStep(
                stage_id=stage["id"],
                stage_title=stage["title"],
                step_id=step["id"],
                step_title=step["title"],
                execution_type=step.get("execution_type", "arcpy_script"),
                notebooks=step.get("notebooks", []),
                inputs=step.get("inputs", []),
                outputs=step.get("outputs", []),
                parameters=step.get("parameters", {}),
                documentation_refs=step.get("documentation_refs", []),
            )


def init_state(manifest: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": manifest["name"],
        "manifest_version": manifest["version"],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "steps": {
            step.step_id: {
                "stage_id": step.stage_id,
                "step_title": step.step_title,
                "execution_type": step.execution_type,
                "status": "pending",
                "notes": "",
                "completed_at_utc": None,
            }
            for step in iter_steps(manifest)
        },
    }


def reconcile_state(manifest: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve notes/status while adding new manifest steps and refreshing metadata."""
    state.setdefault("steps", {})
    state["name"] = manifest["name"]
    state["manifest_version"] = manifest["version"]

    for step in iter_steps(manifest):
        existing = state["steps"].setdefault(
            step.step_id,
            {
                "status": "pending",
                "notes": "",
                "completed_at_utc": None,
            },
        )
        existing["stage_id"] = step.stage_id
        existing["step_title"] = step.step_title
        existing["execution_type"] = step.execution_type
        existing.setdefault("status", "pending")
        existing.setdefault("notes", "")
        existing.setdefault("completed_at_utc", None)

    return state


def load_or_init_state(manifest: Dict[str, Any], state_path: Path) -> Dict[str, Any]:
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return reconcile_state(manifest, state)

    state = init_state(manifest)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    save_state(state, state_path)
    return state


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def compact_list(values: List[str]) -> str:
    return ", ".join(values) if values else "none"


def list_workflow(manifest: Dict[str, Any], state: Dict[str, Any]) -> None:
    print(f"Workflow: {manifest['name']} (manifest {manifest['version']})")
    for stage in manifest["stages"]:
        print(f"\n[{stage['id']}] {stage['title']}")
        if stage.get("purpose"):
            print(f"  Purpose: {stage['purpose']}")
        for step in stage["steps"]:
            step_state = state["steps"].get(step["id"], {})
            status = step_state.get("status", "pending")
            execution_type = step.get("execution_type", "arcpy_script")
            print(f"  - {step['id']} [{status}] ({execution_type}) {step['title']}")
            notebooks = step.get("notebooks", [])
            if notebooks:
                for nb in notebooks:
                    print(f"      script: {nb}")
            else:
                print("      script: none; tracked as documented/manual workflow step")


def show_step(manifest: Dict[str, Any], state: Dict[str, Any], step_id: str) -> None:
    for step in iter_steps(manifest):
        if step.step_id != step_id:
            continue

        step_state = state["steps"].get(step_id, {})
        print(f"{step.step_id}: {step.step_title}")
        print(f"Stage: {step.stage_id} - {step.stage_title}")
        print(f"Status: {step_state.get('status', 'pending')}")
        print(f"Execution type: {step.execution_type}")
        print(f"Inputs: {compact_list(step.inputs)}")
        print(f"Outputs: {compact_list(step.outputs)}")
        print(f"Documentation refs: {compact_list(step.documentation_refs)}")
        if step.parameters:
            print("Parameters:")
            print(json.dumps(step.parameters, indent=2))
        if step.notebooks:
            print("Scripts:")
            for nb in step.notebooks:
                print(f"  - {nb}")
        else:
            print("Scripts: none")
        notes = step_state.get("notes")
        if notes:
            print(f"Notes: {notes}")
        return

    valid = ", ".join(sorted(step.step_id for step in iter_steps(manifest)))
    raise SystemExit(f"Unknown step_id '{step_id}'. Valid values: {valid}")


def set_step_status(state: Dict[str, Any], step_id: str, status: str, note: str) -> None:
    if step_id not in state["steps"]:
        valid = ", ".join(sorted(state["steps"].keys()))
        raise SystemExit(f"Unknown step_id '{step_id}'. Valid values: {valid}")

    step_state = state["steps"][step_id]
    step_state["status"] = status
    if note:
        step_state["notes"] = note
    if status == "completed":
        step_state["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    elif status in {"pending", "in_progress"}:
        step_state["completed_at_utc"] = None


def next_pending(manifest: Dict[str, Any], state: Dict[str, Any]) -> None:
    for stage in manifest["stages"]:
        for step in stage["steps"]:
            step_state = state["steps"].get(step["id"], {})
            if step_state.get("status", "pending") != "completed":
                print(step["id"])
                print(step["title"])
                print(f"stage: {stage['id']}")
                print(f"execution_type: {step.get('execution_type', 'arcpy_script')}")
                notebooks = step.get("notebooks", [])
                if notebooks:
                    for nb in notebooks:
                        print(nb)
                else:
                    print("No repo script; documented/manual workflow step.")
                return
    print("No pending steps. Workflow is complete.")


def validate_manifest_coverage(manifest: Dict[str, Any], root: Path) -> int:
    workflow_files: Set[str] = set()
    duplicates: Set[str] = set()
    missing_paths: List[str] = []
    manual_steps = 0

    for step in iter_steps(manifest):
        if not step.notebooks:
            manual_steps += 1
        for nb in step.notebooks:
            normalized = normalize_repo_path(nb)
            if normalized in workflow_files:
                duplicates.add(normalized)
            workflow_files.add(normalized)
            if not (root / nb).exists():
                missing_paths.append(nb)

    discovered = {
        normalize_repo_path(str(p.relative_to(root)))
        for p in root.rglob("*.ipynb")
        if ".git" not in p.parts
    }

    uncovered = sorted(discovered - workflow_files)

    has_errors = False
    if missing_paths:
        has_errors = True
        print("ERROR: These manifest script paths do not exist:")
        for nb in missing_paths:
            print(f"  - {nb}")

    if uncovered:
        has_errors = True
        print("ERROR: These .ipynb script files are not mapped in the workflow manifest:")
        for nb in uncovered:
            print(f"  - {nb}")

    if duplicates:
        has_errors = True
        print("ERROR: These script files are mapped more than once:")
        for nb in sorted(duplicates):
            print(f"  - {nb}")

    if not has_errors:
        print(f"Coverage OK: mapped {len(workflow_files)} .ipynb script files.")
        print(f"Documented/manual steps with no repo script: {manual_steps}.")
        return 0
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LSWF production workflow tracker")
    parser.add_argument("command", choices=["list", "init", "set", "next", "show", "validate"])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--step-id", default="")
    parser.add_argument("--status", choices=VALID_STATUSES, default="pending")
    parser.add_argument("--note", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    if args.command == "validate":
        return validate_manifest_coverage(manifest, REPO_ROOT)

    if args.command == "init":
        state = init_state(manifest)
        save_state(state, args.state)
        print(f"Initialized state file at {args.state}")
        return 0

    state = load_or_init_state(manifest, args.state)

    if args.command == "list":
        list_workflow(manifest, state)
    elif args.command == "show":
        if not args.step_id:
            raise SystemExit("--step-id is required for 'show'")
        show_step(manifest, state, args.step_id)
    elif args.command == "set":
        if not args.step_id:
            raise SystemExit("--step-id is required for 'set'")
        set_step_status(state, args.step_id, args.status, args.note)
        save_state(state, args.state)
        print(f"Updated {args.step_id} -> {args.status}")
    elif args.command == "next":
        next_pending(manifest, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
