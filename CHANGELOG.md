# Changelog

## [1.1.2](https://github.com/JoShMiQueL/gh-actions/compare/v1.1.1...v1.1.2) (2026-11-15)


### Bug Fixes

* **version.yml:** validate workflows-permission PAT — end-to-end floating major test ([2f3f085](https://github.com/JoShMiQueL/gh-actions/commit/2f3f0854f0884c855d3deef49f2a5752465a76cd))

## [1.1.1](https://github.com/JoShMiQueL/gh-actions/compare/v1.1.0...v1.1.1) (2026-11-15)


### Bug Fixes

* **version.yml:** bot-pushed tags never re-trigger — move floating major inside the same run (after rp), idempotent: newest version tag → major ([e0899e3](https://github.com/JoShMiQueL/gh-actions/commit/e0899e3caa42f36150aa7c5245edb74ea9087a14))
* **version.yml:** degrade major-tag to warning when token lacks workflows perm — needs a fine-grained PAT with 'workflows', GITHUB_TOKEN/gho_ are hard-blocked by GitHub ([b0bcb85](https://github.com/JoShMiQueL/gh-actions/commit/b0bcb856cf7658e920e5fd068b7bc7ddaa86d171))
* **version.yml:** git push needs PAT in remote URL — GITHUB_TOKEN auth header covers API not git writes (exit 128 on tag push) ([0df2f3f](https://github.com/JoShMiQueL/gh-actions/commit/0df2f3f0b5eeb898e9708b91c39da346a5837c0b))
* **version.yml:** git push rejected by workflows-permission check — update the floating major ref via REST git-refs API instead (no smart-HTTP validation) ([0dae06b](https://github.com/JoShMiQueL/gh-actions/commit/0dae06b99c3dff1181241ca470fd5478f7c23317))
* **version.yml:** git tag -fa -m needs user identity (empty ident exit 128) ([84f2188](https://github.com/JoShMiQueL/gh-actions/commit/84f21881835332c96f415a336b6bbf68fc417c33))
* **version.yml:** GITHUB_TOKEN not the PAT for git/refs — gho_ OAuth gets 'not accessible by integration', the job token is the integration identity ([4a5dd11](https://github.com/JoShMiQueL/gh-actions/commit/4a5dd112e12bd7f6ac826e1326036840bd32e024))
* **version.yml:** use GITHUB_TOKEN (checkout persisted) — it can push tags on existing commits; OAuth tokens get 'workflows permission' rejected when the referenced commit touches .github/workflows ([83f8533](https://github.com/JoShMiQueL/gh-actions/commit/83f85336eef8b466c8ace546bd73568a775a9d8f))

## [1.1.0](https://github.com/JoShMiQueL/gh-actions/compare/v1.0.0...v1.1.0) (2026-11-15)


### Features

* self-versioning live — PAT configured, validating tag re-trigger + floating major ([73ed9be](https://github.com/JoShMiQueL/gh-actions/commit/73ed9bebc6a9245ea5e2051a9d0f18f11022fcd7))

## 1.0.0 (2026-11-15)


### Features

* **build.yml:** packaging layer — artifact-name templates ({name}/{version}/{tag}/{target}/{stem}/{ext}), archive zip|tar.gz|auto, include files, per-asset checksums, fail-on-unmatched-artifacts, make-latest, discussion-category, working-directory (monorepo), target input exported as $TARGET; assets staged to RUNNER_TEMP so upload only sees basenames (collision-safe renames flagged) ([670bccb](https://github.com/JoShMiQueL/gh-actions/commit/670bccb30d1747316ce98b72ed0bc63356a3ac84))
* embedded release-please job + toolchain@version + version-bump + bash internals + release-title/notes ([2ba44c1](https://github.com/JoShMiQueL/gh-actions/commit/2ba44c12e3e9f8cf3397d1382f52da5d63edd08e))
* notes-only tier — build-command/artifacts now optional; HAS_BUILD env gates toolchain/stamp/setup/build; 'Release plan' step logs the tier + warns on ignored inputs; attach still runs (create/title/flag) minus upload ([5813ca4](https://github.com/JoShMiQueL/gh-actions/commit/5813ca4fcd1ced1231bec24957d4b40cbb6f2f8a))
* **version.yml:** floating major tag job — v1/v0 moves to each non-prerelease tag so callers pin [@v1](https://github.com/v1) stably ([3bfd6f8](https://github.com/JoShMiQueL/gh-actions/commit/3bfd6f8d1cb33c0283aad4c23a0302b38512d8fe))


### Bug Fixes

* **build:** GNU tar -a produces tar-not-zip (corrupt .zip on Windows) — zip via bsdtar where present else pwsh Compress-Archive ([6479193](https://github.com/JoShMiQueL/gh-actions/commit/647919324a938b70e4f526f2834c9c30ad2e4807))
* **build:** zip fallback chain — bsdtar → zip binary → pwsh (was bsdtar → pwsh, broke on ubuntu where pwsh absent but zip present) ([daab605](https://github.com/JoShMiQueL/gh-actions/commit/daab6051e3f05b37b3fee714dbd5c35af5ec2bcc))
* **build:** zip on Windows — tar reads 'D:\...' as remote host:path (need --force-local); zip binary absent in Git Bash → pwsh Compress-Archive fallback ([1bcf374](https://github.com/JoShMiQueL/gh-actions/commit/1bcf374020c505ead1f7e4e135983992f27ffac7))
* drop set -e in attach step — it killed on the release-view/edit chain; explicit rc + per-artifact error ([8e04c4a](https://github.com/JoShMiQueL/gh-actions/commit/8e04c4a5b066cc0a085cd2bf10659cba9461c8a5))
* **idempotency:** contributors + release-notes append twice on re-tag — skip when already present in body ([a0cbac7](https://github.com/JoShMiQueL/gh-actions/commit/a0cbac7b421623e8b322690c86b4bd771f0a4118))
* Release plan exited 1 on empty inputs (trailing [ -n ] test) — exit 0 ([5cb1a6e](https://github.com/JoShMiQueL/gh-actions/commit/5cb1a6e4eec83b101606abe0368f8ab87587e3e6))
* release-notes idempotency — grep -F on multi-line NOTES matched a blank line and skipped; use first non-empty line as the marker ([f2b6482](https://github.com/JoShMiQueL/gh-actions/commit/f2b64825bb62f5729ce3656cc185ebb58e70e166))
* stamp loop exited 1 on empty version-files (trailing [ -n ] test) — exit 0 ([acdf3cb](https://github.com/JoShMiQueL/gh-actions/commit/acdf3cb0bc62ef07795a4904942d2b2598dcd3c4))
* step shell: can't take expressions — route hooks through bash wrapper, &lt;shell&gt; -NoProfile -Command for pwsh ([f07e062](https://github.com/JoShMiQueL/gh-actions/commit/f07e06212bd3d775658b596d024030c58682ac3f))
* toolchain input missing required 'type' — broke caller resolution ([2bbd3b9](https://github.com/JoShMiQueL/gh-actions/commit/2bbd3b999373785dcafa863b6f80997b7c4331f1))
