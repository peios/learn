---
title: Signing and provenance
type: concept
description: "How pekit signs .peipkg artifacts and PIP-signs binaries, the provenance every manifest records, corresponding-source packages, and the gates publish enforces."
related:
  - pekit/recipes/sources
  - pekit/recipes/environments-and-keyrings
  - pekit/running/workspaces
  - pekit/reference/supporting-files
  - pekit/reference/cli
  - peios/package-management/repositories-and-trust
  - peios/binary-signing-and-pip/scope
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

A `[publish.peipkg]` target additionally needs the private key that signs its
repository descriptor and indexes. Its `signing_key` may name a key file
directly or use `keyring:<dotted.entry>` to read a key-file path from a keyring,
for example `keyring:signing.repository_key`. This is deliberately separate
from the well-known `signing.package_key`: one key may perform both roles, but
the repository publisher also supports distinct package and metadata keys.

When Pekit initializes a repository it records both public keys when they
differ. When publishing to an existing repository, that repository's signed
descriptor must already trust the relevant keys; Pekit never widens an
existing trust set as a side effect of publishing.

## Signing binaries for PIP

Package signing protects the artifact in transit; it says nothing to the
kernel about the programs inside. The Peios kernel derives a process's
[Process Integrity Protection](~peios/binary-signing-and-pip/process-integrity-protection)
tier from a second, separate signature carried by the binary itself, and
pekit produces that signature too — as a step of the **build target**, not of
packaging.

A build target lists the files to sign in a `sign` table, keyed by signature
kind. The `pip` kind maps paths or globs relative to the target's `$PEKIT_OUT`
to the keyring entry that holds the signing key:

```toml
[build.main]
command = "make && make install DESTDIR=$PEKIT_OUT"

[build.main.sign.pip]
"usr/bin/peinit"  = "tcb.priv"
"usr/lib/*.so.*"  = "tcb.priv"
```

```toml
# dev.keyring.pekit.toml — per-developer, gitignored
[tcb]
priv = "kacs-tcb-dev.key"     # openssl genpkey -algorithm ML-DSA-65
```

The value names any keyring leaf; there is no fixed entry name. It holds the
path to an ML-DSA-65 private key — PKCS#8 PEM, or a raw 32-byte seed —
resolved against the invocation's working directory when relative. The kind
decides only the format and the storage location: for `pip` that is the
[fixed 3310-byte blob](~peios/binary-signing-and-pip/signature-format) in an
ELF section named `.peios.sig`.

Signing runs after the target's command exits 0 and before any dependent
target or package sees the output, so it is the last thing to touch the
binary. That ordering is why this is a build step: the signature covers the
whole file, so every strip, debug split or `patchelf` a recipe performs has to
come first, and those all live in build commands. It also means `pekit test`
exercises the signed binary rather than an unsigned stand-in.

For each matched file, pekit:

1. Adds a zero-filled `.peios.sig` section, or reuses one the build already
   reserved (it must be `SHT_PROGBITS` and exactly 3310 bytes). Adding a
   section appends to the file and never moves existing bytes, so program
   headers and loadable segments are unaffected.
2. Hashes the file with the section contents zeroed, signs the hash with pure
   ML-DSA-65 (deterministic, empty context) and writes the blob into the
   reserved bytes.
3. Verifies the finished file the way the kernel will before returning, and
   emits a `sign` event naming the keyring entry and the key's fingerprint —
   the SHA-256 of the raw public key, the same bytes a kernel key table
   carries.

Two properties are deliberate:

- **Every failure is fatal.** A keyring entry that is missing or does not
  load, a pattern that matches nothing, a file that is not a 64-bit
  little-endian ELF, a reserved section of the wrong size, and two patterns
  naming different keys for one file all abort the target. There is no
  `--allow-unsigned` equivalent, because an unsigned binary is not a weaker
  binary: it runs with no tier and no diagnostic, and build time is the only
  place the mistake is visible.
- **Only the ELF section form is produced.** The specification also allows
  the signature in an extended attribute, but package payloads
  [carry no extended attributes](~peios/package-format-and-repository-protocol/determinism),
  so nothing pekit ships could use it. Scripts and other non-ELF files take
  their interpreter's tier and cannot be usefully signed.

Which tier a signature confers is a property of the key, not of anything in
the recipe: the kernel looks the verifying key up in its compiled-in table.
Getting a key into that table is a kernel-build question — see the `tcb.pub`
entry the pkm recipe consumes — and a binary signed with a key the kernel does
not carry is simply unsigned there.

