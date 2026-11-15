# gh-actions — one reusable release pipeline

A single reusable workflow, `release.yml`, that runs the whole
"commits → Release PR → tag → build → publish" pipeline for any project.
release-please runs **inside** the reusable — one caller file does everything.

## The model (clap / industry standard)

| Artifact | Content |
|---|---|
| **`CHANGELOG.md`** (repo file) | **Changes only** — `### Features`/`### Bug Fixes`. Owned by release-please. |
| **Release body** (the GitHub page) | **Everything** — the changelog + `### Contributors` (authors of the range, `*(new contributor)*` for first-timers). |

## One file per project (~30 lines)

`.github/workflows/release.yml`:

```yaml
name: Release
on:
  push:
    branches: [main]      # release-please accumulates conventional commits
    tags: ["v*.*.*"]      # build+publish on tag
  workflow_dispatch:
    inputs: { version: { required: false, type: string } }   # manual release
permissions:
  contents: write         # tag + Release + upload
  pull-requests: write    # release-please opens the Release PR
jobs:
  release:
    uses: JoShMiQueL/gh-actions/.github/workflows/release.yml@main
    secrets:
      token:    ${{ secrets.RELEASE_PLEASE_TOKEN }}
      env-json: ${{ secrets.PROJECT_RELEASE_ENV }}   # optional JSON {"KEY":"val"}
    with:
      toolchain: "rust node@24"
      shell: pwsh
      node_workdir: launcher/ui
      version-files: launcher/src-tauri/tauri.conf.json
      build-command: cargo build --release -p s1l-launcher
      artifacts: target/release/s1l-launcher.exe
      post-publish-command: ./target/release/s1l.exe pack launcher ... --version $env:VERSION
```

Push to `main` → the embedded release-please job opens/updates the Release PR.
Merge it → tag + Release. Push/dispatch a tag → the release job builds + attaches.

## Inputs

| Input | Default | What it controls |
|---|---|---|
| `version` | `""` | manual-dispatch version — skips release-please, releases this directly |
| `tag-prefix` | `"v"` | strip this from the tag → version (`""`, `"pkg-v"`, …) |
| `runner` | `windows-latest` | OS for the build (`ubuntu-latest`, `macos-latest`, self-hosted label) |
| `shell` | `bash` | shell for **hook** commands (`setup`/`build`/`post-publish`) — `bash`/`pwsh`/`sh`/`cmd`. Internals always use bash (Git Bash on Windows). |
| `toolchain` | `custom` | `name[@version]` tokens → their setup action: `rust`(@stable) `node`(@lts/\*) `go`(@stable) `dotnet`(@8.x) `python`(@3.x) `bun`(@latest). `"rust@1.75 node@24 python@3.12"`. `custom` = none — exotic stacks (C++ MSVC, zig, java, flutter…) via `setup-command` or an earlier `uses:` in your workflow |
| `node_workdir` | `""` | dir with `package.json` → `npm ci\|install`+`npm run build` + version-stamp; implies node toolchain; empty skips it |
| `version-bump` | `auto` | `auto`: stamp `$VERSION` into the toolchain's canonical manifest — root `Cargo.toml` (rust, skipped when `[workspace]`), `package.json` (node/bun, root + node_workdir), `pyproject.toml` (python). `none`: stamp it yourself in `setup-command` |
| `version-files` | `""` | extra files to stamp `$VERSION` into, one per line — nested `Cargo.toml`, `tauri.conf.json`, `*.csproj`, … First semver in each file is replaced |
| `setup-command` | `""` | after version-stamp, before build — codegen, extra deps, patches |
| `build-command` | — | **required** — the release build |
| `artifacts` | — | **required** — files/globs attached to the Release, one per line; missing fails loudly |
| `release-title` | `""` | title template — `{version}`/`{tag}` expand (`"MyApp {version}"`) |
| `release-notes` | `""` | extra markdown appended to the body — after changelog, before Contributors |
| `contributors` | `true` | append the Contributors section to the body |
| `prerelease` | `false` | mark pre-release — **auto** on `-` in the version (`v0.2.0-beta`) |
| `draft` | `false` | create the Release as a draft |
| `post-publish-command` | `""` | after attach+contributors — self-update pointer, notify |
| `release-please` | `true` | run the embedded release-please job on branch pushes |
| `rp-config-file` | `release-please-config.json` | release-please config path |
| `rp-manifest-file` | `.release-please-manifest.json` | release-please manifest path |

## Secrets

| Secret | Needed for |
|---|---|
| `token` | release-please pushes tags + `gh release edit`. A PAT — bot-pushed tags only re-trigger the workflow when a PAT pushed them (GITHUB_TOKEN doesn't cascade). Falls back to `github.token` when tags come from manual `git tag`. |
| `env-json` | One JSON object = the project's env, injected into every step with each value `::add-mask::`ed first. **`env` is a reserved secret name — use `env-json`.** |

## Hooks (`setup-command` / `post-publish-command`)

- Run in `shell` (default `bash`); see `$VERSION`/`$TAG` (bash) or `$env:VERSION`
  (pwsh) — the resolve step exports them to `GITHUB_ENV`.
- **`with:` inputs evaluate BEFORE the reusable runs** — GitHub's
  `${{ env.VERSION }}` does NOT exist there. Use the shell variable inside the
  hook body, never `${{ env.* }}`.

## Cross-OS

Internal steps are `shell: bash` — Git Bash ships on Windows runners, so the
same bash runs on windows/ubuntu/macos. Choose `shell: pwsh` only when your
hook commands need PowerShell syntax.

## Why not more pieces?

release-please is a maintained action — it runs as a job inside the reusable,
not behind a wrapper. Contributors is a step inside the release job. So:
**one reusable workflow**, one caller file per project, every knob in `with:`.
