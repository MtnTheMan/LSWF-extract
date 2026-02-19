#!/usr/bin/env python3
"""Track and validate a cohesive LSWF notebook workflow.

This script does not remove/replace existing notebooks. It layers a single,
stateful workflow on top of them using a JSON manifest.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "workflow" / "workflow_manifest.json"
DEFAULT_STATE = REPO_ROOT / "workflow" / "workflow_state.json"


@dataclass(frozen=True)
class WorkflowStep:
    stage_id: str
    stage_title: str
    step_id: str
    step_title: str
    notebooks: List[str]


def load_manifest(path: Path) -> Dict:
    return json.loads(path.read_text())


def iter_steps(manifest: Dict) -> Iterable[WorkflowStep]:
    for stage in manifest["stages"]:
        for step in stage["steps"]:
            yield WorkflowStep(
                stage_id=stage["id"],
                stage_title=stage["title"],
                step_id=step["id"],
                step_title=step["title"],
                notebooks=step["notebooks"],
            )


def init_state(manifest: Dict) -> Dict:
    return {
        "name": manifest["name"],
        "manifest_version": manifest["version"],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "steps": {
            step.step_id: {
                "stage_id": step.stage_id,
                "status": "pending",
                "notes": "",
                "completed_at_utc": None,
            }
            for step in iter_steps(manifest)
        },
    }


def load_or_init_state(manifest: Dict, state_path: Path) -> Dict:
    if state_path.exists():
        return json.loads(state_path.read_text())
    state = init_state(manifest)
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    return state


def save_state(state: Dict, state_path: Path) -> None:
    state["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    state_path.write_text(json.dumps(state, indent=2) + "\n")


def list_workflow(manifest: Dict, state: Dict) -> None:
    print(f"Workflow: {manifest['name']} (manifest {manifest['version']})")
    for stage in manifest["stages"]:
        print(f"\n[{stage['id']}] {stage['title']}")
        for step in stage["steps"]:
            step_state = state["steps"].get(step["id"], {})
            status = step_state.get("status", "pending")
            print(f"  - {step['id']} [{status}] {step['title']}")
            for nb in step["notebooks"]:
                print(f"      • {nb}")


def set_step_status(state: Dict, step_id: str, status: str, note: str) -> None:
    if step_id not in state["steps"]:
        valid = ", ".join(sorted(state["steps"].keys()))
        raise SystemExit(f"Unknown step_id '{step_id}'. Valid values: {valid}")

    step_state = state["steps"][step_id]
    step_state["status"] = status
    if note:
        step_state["notes"] = note
    if status == "completed":
        step_state["completed_at_utc"] = datetime.now(timezone.utc).isoformat()


def next_pending(manifest: Dict, state: Dict) -> None:
    for stage in manifest["stages"]:
        for step in stage["steps"]:
            if state["steps"][step["id"]]["status"] != "completed":
                print(step["id"])
                print(step["title"])
                for nb in step["notebooks"]:
                    print(nb)
                return
    print("No pending steps. Workflow is complete.")


def validate_manifest_coverage(manifest: Dict, root: Path) -> int:
    workflow_files: Set[str] = set()
    missing_paths: List[str] = []

    for step in iter_steps(manifest):
        for nb in step.notebooks:
            workflow_files.add(nb)
            if not (root / nb).exists():
                missing_paths.append(nb)

    discovered = {
        str(p.relative_to(root))
        for p in root.rglob("*.ipynb")
        if ".git" not in p.parts
    }

    uncovered = sorted(discovered - workflow_files)

    has_errors = False
    if missing_paths:
        has_errors = True
        print("ERROR: These manifest notebook paths do not exist:")
        for nb in missing_paths:
            print(f"  - {nb}")

    if uncovered:
        has_errors = True
        print("ERROR: These notebooks are not mapped in the workflow manifest:")
        for nb in uncovered:
            print(f"  - {nb}")

    if not has_errors:
        print(f"Coverage OK: mapped {len(workflow_files)} notebooks.")
        return 0
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LSWF cohesive workflow tracker")
    parser.add_argument("command", choices=["list", "init", "set", "next", "validate"])
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--step-id", default="")
    parser.add_argument("--status", choices=["pending", "in_progress", "completed"], default="pending")
    parser.add_argument("--note", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)

    if args.command == "validate":
        return validate_manifest_coverage(manifest, REPO_ROOT)

    if args.command == "init":
        args.state.parent.mkdir(parents=True, exist_ok=True)
        state = init_state(manifest)
        save_state(state, args.state)
        print(f"Initialized state file at {args.state}")
        return 0

    state = load_or_init_state(manifest, args.state)

    if args.command == "list":
        list_workflow(manifest, state)
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
