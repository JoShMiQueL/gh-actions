# release — release-please, augmented + an optional build layer

Two reusable workflows that compose. **`release.yml`** augments release-please
with the Release body/metadata it can't produce. **`build.yml`** is the
opt-in CI half for projects that compile binaries. Use one or both.

| Reusable | What it adds on top of release-please | When you call it |
|---|---|---|
| **`release.yml`** | Release title template, extra `release-notes`, **`### Contributors`** (authors of the range, `*(new contributor)*` badges), prerelease/draft flags | **Always** — it's the augmentation |
| **`build.yml`** | toolchain setup → version-stamp → build → attach artifacts → post-publish hook | Only when the project ships binaries |

## The model (clap / industry standard)

| Artifact | Content |
|---|---|
| **`CHANGELOG.md`** (repo file) | **Changes only** — `### Features`/`### Bug Fixes`. Owned by release-please. |
| **Release body** (the GitHub page) | **Everything** — the changelog + `release-notes` + `### Contributors`. |

## Minimal caller — a lib / docs / config repo (no binaries)

```yaml
name: Release
on:
  push:
    branches: [main]      # release-please accumulates conventional commits
    tags: ["v*.*.*"]      # augment the Release on tag
  workflow_dispatch:
    inputs: { version: { required: false, type: string } }
permissions:
  contents: write         # tag + Release edit
  pull-requests: write    # release-please opens the Release PR
jobs:
  release:
    uses: JoShMiQueL/gh-actions/.github/workflows/release.yml@main
    secrets:
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
    with:
      version: ${{ inputs.version }}
      release-title: "MyLib {version}"
```

That's it — Release PR maintenance, title, notes, Contributors. Zero build.

## App with binaries — add a `build` job in the same file

```yaml
jobs:
  release:                                    # rp augmentation — always
    uses: JoShMiQueL/gh-actions/.github/workflows/release.yml@main
    secrets:
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
    with:
      version: ${{ inputs.version }}
      release-title: "MyApp {version}"

  build:                                      # CI — only when binaries ship
    if: ${{ github.ref_type == 'tag' || inputs.version != '' }}
    uses: JoShMiQueL/gh-actions/.github/workflows/build.yml@main
    secrets:
      token:    ${{ secrets.RELEASE_PLEASE_TOKEN }}
      env-json: ${{ secrets.PROJECT_RELEASE_ENV }}   # optional JSON {"KEY":"val"}
    with:
      version: ${{ inputs.version }}
      toolchain: "rust node@24"
      shell: pwsh
      node_workdir: launcher/ui
      version-files: launcher/src-tauri/tauri.conf.json
      build-command: cargo build --release -p myapp
      artifacts: target/release/myapp.exe
      post-publish-command: ./target/release/cli.exe publish ... --version $env:VERSION
```

Both jobs fire on the same tag push and run **in parallel** — `release` edits
the Release *body* (notes/Contributors), `build` uploads *assets*. They don't
conflict; whichever lands first creates the Release if missing. **Keep
`release-title` identical in both** in case `build` wins the create race.

## `release.yml` inputs (rp augmentation)

| Input | Default | What it controls |
|---|---|---|
| `version` | `""` | manual-dispatch version — skips release-please, releases this directly |
| `tag-prefix` | `"v"` | strip this from the tag → version (`""`, `"pkg-v"`, …) |
| `runner` | `ubuntu-latest` | OS for the metadata job — no compilation happens here |
| `release-title` | `""` | title template — `{version}`/`{tag}` expand |
| `release-notes` | `""` | extra markdown appended to the body — after changelog, before Contributors |
| `contributors` | `true` | append the `### Contributors` section |
| `prerelease` | `false` | mark pre-release — **auto** on `-` in the version (`v0.2.0-beta`) |
| `draft` | `false` | create/update the Release as a draft |
| `release-please` | `true` | run the embedded release-please job on branch pushes |
| `rp-config-file` | `release-please-config.json` | release-please config path |
| `rp-manifest-file` | `.release-please-manifest.json` | release-please manifest path |

## `build.yml` inputs (CI layer)

| Input | Default | What it controls |
|---|---|---|
| `version`, `tag-prefix` | `""`, `"v"` | same resolution as release.yml |
| `runner` | `windows-latest` | OS for the build |
| `shell` | `bash` | shell for **hook** commands (`setup`/`build`/`post-publish`) — `bash`/`pwsh`/`sh`/`cmd`. Internals always use bash |
| `toolchain` | `custom` | `name[@version]` tokens → their setup action: `rust`(@stable) `node`(@lts/\*) `go`(@stable) `dotnet`(@8.x) `python`(@3.x) `bun`(@latest). `custom` = none — exotic stacks via `setup-command` or an earlier `uses:` |
| `node_workdir` | `""` | dir with `package.json` → `npm ci\|install`+`npm run build` + version-stamp; implies node toolchain |
| `version-bump` | `auto` | `auto`: stamp `$VERSION` into the toolchain's canonical manifest (root `Cargo.toml` skipped when `[workspace]`, `package.json`, `pyproject.toml`). `none`: stamp it yourself |
| `version-files` | `""` | extra files to stamp `$VERSION` into, one per line — first semver in each file is replaced |
| `setup-command` | `""` | after version-stamp, before build — codegen, deps, patches |
| `build-command` | `""` | the release build (omit for frontend-only via `node_workdir`) |
| `artifacts` | `""` | files/globs attached to the Release, one per line; missing fails loudly; empty = attach nothing |
| `release-title`, `prerelease`, `draft` | — | only used if *this* job creates the Release (lost the race to release.yml) |
| `post-publish-command` | `""` | after attach — self-update pointer, notify, publish to a store |

## Secrets

| Secret | `release.yml` | `build.yml` | Needed for |
|---|---|---|---|
| `token` | ✓ | ✓ | release-please pushes tags + `gh release` calls. A PAT — bot-pushed tags only re-trigger workflows when a PAT pushed them (GITHUB_TOKEN doesn't cascade). |
| `env-json` | — | ✓ | One JSON object = the project's env, injected into every step with each value `::add-mask::`ed first. `with:` inputs can't carry secrets — this is how hooks get credentials. **`env` is a reserved secret name — use `env-json`.** |

## Hooks (`setup-command` / `build-command` / `post-publish-command`)

- Run in `shell` (default `bash`); see `$VERSION`/`$TAG` (bash) or
  `$env:VERSION` (pwsh) plus every `env-json` var.
- **`with:` inputs evaluate BEFORE the reusable runs** — `${{ env.VERSION }}`
  does NOT exist there. Use the shell variable inside the hook body.

## Cross-OS

Internal steps are `shell: bash` — Git Bash ships on Windows runners, so the
same bash runs everywhere. `release.yml` defaults to `ubuntu-latest` (it only
edits Release metadata); `build.yml` defaults to `windows-latest`.
