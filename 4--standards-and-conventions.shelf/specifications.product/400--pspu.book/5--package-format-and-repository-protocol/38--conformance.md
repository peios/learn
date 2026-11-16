---
title: Conformance
description: The requirements of this chapter collected by role, producer, publisher and consumer.
---

## Producer

- Packs only regular files, symbolic links and directories, refusing
  set-user-ID and set-group-ID files and every other kind (§5.16).
- Writes the manifest in its one form (§5.18), with paths that meet §5.13
  and metadata that meets §5.19 to §5.23.
- Derives what ELF objects need and provide (§5.22).
- Never replaces a stored version with other content (§5.11).

## Publisher

- Signs every pointer file with the repository's key, one higher in
  sequence (§5.32, §5.33).
- Writes tree nodes in their one form (§5.31), with each version's summary
  and the catalog's provides tree.
- Leaves out of `leading` what it can't satisfy, and says so (§5.36).
- Never changes a snapshot, and keeps yanks and tombstones (§5.36).
- Writes an export's pointer file after everything it names, and never
  from an older publication than the export has (§5.36).
- Keeps its private key out of the repository (§5.33).

## Consumer

- Refuses anything not in its one form, and anything that doesn't hash to
  its name (§5.9).
- Checks a package as §5.26 orders before storing it, decompressing the
  blobs of a repository that compresses them and refusing one that
  decompresses to more than 64 GiB (§5.12).
- Gives each file and directory its security metadata before anything
  else can reach it, or says how many lack it (§5.20).
- Refuses the conflicts of §5.24, and reuses a closure that exists.
- Records what wants each package in the inventory (§5.25).
- Resolves as §5.29 specifies, deterministically, from summaries and not
  manifests for a repository served over HTTP, and checks each manifest it
  fetches against its summary (§5.31).
- Checks a configured repository's signature when it has a key, takes its
  packages from its catalog, and refuses a lower sequence than it has seen
  (§5.29, §5.33, §5.34).
- Takes each package name from one repository (§5.30).
- Reads a repository served over HTTP from its catalog, takes the pointer
  file and its signature from one base URL, tries the next base URL when
  one doesn't serve a file, and never when a file fails its check (§5.34).

Conformance doesn't require a consumer to give security metadata on a
system that won't let it, nor to fetch over a network.
