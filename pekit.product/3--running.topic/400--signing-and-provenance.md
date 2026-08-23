---
title: Signing and provenance
type: concept
description: "How pekit signs .peipkg artifacts, the provenance every manifest records, corresponding-source packages, and the gates publish enforces."
related:
  - pekit/recipes/sources
  - pekit/recipes/environments-and-keyrings
  - pekit/running/workspaces
  - pekit/reference/supporting-files
  - pekit/reference/cli
  - peios/package-management/repositories-and-trust
---

A published package is a claim: *these bytes were built from these inputs, by
this recipe, with this tool*. Pekit backs that claim end to end. On the input
side, fetched sources are pinned trust-on-first-use in
[`pekit.lock`](~pekit/recipes/sources#the-lockfile) and upstream release
signatures can be verified against committed keys — both covered on the
[Sources](~pekit/recipes/sources) page. This page covers the output side:
signing the artifacts pekit writes, the provenance recorded in every
manifest, the corresponding-source package that keeps a build's exact inputs
publishable, and the checks `publish` runs before shipping anything.

## Signing artifacts

Package signing is configured through one well-known keyring entry,
`signing.package_key`, whose value is the path to an **Ed25519 private
key** — either the raw 32-byte seed or a PKCS#8 PEM as produced by
`openssl genpkey -algorithm ed25519`. A relative path resolves against the
invocation's working directory. Because it rides the
[keyring mechanism](~pekit/recipes/environments-and-keyrings), the key path
lives in a per-developer, gitignored file — or arrives inline as
`--keyring.signing.package_key=<path>` — and private key material never
enters a recipe.

```console
$ pekit publish --keyring=dev
```

With a key configured, **every peipkg-format artifact the run produces** —
package members and the corresponding-source package alike — is packed with
an embedded signature naming the key's fingerprint (the lowercase hex SHA-256
of the raw 32-byte public key), and each emits a `sign` event. Sign events
stay visible under `--quiet`, so a quiet run still shows what was signed with
which key.

Two failure behaviours are deliberate:

- A configured key that cannot be loaded is a hard `signing_key` error. Pekit
  never falls back to silently writing unsigned output — a signing setup that
  degrades quietly would defeat the point.
- Without a key, `package` writes unsigned artifacts (fine for local
  development), but `publish` refuses peipkg-format packages with
  `unsigned_publish` unless you pass `--allow-unsigned`.

## What the manifest records

Every peipkg manifest pekit writes carries a `build` block stating where the
artifact came from:

| Field | Value |
|---|---|
| `timestamp` | The run's start time, UTC RFC 3339. |
| `farm_id` | `local` — pekit builds are local builds. |
| `source_ref` | The source [provenance ref](~pekit/recipes/sources#source-roots-and-provenance): `git:<url>@<commit>`, `url:<url>#sha256:<hash>`, and so on. |
| `recipe_ref` | The recipe tree's own git commit, `git:<commit>`. Suffixed `+dirty` when the work tree has uncommitted changes anywhere — including a freshly written, not-yet-committed `pekit.lock`. Omitted when the recipe is not inside a git work tree. |
| `builder` | The producing pekit's own revision: `pekit/<12-hex-commit>`, `+dirty` when built from a modified tree, falling back to the module version when the binary carries no VCS stamp. |
| `source_package` | The name of the corresponding-source package emitted from this recipe (below); empty when none is. |

Together these state the full provenance chain — the exact upstream inputs,
the exact recipe that drove the build, and the exact tool that performed
it. `recipe_ref` deliberately resolves the **enclosing** repository: a
workspace member's identity is the workspace repository's commit, not some
per-recipe notion. A dirty tree is over-marked rather than under-marked,
because a commit id alone does not describe a build whose tree had local
changes.

## Corresponding-source packages

A recipe with a reproducible source automatically emits a
**corresponding-source package** whenever it packages `peipkg`-format
members. This is how the distribution meets copyleft source-availability
obligations: publishing a binary and its source package through the same
channel keeps the exact inputs of every published build available for as long
as the binary is.

One source package covers every peipkg member the recipe produces. It is
emitted when all of these hold:

- `source_package.enabled` is not set to `false` (emission is the default);
- the source actually materialised as **git with a resolved commit** or
  **url** — a local override never qualifies, and neither does a git source
  built from a bare branch ref with no selected version (a deliberately
  moving target has no stable corresponding source);
- at least one emitted member has `format = "peipkg"`.

The package is named `<recipe-dir>-source` by default (rename with
`source_package.name`), is `noarch`, and is versioned identically to the
members — members that disagree on version are a
`source_package_version_conflict` error. Its license is the conjunction of
the members' distinct licenses, joined with ` AND `; its homepage is kept
only when every member agrees on one; and it publishes to the first member's
[`[publish]`](~pekit/reference/supporting-files#publish-targets) destinations.

Everything installs under `/usr/src/dist/<name>-<version>/` (with any
`-source` suffix stripped from `<name>`):

- `upstream/` — the pristine source input. For a url source, the downloaded
  artifact byte-for-byte, so its hash matches the committed `pekit.lock`; for
  a git source, a `git archive` export of the locked commit — deterministic
  for a commit and independent of the mutable checkout.
- `patches/` — the recipe's [patch series](~pekit/recipes/sources#patches),
  when one is declared. The applied series is the shipped series by
  construction, and it ships under the fixed `patches/` name even when
  `[source].patches` picks a different directory.
- `recipe/` — the build-controlling files from the recipe directory:
  `pekit.toml`, `pekit.lock`, package definitions (including
  `packages.pekit/`), env files, and `keys/`. `*.keyring.pekit.toml` files
  are **never** included — developer key material stays out.

Each binary member's manifest names the source package in
`build.source_package`, linking every binary to its corresponding source. The
recipe-side schema is in the
[recipe format reference](~pekit/reference/recipe-format#source_package).

## What publish checks before shipping

`publish` is packaging plus shipping, and the shipping half is gated:

- **Unsigned peipkg packages are refused** (`unsigned_publish`) unless
  `--allow-unsigned` is passed, as above.
- **Unanchored provenance is refused** (`unanchored_provenance`) unless
  `--allow-unanchored` is passed. Unanchored means a url source with neither
  a `checksum` nor a lock entry — a state a real resolve immediately locks
  away, so in practice this gates dry-run publish plans for never-fetched
  sources. A plain `package` from an unanchored source warns instead.
- **An existing destination file is refused** (`publish_exists`) when the
  target's `overwrite = false`.
- **Two artifacts resolving to the same destination** in one run is a
  `publish_collision`; across workspace members, the
  [publish preflight](~pekit/running/workspaces#cross-member-publish-collision-detection)
  catches the same collision before any member ships anything.

## Where to go next

For the input side of the chain — the lockfile, `--repin`, and upstream
signature pinning — read [Sources](~pekit/recipes/sources).

For the keyring files that carry the signing key, read
[Environments and keyrings](~pekit/recipes/environments-and-keyrings).

For every flag mentioned here, read the
[command-line reference](~pekit/reference/cli).
