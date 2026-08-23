---
title: Validation
description: The package is decompressed, parsed and checked in full before anything is staged — including destinations, and what is not re-checked.
---

Before anything is staged, the package is decompressed, parsed, and
checked in full.

1. Decompress and walk the archive, enforcing the layout and ordering
   rules of PSPU §5.12.
2. Parse the manifest.
3. Parse the files manifest.
4. Check that every payload file has an entry in the files manifest and
   that every entry has a file — in both directions.
5. Check that the manifest's name, version, and architecture match what
   the plan selected.
6. Validate every payload path against PSPU §5.13 and every entry type
   against PSPU §5.12.
7. Validate every symlink's target against PSPU §5.17.
8. Validate every payload entry's destination against the permitted
   install destinations.

## Destinations are checked here

Step 8 is not a duplicate of the producer's own check. A package
arriving on a target system need not have been produced by a cooperating
producer, so validation performed while packing says nothing about the
bytes about to be written. This is where the destination rules are
actually enforced.

**Ancestor directories are exempt.** An archive carries an explicit
entry for every ancestor of the content it ships, and those are
structure rather than destination claims. A directory entry is checked
only when no other payload entry sits beneath it — which is the archive
shape of an explicit empty directory, and *is* a destination claim.

**Special system packages need two keys.** A package declaring
`special_system_package` has waived the producer-side layout check. That
grants nothing here: peipkg refuses an out-of-layout payload unless the
operator also passed `--dangerously-bypass-path-restrictions`. When the
declaration arrives without the flag, the refusal names the refused
request, so that an operator can tell "this package asked for an
exemption I did not grant" from "this package is malformed".

When both keys are present, the destination check is skipped entirely
for that package, with no residual denylist. A package installed this
way can write anywhere, including under `/lcl/policy`.

## What is not re-checked

The determinism rules of PSPU §5.11 constrain the archive's bytes:
ordering, modification times, ownership, mode, extended attributes, and
header format. peipkg checks entry ordering and nothing else. A package
whose entries carry a mode other than `0777`, a non-zero owner, an
`mtime` unrelated to its manifest, or extended attributes is accepted
and installed.

Because extraction ignores tar modes entirely (§5.4), such a package
behaves no differently on Peios. Extracted elsewhere with an ordinary
tar tool, it does not.

## Size cross-checks

The manifest's declared installed size has to equal the sum of the file
sizes in the files manifest, and a package where the two disagree is
rejected. The decompression bounds of PSPU §5.27 are enforced
continuously during the walk, on every chunk of output.

The cap is computed from the size the *manifest* declares, plus the
fixed overhead allowance, subject to the absolute 4 GiB ceiling. The
index's declared sizes are parsed and carried onto the candidate but are
not compared against the manifest's and are not used as the bound.
