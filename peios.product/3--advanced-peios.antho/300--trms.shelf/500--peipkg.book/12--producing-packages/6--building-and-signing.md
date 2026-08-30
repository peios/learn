---
title: Building and Signing
description: Fetching, patching, building into stage directories, packing the result, signing it, and recording the corresponding source.
---

## The build

pekit fetches or updates the source, applies the patch series, and runs
the targets a package's `builds` list names, each into its own stage
directory, honouring the dependency edges between them.

Every command runs with the assembled environment: the workspace layer,
the source layer, the recipe layer, the selected environment file, and
the keyring, in that order, wrapped by the recipe's wrapper if it
declares one.

Generation targets run their verification where the gating keys direct,
so a build fails if a committed generated artifact is stale.

## Packing

Packing collects the file map's matches from the stage directories, adds
the symlinks, subtracts the excludes, applies templating, merges derived
capabilities over declared ones, and hands the result to the packing
library.

That library builds the manifest, the files manifest, and the archive
according to PSPU §5, and then **decodes its own output through the
consumer's validators**. A package that packs has already satisfied the
rules a consumer applies on the way in — which is why a recipe error
often surfaces as a manifest error at pack time.

The layout check runs here, over the whole file map minus any entry
marked as an override.

The **side-effect check** runs here too, over the whole file map
*including* overrides: an override escapes the layout rules, but a
kernel module still needs indexing wherever it was declared. It enforces
§5.24 in both directions for the effects whose trigger is a payload file
pattern.

| Payload | Declaration | Result |
|---|---|---|
| A `.ko` or `.ko.*` under `usr/lib/modules/` | no `depmod` | Error |
| No kernel module | `depmod` declared | Error |
| A file under `usr/share/man/` | no `man-db` | Warning |
| No man page | `man-db` declared | Warning |

`depmod` is an error because §5.24 makes it a MUST and the failure it
prevents is silent: a stale `modules.dep` makes `modprobe` resolve a
dependency chain and then fail on a file that is not there, far from the
package that caused it. `man-db` is a warning because §5.24 makes it a
SHOULD — lookup falls back to a filesystem scan, which is suboptimal
rather than broken.

Warnings are reported even when an error is also raised, so one run
tells the author everything.

A side effect whose trigger is not a payload pattern is simply not in
the checkable set. The rule is *where the trigger is mechanical, pack
enforces it*, which leaves room for a future effect that depends on what
a package means rather than on what it contains — the declaration stays
the author's, and pack validates it rather than deriving it.

`special_system_package` does **not** waive this check, unlike the
layout one. Special packages stage exotic layouts, which is why those
rules let them through; what maintenance a payload needs afterwards is a
separate question, and the kernel's module tree is exactly the payload
that most needs `depmod`.

## Signing

The signing key is supplied through the keyring, under a well-known key
name. The signature is computed over the uncompressed tar bytes
preceding the signature entry and written as the archive's last entry,
before compression.

A package built with no signing key configured is a conformant unsigned
package, installable only from a repository whose policy permits
unsigned content.

Private keys are read as raw key bytes or in a standard encrypted-key
container. Neither encoding is specified by the format, which cares only
about the resulting signature — but both are a real interface, since the
keyring names a file that some other tool may have produced.

## Binary signing

Separate from the package signature is the signature the kernel checks
on individual files — the ML-DSA-65 blob of PSPK chapter 3 that gives a
binary its PIP tier and lets firmware reach a device. A build target
declares which of its outputs get one and with which key:

```toml
[build.main.sign.pip]
"usr/bin/peinit" = "tcb.priv"
"usr/lib/firmware/**" = "tcb.priv"
```

Each entry maps an output-relative path or glob to the keyring leaf
naming the private key. Signing runs after the build command, over the
staged output, before packing. Every failure is fatal: a pattern that
matches nothing, a key that does not load, a file matched by two
patterns naming different keys, or a signed file that does not verify
back through an independent check.

Where the signature lands depends on the file. An ELF file gets a
`.peios.sig` section, reserved and zero-filled before hashing so the
bytes the kernel hashes are the bytes that were signed. Any other file
— a firmware blob, a data file — gets a **detached signature**,
`<file>.peios.sig`, written beside it with the blob over the whole
file. The file is untouched; the sidecar is packed as an ordinary
payload entry and peipkg turns it into the `security.peios.sig`
extended attribute at install (PSPU §5.16). A glob that sweeps a
sidecar back up does not sign the signature, so `**` is safe.

Each signed file produces one `sign` event naming the placement —
`section` or `sidecar` — the keyring entry and the key's fingerprint.

## Corresponding source

For any recipe with a reproducible source producing packages in the
package format, pekit emits a **corresponding-source package** by
default: the pristine upstream artifact, the applied patch series, and
the build-controlling recipe files, laid out under the source
destination.

The emitted package's name is recorded in the built package's manifest,
so a consumer holding a binary can find the source that produced it.
