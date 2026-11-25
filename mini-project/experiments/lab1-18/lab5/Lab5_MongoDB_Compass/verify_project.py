"""Verify scripts and JSON locally, without a running MongoDB server."""
from pathlib import Path
import ast
import json

ROOT=Path(__file__).resolve().parent
py_files=list(ROOT.rglob("*.py"))
json_files=list(ROOT.rglob("*.json"))
for path in py_files:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
for path in json_files:
    json.loads(path.read_text(encoding="utf-8"))
assert len(json_files)==4, "Expected four activity JSON datasets"
assert len([p for p in py_files if p.name.startswith(('lab_5_', 'activity_5_'))])==4
print(f"PASS: {len(py_files)} Python files; {len(json_files)} JSON files; four activity scripts")
