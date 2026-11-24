# AGENTS.md — guía para agentes trabajando en este repo

Cinco workflows reusables en `.github/workflows/`:

| Fichero | Rol |
|---|---|
| `release.yml` | release-please aumentado — Release PR, title, notes, `### Contributors`, flags. **Sin compilar.** |
| `build.yml` | capa CI opt-in — toolchain → stamp → build → package (rename/archive/checksums) → attach → post-publish |
| `ci.yml` | CI genérico — install → verify (1 OS) → test (matriz OS). Agnóstico de package manager via inputs. |
| `npm-publish.yml` | verify-tag → test → OIDC `npm publish --provenance`, idempotente (skip si ya publicado). |
| `pr-title.yml` | gate de Conventional Commits en el título del PR — squash-merge safe. |
| `version.yml` | auto-versionado de ESTE repo — llama a `./release.yml` y mueve el major flotante `v1` |

Los proyectos llaman con `uses: JoShMiQueL/gh-actions/.github/workflows/<f>.yml@<ref>`.

## Reglas duras antes de tocar nada

- **`uses:` dentro de un caller es a NIVEL DE JOB, no step.** `jobs.x.uses:` llama al workflow entero; `steps[].uses:` llama actions. No mezclar.
- **`secrets:` y `with:` van en block style** — el flow `{ }` no admite `${{ }}`.
- **Todo caller necesita `pull-requests: write`** en `permissions:` — release.yml lo declara globalmente (rp abre la Release PR) y sin él da `startup_failure` críptico.
- **`${{ env.* }}` NO existe dentro de `with:`** — los inputs se evalúan antes de correr. Los hooks usan `$VERSION`/`$TAG`/`$TARGET`/`$ASSETS_DIR` como vars de shell.
- **`shell:` de un step no admite expresiones** — los hooks se enrutan: bash → `eval`, pwsh → `pwsh -NoProfile -Command "$HOOK"`.
- **Artifacts se suben por basename** desde dentro de su dir — `gh release upload` rompe paths en Windows.
- **Todo `run:` de bash termina en `exit 0` o `|| true`** — un `[ -n "$x" ] && echo` final devuelve 1 en inputs vacíos.
- **`env` es nombre reservado de secret** — por eso `env-json`.
- **`fromJSON` para matrices por input** — un `os-matrix` string JSON en `workflow_call` se expande con `strategy.matrix.os: ${{ fromJSON(inputs.os-matrix) }}`. `verify` corre solo en `[0]` (no necesita el fan-out).
- **El test de `npm-publish` gatea el publish** — `needs: [verify-tag, test]` con `if: always() && !contains(needs.*.result, 'failure')` — publish corre solo si TODO el matriz pasó, incluso cuando `test` no corre (skipped ≠ failed).
- **`--provenance` es opt-out, no opt-in** — OIDC trusted publishing es el default; el flag se pasa a menos que el registry no lo soporte (`provenance: false`).

## Convenciones del código

- Internals siempre `shell: bash` (Git Bash corre en Windows/mac/Linux).
- Secrets: `secrets.token` (PAT) y `secrets.env-json` (JSON → env vars enmascaradas). `with:` no puede llevar secrets.
- Nombres de steps: `Setup X`, `Parse toolchain`, `Stamp version`, `Package artifacts`, `Attach artifacts to GitHub Release`, `Append …`, `Post-publish`.
- Comentarios en los `run:` explican el PORQUÉ, no el qué (los edge cases GitHub son todos non-obvious).

## Versionado del repo (self-dogfooding)

`version.yml` se versiona a sí mismo con `release.yml`:
- push a main → rp abre Release PR (solo `feat:`/`fix:`/`perf:`/`revert:` bump — `chore`/`docs`/`ci` ignorados)
- merge → tag `v1.x.y` → `major-tag` mueve el flotante `v1`
- **El major-tag necesita un fine-grained PAT con `workflows` permission** en `RELEASE_PLEASE_TOKEN` — `GITHUB_TOKEN` y `gho_` OAuth están hard-bloquedos cuando el commit toca `.github/workflows/`. Sin ese PAT el step degrada a `::warning::` (no rompe el run) y el major se mueve a mano:
  `gh api repos/JoShMiQueL/gh-actions/git/refs/tags/v1 --method PATCH -f sha=$(gh api repos/JoShMiQueL/gh-actions/git/ref/tags/vX.Y.Z --jq .object.sha) -F force=true`

## Tests

No hay suite — se valida contra repos `audit-{go,multi,python,custom,edge}` en GitHub (privados, de usar y tirar). Cada cambio grande: caller de un audit repo → `workflow_dispatch` → verificar la Release resultante. No pushear tests a `main` de un proyecto real.

## Errores conocidos / trampas

- `release-please-action@v5+` (Node 24) — v4 está deprecated.
- Runners: **pinear imagen** (`ubuntu-24.04`, `windows-2022`, `macos-15`) — `-latest` migra debajo y genera warnings.
- `\u0000` en un `run:` rompe el YAML (escrito como byte NUL literal) — parsear env-json con `jq -c` per-entry.
- `tar -acf x.zip` en Git Bash (GNU tar) crea tar-con-nombre-zip corrupto — zip real: bsdtar, `zip` binary o `pwsh Compress-Archive` (cadena en `Package artifacts`).
- `grep -qF "$VAR"` con `$VAR` multilínea matchea líneas vacías → usa la primera línea no-vacía como marcador.