## What the manifest records

Every peipkg manifest pekit writes carries a `build` block stating where the
artifact came from:

| Field | Value |
|---|---|
| `timestamp` | The run's start time, UTC RFC 3339. |
| `farm_id` | `local` — pekit builds are local builds. |
| `source_ref` | The source [provenance ref](~pekit/recipes/sources#source-roots-and-provenance): `git:<url>@<commit>`, `url:<url>#sha256:<hash>`, and so on. |
| `recipe_ref` | The recipe tree's own git commit, `git:<commit>`. Suffixed `+dirty` when any of the build's own inputs are uncommitted — including a freshly written, not-yet-committed `pekit.lock`. Omitted when the recipe is not inside a git work tree. |
| `builder` | The producing pekit's own revision: `pekit/<12-hex-commit>`, `+dirty` when built from a modified tree, falling back to the module version when the binary carries no VCS stamp. |
| `source_package` | The name of the corresponding-source package emitted from this recipe (below); empty when none is. |

Together these state the full provenance chain — the exact upstream inputs,
the exact recipe that drove the build, and the exact tool that performed
it. `recipe_ref` deliberately resolves the **enclosing** repository: a
workspace member's identity is the workspace repository's commit, not some
per-recipe notion.

### What makes a recipe dirty

`+dirty` answers one question: did anything that could change *this* artifact
differ from that commit? So the marker covers the build's own inputs, and
nothing else:

| Counts as dirty | Does not |
|---|---|
| The selected recipe directory — `pekit.toml`, its package definitions, `pekit.lock`, source patches, embedded upstream keys | Other recipes in the same repository, whether or not workspace fan-out selects them |
| Inherited workspace inputs beside the members — `workspace.pekit.toml`, shared package defaults, environment files, keyrings | Pekit's managed output: a member's `out_dir`, as a real directory or as a link into shared staging |
| Anything else uncommitted inside those paths, tracked or not | The destinations a run publishes into, including a local peipkg repository |

Within that scope a dirty tree is over-marked rather than under-marked,
because a commit id alone does not describe a build whose inputs had local
changes: pekit marks the artifact, rather than trying to decide which edits
mattered. That is also why two differently dirty work trees at the same commit
produce the same `recipe_ref` — `+dirty` says the commit is not the whole
story, not what the rest of it was.

A shared recipe repository is the reason for the scope. Without it, editing any
package taints the provenance of every package published from that repository
until the edit is committed, and an operational output or repository link
beside a member taints an otherwise exact commit — which is not something a
repository should have to solve with `.gitignore` entries.

Provenance also decides how long a staged artifact stays usable. Package
stages are stamped with the `recipe_ref`, `builder` and `source_ref` they were
packed under, and a packaging run drops every stage stamped differently before
it packs anything — so committing the recipe, or dirtying the tree, cannot
leave an artifact behind whose `recipe_ref` describes the recipe as it used to
be. Only packing repeats; completed build stages are untouched and
`--no-build` still reuses them. See
[Package stages and recipe provenance](~pekit/running/commands-and-targets#package-stages-and-recipe-provenance).

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
  **url/PyPI** — a local override never qualifies, and neither does a git source
  built from a bare branch ref with no selected version (a deliberately
  moving target has no stable corresponding source);
- at least one emitted member has `format = "peipkg"`.

The package is named `<recipe-dir>-source` by default (rename with
`source_package.name`), is `noarch`, and is versioned identically to the
members — members that disagree on version are a
`source_package_version_conflict` error. Its license is the conjunction of
the members' distinct licenses, joined with ` AND `. Its license class is the
most restrictive class declared by any member, so an all-`free` family remains
`free`, while an omitted or `unknown` member makes the corresponding source
package `unknown`. Its homepage is kept only when every member agrees on one;
and it publishes to the first member's [`[publish]`](~pekit/reference/supporting-files#publish-targets)
destinations.

Everything installs under `/usr/src/dist/<name>-<version>/` (with any
`-source` suffix stripped from `<name>`):

- `upstream/` — the pristine source input. For a url source, the downloaded
  artifact byte-for-byte, so its hash matches the committed `pekit.lock`; for
  an ordinary git source, a `git archive` export of the locked commit —
  deterministic for a commit and independent of the mutable checkout. For
  tracked-path git, that archive is restricted to the one locked relative path;
  no other repository file enters the source package. A URL source's
  upstream-maintained patch series is included byte-for-byte under
  `upstream/patches/`, in the same order and with the same hashes as its
  nested lock entries.
- `source/` — the prepared source tree before package targets run, including the
  applied upstream and distribution patches. Reconstruction uses this tree
  directly, without fetching the upstream source or applying patches again.
- `workspace/` — the captured recipe tree at its original relative path,
  inherited workspace/package/lint policy, environment profiles, and declared
  shared inputs. Recipe-local test fixtures, tools, scripts and license files
  are included. Safe relative symlinks retain their topology; missing or
  escaping targets fail packaging. Empty fixture directories are preserved.
- `recipe/` and `patches/` — compatibility views for older source consumers.
  New reconstruction tooling uses the complete `workspace/` topology.
- `acquisition/vendor/` — captured outputs of an isolated `build.vendor` stage,
  when it ran, including vendored language dependencies.
- `build-environment/` — dependency versions and artifact identities recorded
  by the selected root preparers. The catalogue Debian profile
  records an immutable prepared-root archive and supports explicit replay below.
  Native repository replay remains a separate provider contract.
- `build-inputs.json`, `rebuild.py` and `REBUILD.md` — the versioned bundle
  manifest, reconstruction entry point and required tools. The manifest records
  file hashes, modes, link targets, the upstream version/ref and selected
  environment. Peipkg transport modes differ from source Unix modes; the
  reconstruction tool restores source modes after all hashes verify.

An isolated job copies shared helpers before any target runs. Workers consume
those read-only copies, and the source package contains the same bytes. Recipe
and policy inputs are captured separately from writable worker trees. Editing
those inputs during a job, or before reusing its outputs, causes packaging to
fail with `source_input_changed`; rebuild with the new inputs. Retained outputs
from before source-input capture was introduced also require one fresh build.

The exporter excludes output/cache state, Git internals, ignored developer
files, keyring files, known credential filenames and configured key-file paths.
An explicitly declared input that is missing, ignored or escapes the workspace
is an error. Keep credentials out of tracked recipe material. Copying build
inputs does not authorize distributing private keys.

Workspace `isolation.inputs` are captured automatically. A recipe can add
`source_package.workspace_inputs = ["helpers/python"]` for its own read-only
shared inputs. Coordinator-side support, such as root preparation scripts,
belongs in workspace `[source_package] inputs = ["_peiroot_", "_debroot_"]`;
this captures source without granting workers access to those directories.

### Reconstructing a source bundle

Verify the outer package signature using the distribution's trust configuration,
then extract it and run `python3 rebuild.py test` or `python3 rebuild.py package`
in its `/usr/src/dist/<name>-<version>/` directory. The command verifies captured
hashes, restores source modes, and invokes Pekit with the included prepared tree,
the recorded version, and the original environment. `PEKIT_REBUILD_ENV` can
select another captured environment. Additional Pekit flags follow the command.

Install a compatible Pekit, Python 3, Bubblewrap and the selected profile's root
preparation tools. A native profile still needs its declared trusted package
repository; a fresh Debian environment needs Docker and archive access; retained-root replay
needs neither. For the catalogue,
provide that repository at `workspace/_peipkgRepo_`. These dependency services and
operator signing keys are supplied separately. A generic reconstruction may
rerun the declared language acquisition stage; its captured vendored sources
are also available for language-specific offline replay.

### Retaining and replaying Debian build environments

The catalogue's Debian root preparer separates networked dependency acquisition
from Pekit's offline build and test workers. A fresh job pulls the current
`debian:trixie` image once, records its immutable image ID and repository digests,
and creates every Debian root for that job by ID. APT package requirements use
concrete names, optionally qualified by architecture. A constraint is `*` or a
comma-separated conjunction of `=`, `>=`, `>`, `<=` and `<` comparisons. Debian
version ordering applies, including epochs and `~`; semver ranges and virtual
package requests are not accepted. Before a single joint install, the preparer
filters available versions against the constraints, permitting a necessary
downgrade only inside the disposable root. It checks all final installed direct
dependencies after resolution. Failed archive refreshes and unsatisfied or
unsupported requirements stop acquisition.

Each completed root is exported and retained as `<sha256>.tar.gz`. Its contents
include installed package files, the dpkg database, APT configuration and signed
index metadata. The per-target `debian-root.json` records the requests, base
image, host architecture, preparer hash, archive hash/size and package inventory
hash. `installed.tsv` includes package name, version, architecture and dpkg state.
Both records enter the corresponding source bundle under `build-environment/`.
Large root archives remain in coordinator storage, outside source bundles and
worker mounts.

The default archive store is
`${XDG_STATE_HOME:-$HOME/.local/state}/pekit/debian-roots`.
`PEKIT_DEBIAN_ROOT_STORE` selects another directory, for example a backed-up
release archive volume. Archives are published atomically, verified before
reuse and extracted into fresh roots. Ordinary build cleanup cannot delete the
store. The preparer does not garbage-collect it: retain or back up every archive
referenced by a supported release's records. Source bundles alone do not contain
these dependency bytes. Deleting a referenced archive makes that historical
environment unavailable; the preparer does not silently reconstruct it from a
new archive state.

After verifying and extracting a corresponding-source package, replay its
recorded Debian environment with:

```sh
export PEKIT_DEBIAN_ROOT_STORE=/srv/releases/debian-roots
export PEKIT_DEBIAN_REPLAY="$PWD/build-environment"
python3 rebuild.py test
```

Supply these variables to the coordinator process, not recipe `[env]` tables.
Replay requires Python 3.11+, GNU tar, Pekit and Bubblewrap, but invokes no Docker
or APT commands. It requires matching captured preparer bytes, architecture and
canonical requested dependencies, and verifies both inventory and archive
hashes. Every executed Debian target must have its own record; missing, corrupt
or incompatible records fail without a network fallback. For a native build
using a Debian vendoring root, this option replays only that Debian environment.
Language acquisition commands retain their explicitly declared network policy;
retaining the root alone does not turn a `cargo vendor` invocation into offline
source replay.

Reconstruction uses local provenance and does not claim a byte-identical signed
release. Retained-root replay fixes the dependency filesystem; the host kernel,
CPU capabilities, runtime mounts, clock, signing identities and independent
reproducibility/publication qualification remain separate checks. New ordinary builds continue
following upstream automatically; no manually maintained version pins are added.

Recipes with no reproducible external source, and explicit `--local` builds,
still do not emit an automatic source package. For in-repository products,
distribute the complete catalogue commit/tree (including shared support and
policy) with the release and record that identity, or give the product a
reproducible Git source so automatic source packaging applies. A binary alone
and a moving repository URL are not a complete corresponding-source offer.

Each binary member's manifest names the source package in
`build.source_package`, linking every binary to its corresponding source. The
recipe-side schema is in the
[recipe format reference](~pekit/reference/recipe-format#source-package).

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
- **A Peipkg repository publication verifies every package before changing its
  indexes.** An untrusted package signer, duplicate package identity, damaged
  artifact, or unusable repository metadata key is a
  `peipkg_repository_publish` error.

## Where to go next

For the input side of the chain — the lockfile, `--repin`, and upstream
signature pinning — read [Sources](~pekit/recipes/sources).

For the keyring files that carry the signing key, read
[Environments and keyrings](~pekit/recipes/environments-and-keyrings).

For every flag mentioned here, read the
[command-line reference](~pekit/reference/cli).

## Kernel module signing

```toml
[build.kernel.sign.module]
"modules-root/**/*.ko.zst" = "modsig.priv"
"modules-irf-root/**/*.ko.zst" = "modsig.priv"
```

The keyring entry names an ML-DSA-65 PKCS#8 PEM private key followed by its X.509
certificate. The coordinator signs the uncompressed relocatable ELF bytes,
verifies the detached CMS signature against that certificate, appends the kernel
signature trailer, and recompresses `.ko.zst` outputs. It uses its trusted OpenSSL,
never the build tree's `scripts/sign-file`. OpenSSL 3.5 authenticated attributes
require the kernel's ML-DSA auth-attribute compatibility setting.

Workers need only the public certificate in `modsig.pub`, granted with
`access = "public"` and requested through `keyring_inputs`. Kernel compilation
keeps signature enforcement enabled; `modules_install` suppresses its own signing
invocation with `CONFIG_MODULE_SIG_ALL=`. The coordinator then signs both module
sets before dependent tests run. Firmware tests similarly prepare fixture blobs
in a build target, apply `sign.pip` in the coordinator, and consume those signed
fixtures in the test worker. Production private keys never enter worker source or
output trees.
