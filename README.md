# gh-actions — composable workflows for GitHub Actions

Six reusable workflows. **`release.yml`** wraps release-please and adds
the Release body/metadata it can't produce. **`build.yml`** is the CI
layer for projects that ship binaries. **`ci.yml`** is generic project
CI. **`npm-publish.yml`** is OIDC trusted publishing. **`pr-title.yml`**
gates conventional-commits PR titles. **`version.yml`** self-versions
this repo. Use one, some, or all — every workflow is independent.

```
            ┌────────────────────────────────────────────────────┐
            │  JoShMiQueL/gh-actions                             │
            │                                                    │
            │  ci.yml        ──► install → verify → test×matrix  │
            │  pr-title.yml  ──► conventional-commits PR gate    │
            │  release.yml   ──► release-please + Release body   │
            │                    (title, notes, Contributors)    │
            │  npm-publish   ──► verify-tag → test → OIDC npm    │
            │  build.yml     ──► toolchain → build → package     │
            │                    → attach → post-publish         │
            │  version.yml   ──► self-versioning (this repo)     │
            └────────────────────────────────────────────────────┘
```

## The model

| Artifact | Content | Owner |
|---|---|---|
| `CHANGELOG.md` | **Changes only** — `### Features` / `### Bug Fixes` | release-please |
| Release body (GitHub page) | **Everything** — changelog + `release-notes` + `### Contributors` | release-please + `release.yml` |
| Release assets | Binaries, archives, checksums | `build.yml` |

## How a release flows

```
push to main (conventional commits) ──► release-please opens/updates
                                        the Release PR
merge the PR when ready ──────────────► rp creates tag + Release
tag push fires both jobs in parallel ─► release job: body (notes + Contributors)
                                        build job(s): compile → attach assets
```

One caller file per project. The dev only chooses **how many jobs** and
**which inputs**.

## Quick start — minimal (library, docs, config repo)

`.github/workflows/release.yml` in your project:

```yaml
name: Release
on:
  push:
    branches: [main]
    tags: ["v*.*.*"]
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
```

That's it — Release PR maintenance, `### Contributors`, done.

## Quick start — app with binaries

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
      token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
    with:
      version: ${{ inputs.version }}
      toolchain: go
      build-command: go build -o myapp .
      artifacts: myapp
      checksums: sha256
```

Both jobs fire on the same tag push **in parallel** — `release` edits the
body, `build` uploads assets. Whichever lands first creates the Release if
missing. Keep `release-title` identical in both in case `build` wins the
create race.

---

# `release.yml` — inputs

| Input | Default | What it does |
|---|---|---|
| `version` | `""` | Manual-dispatch version → releases it directly, skips release-please entirely. Ignored on tag/branch push. |
| `tag-prefix` | `"v"` | Prefix stripped from the tag to get the version: `v0.1.4`→`0.1.4`, `pkg-v0.1.4`→`0.1.4` (`tag-prefix: "pkg-v"`), `0.1.4`→`0.1.4` (`""`). |
| `runner` | `ubuntu-24.04` | OS for the metadata job — nothing compiles here. |
| `release-title` | `""` | Title template — `{version}` and `{tag}` expand. Empty keeps rp's title (or `v{version}` on manual creates). |
| `release-notes` | `""` | Markdown appended to the body — after the changelog, before Contributors. |
| `contributors` | `true` | Append `### Contributors` — authors of `prev_tag..tag`, first-timers flagged `*(new contributor)*`. |
| `prerelease` | `false` | Mark pre-release. **Auto**: any `-` in the version (`v0.2.0-beta`, `-rc.1`) is always pre-release. |
| `draft` | `false` | Create/update the Release as a draft. |
| `release-please` | `true` | Run the embedded release-please job on branch pushes. `false` if you drive rp from your own workflow. |
| `rp-config-file` | `release-please-config.json` | release-please config path. |
| `rp-manifest-file` | `.release-please-manifest.json` | release-please manifest path. |

## `release.yml` — secrets

