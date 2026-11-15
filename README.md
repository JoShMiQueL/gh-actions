# gh-actions — reusable release pipelines

Personal toolkit of reusable GitHub workflows + actions. Each project calls
them with a thin caller — no per-project pipeline rewriting.

## The model (clap / industry standard)

| Artifact | Content |
|---|---|
| **`CHANGELOG.md`** (repo file) | **Changes only** — `### Features`/`### Bug Fixes`, categorized. Owned by release-please. No contributors. |
| **Release body** (the GitHub page) | **Everything** — changelog + `### Contributors` (authors of the range, `(new contributor)` for first-timers). |

The CHANGELOG is the product's history; the Release is the social event —
contributors live in the body, never in the file.

## Pieces

| Path | Kind | What it does |
|---|---|---|
| `.github/workflows/release-please.yml` | reusable | wraps `release-please-action` → opens/maintains the Release PR (changelog = clean changes) |
| `.github/workflows/release-publish.yml` | reusable | tag → resolve version → stamp → build → attach binaries → **`### Contributors` appended to the Release body** → post-publish hook |
| `.github/actions/contributors/action.yml` | composite | standalone: appends the Contributors section to a Release body |

## Use in a project

**1. `release-please.yml`** — put `release-please-config.json` +
`.release-please-manifest.json` in the project root, then:

```yaml
on: { push: { branches: [main] } }
permissions: { contents: write, pull-requests: write }
jobs:
  rp:
    uses: JoShMiQueL/gh-actions/.github/workflows/release-please.yml@main
    secrets:
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
```

**2. `release-publish.yml`** — thin caller with the project's build recipe:

```yaml
on:
  push: { tags: ["v*.*.*"] }
  workflow_dispatch:
    inputs: { version: { required: true } }
permissions: { contents: write }
jobs:
  publish:
    uses: JoShMiQueL/gh-actions/.github/workflows/release-publish.yml@main
    secrets:
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
      env:   ${{ secrets.PROJECT_RELEASE_ENV }}   # JSON {"KEY":"val",...}
    with:
      version: ${{ inputs.version }}
      language: rust
      node_workdir: launcher/ui
      build-command: cargo build --release -p s1l -p s1l-launcher
      artifacts: target/release/s1l-launcher.exe
      post-publish-command: ./target/release/s1l.exe pack launcher ...
```

## The `env` secret

Per-project secrets as **one JSON object** — keeps the caller clean, one secret
to rotate:

```
PROJECT_RELEASE_ENV = {"S1L_PACK_SEED":"44f4…","S1L_R2_BUCKET":"s1l-store",...}
```

Loaded into every step via `Load project env`. Set it as a repo secret in each
project.

## Contributors logic

Commit authors of the release range (`prev_tag..this_tag`), deduped. An author
is flagged `*(new contributor)*` if they never committed before the previous
tag. Works on direct commits (no PRs needed) — reads `git log --format=%an`,
not GitHub's contributor graph (which only fills for PRs).
