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
      env-json:   ${{ secrets.PROJECT_RELEASE_ENV }}   # JSON {"KEY":"val",...}
                                                     # (bare `env` is a reserved secret name — use env-json)
    with:
      version: ${{ inputs.version }}
      toolchain: rust
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
| `runner` | `windows-latest` | OS for the build (`ubuntu-latest`, `macos-latest`, …) |
| `toolchain` | `custom` | space/comma-separated builtins → their setup action: `rust` (dtolnay+cache) `node` `go` `dotnet` `python` `bun` \| `custom` = none — exotic stacks (C++ MSVC, zig, java, flutter…) via `setup-command` or an earlier `uses:` in your workflow |
| `node_version` | `24` | node for the frontend step |
| `node_workdir` | `""` | dir with a `package.json` → `npm ci\|install`+`npm run build` (no lockfile = `npm install`); empty skips it |
| `setup-command` | `""` | pwsh pre-build (version stamp, codegen) — `$env:VERSION`/`$env:TAG` set |
| `build-command` | — | **required** — the release build |
| `artifacts` | — | **required** — paths/globs attached to the Release (one per line) — fails if any is missing |
| `contributors` | `true` | append the Contributors section to the body |
| `prerelease` | `false` | mark the Release pre-release — **auto** on `-` in the version (`v0.2.0-beta`, `-rc.1`) |
| `draft` | `false` | create the Release as a draft |
| `post-publish-command` | `""` | pwsh after attach (self-update pointer, notify) |

**Cross-OS**: every `run:` step is `shell: pwsh` — present on windows/ubuntu/macos
runners. Write hook commands in pwsh, not bash.

## Secrets

| Secret | Needed for |
|---|---|
| `token` | `gh release edit` (contributors) — a PAT; falls back to `github.token` |
| `env-json` | One JSON object = the project's whole env, injected into every step (`{"KEY":"val",...}`) — keeps secrets out of the YAML. **`env` is a reserved secret name — use `env-json`.** |

## Why not more pieces?

release-please is already a maintained action — a wrapper would add nothing.
Contributors isn't worth a separate action — it's a step inside `release.yml`
(the only place it's ever wanted). So: **one reusable workflow**, used
everywhere, with every knob documented in its header.