| Secret | Needed for |
|---|---|
| `token` | PAT — release-please pushes tags + `gh release edit`. **A bot-pushed tag only re-triggers workflows if a PAT pushed it** (`GITHUB_TOKEN` doesn't cascade). Falls back to `github.token` — enough when tags come from manual `git tag`. |

---

# `build.yml` — inputs

## trigger / resolve

| Input | Default | What it does |
|---|---|---|
| `version` | `""` | Manual-dispatch version → tag = `tag-prefix`+version. Ignored on tag push. |
| `tag-prefix` | `"v"` | Same resolution as release.yml. |
| `runner` | `windows-2022` | Runner OS label — any GitHub or self-hosted label. Set per-leg when matrixing. |
| `shell` | `bash` | Shell for **hook** commands only (`setup`/`build`/`post-publish`) — `bash`/`pwsh`/`sh`/`cmd`. Internal steps always use bash (Git Bash on Windows). Use `pwsh` when hooks need PowerShell (`$env:VERSION`). |
| `working-directory` | `""` | `cd` here after checkout — monorepo support. Stamp, hooks, build and artifact patterns all resolve relative to it. |

## toolchain

| Input | Default | What it does |
|---|---|---|
| `toolchain` | `custom` | Space-separated `name[@version]` tokens → their setup action: `rust`(@stable + cargo cache) `node`(@lts/\*) `go`(@stable) `dotnet`(@8.x) `python`(@3.x) `bun`(@latest). E.g. `"rust@1.75 node@24"`. `custom` = provision nothing — exotic stacks (MSVC, zig, java…) via `setup-command` or a `uses:` step of your own before this job. |
| `node_workdir` | `""` | Dir with `package.json` → `npm ci` (or `npm install` w/o lockfile) + `npm run build` run here, and its package.json gets version-stamped. Implies the node toolchain. Empty = no frontend step. |

## version stamp

| Input | Default | What it does |
|---|---|---|
| `version-bump` | `auto` | `auto`: stamp `$VERSION` into the toolchain's canonical manifest — root `Cargo.toml` (skipped when `[workspace]` root), `package.json` (root + node_workdir), `pyproject.toml`. First semver found is replaced. `none`: stamp it yourself in `setup-command`. |
| `version-files` | `""` | Extra files to stamp, one path per line — nested `Cargo.toml`, `tauri.conf.json`, `*.csproj`… Same first-semver rule. |

## build

| Input | Default | What it does |
|---|---|---|
| `target` | `""` | Build target name/triple (`x86_64-pc-windows-msvc`, `linux/arm64`…) — exported as `$TARGET` to hooks and usable as `{target}` in name templates. Doesn't cross-compile by itself; your `build-command` uses it (`cargo build --target $TARGET`). |
| `setup-command` | `""` | Runs after stamp, before build — codegen, deps, patches. Sees `$VERSION`/`$TAG`/`$TARGET`. |
| `build-command` | `""` | The release build. Omit for frontend-only (node_workdir does the work). |

## package

| Input | Default | What it does |
|---|---|---|
| `artifacts` | `""` | Files/globs to attach, one per line. Resolved inside the workspace — `../` or absolute paths are refused (security). Empty = attach nothing. |
| `artifact-name` | `""` | Rename template per artifact — `{name}`(repo) `{version}` `{tag}` `{target}` `{basename}` `{stem}` `{ext}` expand. Use `{target}`/`{stem}` so matrix legs or multiple files don't collide — collisions fail loudly. |
| `archive` | `none` | Pack all artifacts (+`include` files) into ONE archive: `none`/`zip`/`tar.gz`/`auto` (auto = zip on Windows, tar.gz elsewhere). |
| `archive-name` | `{name}-{version}-{target}` | Archive name template — `{name}` `{version}` `{tag}` `{target}` expand; extension appended by `archive`. → `myapp-1.2.0-x86_64-pc-windows-msvc.zip` |
| `include` | `""` | Extra files packed into the archive, one per line — `LICENSE`, `README.md`. Missing files warn, don't fail. |
| `checksums` | `none` | Per-asset checksum file — `sha256`/`sha512`/`"sha256 sha512"`. Produces `<asset>.sha256` next to each upload. |
| `fail-on-unmatched-artifacts` | `true` | `true`: a pattern matching nothing fails the run (silence = broken build). `false`: warn and continue (optional outputs). |

## release metadata (used if *this* job creates the Release)

| Input | Default | What it does |
|---|---|---|
| `release-title` | `""` | Same template rules — keep consistent with the release.yml job. |
| `prerelease` | `false` | Auto on `-` in version. |
| `draft` | `false` | Create as draft. |
| `make-latest` | `auto` | `auto` = GitHub decides · `true` = force latest (skipped on pre/draft) · `false` = explicitly un-latest (maintenance releases on old branches). |
| `discussion-category` | `""` | Existing Discussions category — GitHub opens a linked Discussion on create. |

## hooks

| Input | Default | What it does |
|---|---|---|
| `post-publish-command` | `""` | Runs after attach — self-update pointers, store publishes, notifications. Sees `$VERSION`/`$TAG`/`$TARGET`/`$ASSETS_DIR`/`$ASSETS` + env-json vars. |

## `build.yml` — secrets

| Secret | Needed for |
|---|---|
| `token` | PAT or `github.token` for `gh release create/upload/edit`. |
| `env-json` | One JSON object → each value `::add-mask::`ed then injected into `GITHUB_ENV` for every later step. Multiline values supported. **`env` is a reserved secret name — hence `env-json`.** This is how hooks get credentials: `with:` can't carry secrets and a called workflow can't iterate unknown secret names. Malformed JSON fails with a clear error. |

---

# Hooks — environment contract

All hook commands (`setup`/`build`/`post-publish`) see, exported to `GITHUB_ENV`:

| Var | Value |
|---|---|
| `$VERSION` | Resolved version (`0.1.4`) — `$env:VERSION` in pwsh |
| `$TAG` | Resolved tag (`v0.1.4`) |
| `$TARGET` | The `target` input (`""` if unset) |
| `$ASSETS_DIR` | Staging dir with final packaged files (post-publish) |
| `$ASSETS` | Newline list of filenames in `$ASSETS_DIR` |
| *env-json keys* | Whatever the project's JSON carried |

**Gotcha**: `with:` inputs evaluate **before** the workflow runs —
`${{ env.VERSION }}` does NOT exist there. Use the shell variable **inside**
the hook body: `$VERSION` (bash) / `$env:VERSION` (pwsh). The hook body
travels as an env var, so `$` reaches the hook's shell unexpanded and is
evaluated there — correct by design.

# Name templates

Used by `release-title`, `artifact-name`, `archive-name`:

| Placeholder | Expands to | Example |
|---|---|---|
| `{name}` | repo name | `myapp` |
| `{version}` | resolved version | `1.2.0` |
| `{tag}` | resolved tag | `v1.2.0` |
| `{target}` | `target` input | `x86_64-pc-windows-msvc` |
| `{basename}` | artifact filename (artifact-name only) | `app.exe` |
| `{stem}` | filename without extension (artifact-name only) | `app` |
| `{ext}` | extension (artifact-name only) | `exe` |

---

# Patterns — pick your path

## 1 · Library / docs / config — no binaries

```
caller: 1 job → release.yml
push main → Release PR → merge → tag → Release(changelog + Contributors)
```

## 2 · Single-platform app

```
caller: release job + build job
merge → tag → ∥ release edits body
              build compiles → myapp + myapp.sha256 attached
```

## 3 · Multi-platform (the full one)

```yaml
build:
  strategy:
    fail-fast: false
    matrix:
      include:
        - { os: ubuntu-24.04,  target: x86_64-unknown-linux-gnu }
        - { os: windows-2022, target: x86_64-pc-windows-msvc   }
        - { os: macos-15,   target: x86_64-apple-darwin      }
  uses: JoShMiQueL/gh-actions/.github/workflows/build.yml@main
  with:
    runner: ${{ matrix.os }}
    target: ${{ matrix.target }}
    toolchain: rust
    build-command: cargo build --release --target $TARGET
    artifacts: target/$TARGET/release/myapp*
    archive: auto
    archive-name: "myapp-{version}-{target}"
    include: |
      LICENSE
      README.md
    checksums: sha256
```

→ `myapp-1.2.0-x86_64-pc-windows-msvc.zip`(+sha256), `…-linux-gnu.tar.gz`(+sha256), `…-apple-darwin.tar.gz`(+sha256) — taiki-e/goreleaser style.

## 4 · Frontend-only

```yaml
with:
  node_workdir: web        # npm ci + build + package.json stamp
  artifacts: web/dist/*
```

## 5 · Monorepo

```yaml
with:
  working-directory: crates/my-cli
  toolchain: rust
  build-command: cargo build --release
  artifacts: ../../target/release/my-cli
```

## 6 · Publish outside GitHub (stores, pointers, signing)

```yaml
secrets:
  env-json: ${{ secrets.MY_RELEASE_ENV }}   # {"KEY":"val",...}
with:
  post-publish-command: ./cli publish --version $VERSION
```

## 7 · No release-please — manual releases only

```yaml
on:
  workflow_dispatch:
    inputs: { version: { required: true, type: string } }
jobs:
  build:
    uses: JoShMiQueL/gh-actions/.github/workflows/build.yml@main
    with: { version: ${{ inputs.version }}, toolchain: go, ... }
```

# `ci.yml` — generic project CI

Install → verify (typecheck/build/lint) once → test fanned out over an OS
matrix. Package-manager agnostic — the same workflow covers bun, npm,
pnpm, Python, Cargo…

```yaml
on:
  push: { branches: [main] }
  pull_request:
jobs:
  ci:
    uses: JoShMiQueL/gh-actions/.github/workflows/ci.yml@v1
```

## `ci.yml` — inputs

| Input | Default | What it does |
|---|---|---|
| `node-version` | `""` | `setup-node` version — `"24"`, `"lts/*"`. Empty skips Node. |
| `bun-version` | `""` | `setup-bun` version — `"1.4.0"`. Empty skips Bun. |
| `working-directory` | `""` | `cd` here before commands — monorepo support. |
| `setup-command` | `""` | Free-form step **before** install — apt deps, codegen, `pip install`. |
| `install-command` | `bun install --frozen-lockfile` | Dependency install — `npm ci`, `pnpm i --frozen-lockfile`, `pip install -e .`. Empty skips. |
| `verify-commands` | `typecheck` + `build` | Newline-separated checks on the **first** OS only. Empty skips the verify job. |
| `test-command` | `bun test` | Run on every OS in the matrix. Empty skips the test job. |
| `os-matrix` | `ubuntu-24.04,windows-2022,macos-15` | JSON array of runner labels the test fans out over. |
| `fail-fast` | `true` | Cancel remaining legs on the first failure. |

## `ci.yml` — secrets

| Secret | Needed for |
|---|---|
| `token` | GitHub API access inside a test — usually unused. |
| `env-json` | JSON object → env vars in every step — passes any secret set without this workflow knowing names. |

---

# `npm-publish.yml` — OIDC trusted publishing

`verify-tag → test → npm publish --provenance`, idempotent — re-running
a tag or cutting a Release over an already-published version is a no-op,
not an E409. No npm token in the repo: the package links to this repo +
workflow via npm's *Trusted Publisher* setting.

```yaml
on:
  push: { tags: ["v*"] }
  release: { types: [published] }
  workflow_dispatch:
jobs:
  publish:
    uses: JoShMiQueL/gh-actions/.github/workflows/npm-publish.yml@v1
    permissions:
      id-token: write   # OIDC — required
      contents: read
```

## `npm-publish.yml` — inputs

| Input | Default | What it does |
|---|---|---|
| `node-version` | `lts/*` | Node for publish — npm publish always runs on Node. |
| `bun-version` | `""` | Bun for install/test when they use it. |
| `working-directory` | `""` | Subdirectory with `package.json` — monorepo support. |
| `install-command` | `bun install --frozen-lockfile` | Dependency install. |
| `verify-commands` | `typecheck` + `build` | Pre-publish checks, newline-separated. |
| `test-command` | `bun test` | Gated before publish. Empty skips the test job. |
| `os-matrix` | `ubuntu-24.04,windows-2022,macos-15` | Fan-out — publish needs **all** green. |
| `fail-fast` | `true` | Matrix cancellation. |
| `registry-url` | `https://registry.npmjs.org` | Override for GitHub Packages / private registries. |
| `access` | `public` | `public` or `restricted`. |
| `provenance` | `true` | `--provenance` flag — OIDC-signed provenance statement. |
| `dry-run` | `false` | `--dry-run` — validates the tarball without publishing. |

## `npm-publish.yml` — secrets

| Secret | Needed for |
|---|---|
| `env-json` | Registry auth for a private mirror, extra env for tests. |

---

# `pr-title.yml` — conventional-commits PR gate

Squash merges put the PR title on main — for release-please to classify
the change (`feat:` → minor, `fix:` → patch), the title must be
conventional. Gates `opened`/`edited`/`synchronize`/`ready_for_review`.

```yaml
on:
  pull_request:
    types: [opened, edited, synchronize, reopened, ready_for_review]
jobs:
  pr-title:
    uses: JoShMiQueL/gh-actions/.github/workflows/pr-title.yml@v1
```

## `pr-title.yml` — inputs

| Input | Default | What it does |
|---|---|---|
| `types` | full conventional set | Allowed type prefixes. |
| `require-scope` | `false` | Force `feat(api):` not just `feat:`. |
| `subject-pattern` | no leading capital | Regex the subject must match. |
| `subject-pattern-error` | — | Message shown on mismatch. |

---

# Versioning

| Ref | Use when |
|---|---|
| `@v1` (floating major) | **Production callers** — stable, gets non-breaking fixes |
| `@main` | Development of these workflows — every push changes behavior for all callers |

The repo self-versions with its own `release.yml` — merge the Release PR
and the tag `v1.x.y` is created, then `v1` is moved to it.

# Gotchas learned the hard way

- **`secrets:` must use block style** — flow `{ }` can't contain `${{ }}`.
- **Caller needs `pull-requests: write`** or rp dies with cryptic `startup_failure`.
- **`${{ env.* }}` doesn't exist inside `with:` inputs** — hooks use `$VAR`.
- **`gh release upload` mangles paths on Windows** — we always upload basenames from inside the file's dir.
- **Artifacts must resolve inside the workspace** — `../x` and absolute paths are refused.
- **Tag re-trigger needs a PAT** — `GITHUB_TOKEN`-pushed tags don't fire workflows.
