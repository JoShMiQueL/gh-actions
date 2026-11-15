# gh-actions — one reusable release pipeline

A single reusable workflow, `release.yml`, that runs the whole "tag → release"
pipeline for any project. release-please is used **directly** (it's the
official action — no wrapper needed); this toolkit adds what release-please
doesn't: build + attach binaries + a Contributors section in the Release body.

## The model (clap / industry standard)

| Artifact | Content |
|---|---|
| **`CHANGELOG.md`** (repo file) | **Changes only** — `### Features`/`### Bug Fixes`. Owned by release-please. |
| **Release body** (the GitHub page) | **Everything** — the changelog + `### Contributors` (authors of the range, `(new contributor)` for first-timers). Added by this pipeline. |

## What a project needs (2 files, ~40 lines total)

**1. `release-please.yml`** — official action, direct:

```yaml
on: { push: { branches: [main] } }
permissions: { contents: write, pull-requests: write }
jobs:
  rp:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
          token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
```

**2. `release.yml`** — thin caller, all project-specific bits as inputs:

```yaml
on:
  push: { tags: ["v*.*.*"] }
  workflow_dispatch:
    inputs: { version: { required: true } }
permissions: { contents: write }
jobs:
  release:
    uses: JoShMiQueL/gh-actions/.github/workflows/release.yml@main
    secrets:
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
      env:   ${{ secrets.PROJECT_RELEASE_ENV }}   # JSON {"KEY":"val",...}
    with:
      version: ${{ inputs.version }}
      language: rust
      node_workdir: launcher/ui
      setup-command: |
        (Get-Content launcher/src-tauri/Cargo.toml -Raw) -replace '(?m)^version\s*=\s*"[^"]*"', "version = `"${{ env.VERSION }}`"" | Set-Content launcher/src-tauri/Cargo.toml -NoNewline
      build-command: cargo build --release -p s1l -p s1l-launcher
      artifacts: target/release/s1l-launcher.exe
      post-publish-command: ./target/release/s1l.exe pack launcher ...
```

## Inputs (all documented in `release.yml`'s header comment)

| Input | Default | What it controls |
|---|---|---|
| `version` | — | manual-dispatch version (ignored on tag push) |
| `tag-prefix` | `"v"` | strip this from the tag → version (`""`, `"pkg-v"`, …) |
| `runner` | `windows-latest` | OS for the build |
| `language` | `custom` | `rust` (toolchain+cache) \| `node` \| `go` \| `custom` |
| `node_version` | `24` | node for the frontend step |
| `node_workdir` | `""` | dir with `package-lock.json` → `npm ci`+`npm run build`; empty skips it |
| `setup-command` | `""` | pwsh pre-build (version stamp, codegen) — `$env:VERSION`/`$env:TAG` set |
| `build-command` | — | **required** — the release build |
| `artifacts` | — | **required** — paths/globs attached to the Release |
| `contributors` | `true` | append the Contributors section to the body |
| `post-publish-command` | `""` | pwsh after attach (self-update pointer, notify) |

## Secrets

| Secret | Needed for |
|---|---|
| `token` | `gh release edit` (contributors) — a PAT; falls back to `github.token` |
| `env` | One JSON object = the project's whole env, injected into every step (`{"KEY":"val",...}`) — keeps secrets out of the YAML |

## Why not more pieces?

release-please is already a maintained action — a wrapper would add nothing.
Contributors isn't worth a separate action — it's a step inside `release.yml`
(the only place it's ever wanted). So: **one reusable workflow**, used
everywhere, with every knob documented in its header.
