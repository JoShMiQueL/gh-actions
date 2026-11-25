"""Validate the reusable workflows in .github/workflows/.

Checks (run on every push/PR — see validate.yml):
  1. every workflow parses as YAML
  2. every `inputs.X` / `secrets.X` referenced in an expression is declared
     under on.workflow_call.inputs / .secrets — a typo'd name is a runtime
     error in every caller, so it's cheaper to catch it here
  3. no `secrets.` inside an `if:` — that fails at parse time in reusable
     workflows and produces a run with zero jobs and no useful error

Exits non-zero on any failure.
"""
import re
import sys
from pathlib import Path

import yaml

WF = Path(__file__).resolve().parent.parent / "workflows"
failed = False

for path in sorted(WF.glob("*.yml")):
    name = path.name
    body = path.read_text(encoding="utf-8")
    print(f"── {name}")

    # 1 · parses
    try:
        doc = yaml.safe_load(body)
    except yaml.YAMLError as e:
        print(f"   ✗ YAML parse error: {e}")
        failed = True
        continue

    # yaml parses a bare `on:` as the boolean True — normalize the key.
    on = doc.get("on", doc.get(True, {})) or {}
    call = on.get("workflow_call") or {}
    declared_inputs = set((call.get("inputs") or {}).keys())
    declared_secrets = set((call.get("secrets") or {}).keys())

    # Strip comments before scanning — a `secrets.X` inside a `#` doc line
    # (e.g. the caller-example header) isn't a real reference.
    uncommented = "\n".join(
        line.split("#", 1)[0] if "#" in line else line
        for line in body.splitlines()
    )
    used_inputs = set(re.findall(r"inputs\.([A-Za-z0-9_-]+)", uncommented))
    used_secrets = set(re.findall(r"secrets\.([A-Za-z0-9_-]+)", uncommented))
    # github.token / GITHUB_TOKEN aren't caller secrets — they're ambient.
    used_secrets -= {"GITHUB_TOKEN", "token"}

    # Only a `workflow_call` reusable needs its inputs/secrets declared.
    # A caller file (workflow_dispatch / push / release triggers) legitimately
    # uses `inputs.*` for dispatch inputs and `secrets.*` for repo secrets —
    # those live outside workflow_call and must NOT be flagged. Check `on`
    # only — the string "workflow_call" also appears in header comments.
    is_reusable = isinstance(on, dict) and "workflow_call" in on
    if is_reusable:
        ok = True
        for m in sorted(used_inputs - declared_inputs):
            print(f"   ✗ inputs.{m} used but not declared"); ok = False
        for m in sorted(used_secrets - declared_secrets):
            print(f"   ✗ secrets.{m} used but not declared"); ok = False
        if ok:
            print(f"   ✓ parses, {len(used_inputs)} inputs + {len(used_secrets)} secrets consistent")
        failed = failed or not ok
    else:
        print(f"   ✓ parses (caller — inputs/secrets not checked)")

# 3 · secrets inside if:
for path in sorted(WF.glob("*.yml")):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.search(r"if:.*secrets\.", line):
            print(f"✗ {path.name}:{i} — secrets referenced in if: (parse-time failure)")
            failed = True

if failed:
    sys.exit("workflow validation failed")
print("all workflows valid")
