---
title: Install
---

This section defines the install operation: the procedure
for adding a new package to the system.

Install is one of three primitive package operations
defined in this chapter; upgrade (§7.2) and uninstall
(§7.3) are the others. All three execute within a
transaction (§7.4) and can be rolled back on failure
(§7.5).

## Preconditions

An install operation begins with the following inputs:

- A `.peipkg` file (already fetched).
- The repository the package was fetched from, with its
  trust state.
- The current installed-package database state.
- The current resolution plan (§4.2) that called for
  this install.

The following preconditions MUST hold before install
proceeds:

1. The package's hash matches the value recorded in the
   repository index (§3.5.3 step 2).
2. The package's signature, if present, verifies against
   the trust set scoped to its origin repository (§5.3.2).
3. The package is not already installed at the same
   version and architecture.
4. The package's architecture matches the system's
   primary architecture or is `noarch` (§2.3.5).
5. The package's dependencies (§4.1) are satisfied by the
   current installed set, the in-flight resolution plan,
   or both combined.
6. No installed package conflicts (§4.1.2) with this
   package.

A precondition failure aborts the install. The transaction
that contains it (if any) MUST be rolled back per §7.5.

## Procedure

The install procedure consists of the following ordered
steps. Each step MUST complete successfully before the
next begins.

### Step 1: parse and validate

1. Decompress the `.peipkg` file.
2. Parse `.peipkg/manifest.json` per §3.3.
3. Parse `.peipkg/files.json` per §3.5.1.
4. Validate that every payload tar entry has a
   corresponding entry in `files.json` per §3.5.1.3.
5. Validate that the manifest's `name`, `version`, and
   `architecture` match what the resolution plan
   selected.
6. Validate every payload entry's path against the
   constraints in §3.2.7 and the entry-type
   restrictions in §3.2.6.
7. Validate every symlink entry's linkname against the
   target constraints in §3.4.8.

### Step 2: prepare

1. Compute the install plan: which files will be created,
   which directories will be created, which side effects
   will be invoked.
2. Verify disk space: the filesystem MUST have sufficient
   free space for the transaction's full duration. The
   reservation accounts for staged copies of files being
   installed (§7.2.3), backup copies of files being
   modified or removed (§7.5.1.3), and the final installed
   payload. A conservative bound is
   `size(ADDED) + 2 × size(REPLACED) + size(REMOVED)`,
   aggregated across all operations in the transaction.
   For a pure install (no replacements), this reduces to
   `size_installed` (§3.3.3). Staging and backup space is
   released at commit; steady-state disk usage matches
   `size_installed`.
3. Verify no payload path collides with a path already
   owned by another installed package (§3.4.10).

### Step 3: extract

For each payload entry in tar order:

1. Determine the install path on disk by joining the
   payload-relative path with the filesystem root. Path
   resolution MUST use TOCTOU-safe interfaces: the
   package manager MUST NOT traverse a symlink it did
   not itself create earlier in this same install
   operation when resolving the install path. On Linux,
   this is achieved with `openat2(...,
   RESOLVE_NO_SYMLINKS | RESOLVE_BENEATH | RESOLVE_NO_XDEV
   | RESOLVE_NO_MAGICLINKS)` anchored at the relevant
   `/usr/`, `/etc/`, or `/var/` subtree, or equivalent
   semantics with `O_NOFOLLOW` on every component.
   `RESOLVE_NO_MAGICLINKS` is included to prevent
   accidental redirection through `/proc/self/fd/`
   magic links should the package manager hold an
   unrelated file descriptor open during extraction.
2. If a non-directory entry already exists at the install
   path (whether owned by another package or unowned),
   handle per the file-ownership rule (§7.1.5). Pre-
   existing symlinks at the install path MUST be
   removed atomically before write; they MUST NOT be
   followed.
3. For directory entries: create the directory if it does
   not exist. Set the directory's permissions per the
   tar entry's mode.
4. For symlink entries: create the symlink with the tar
   entry's linkname as target. The linkname MUST satisfy
   the symlink-target constraints in §3.4.8 — these
   are validated at parse time (§7.1.2.1), so by the
   time extraction reaches a symlink entry the target
   is known-safe.
5. For regular-file entries: create the file with the tar
   entry's mode and content. Apply security descriptor
   per §3.4.7 (inheritance by default; manifest-declared
   override if present).
6. After creating the file, compute its content hash and
   verify it matches the corresponding entry in
   `.peipkg/files.json` (§3.5.3 step 7).
7. If hash verification fails, roll back the install per
   §7.5.

Each file extraction SHOULD be performed atomically (write
to a temporary path within the same parent directory,
then `renameat2` to the final path). The exact atomicity
mechanism is implementation-defined; the requirement is
that no consumer of the filesystem observes a
partially-written file and that the rename does not
follow a symlink at the destination.

> [!INFORMATIVE]
> Tar order constrains how the consumer reads from the
> archive (the format is sequential), not the order in
> which files are placed on disk. After parsing a tar
> entry, a consumer MAY apply its filesystem effects
> concurrently with reading and processing later entries,
> provided that (a) signature verification (§3.5.3 step
> 3) has succeeded before any externally-observable
> filesystem effect is applied; (b) the per-file hash
> check (step 6 above) is performed before any file is
> committed to its final install path; and (c) every
> path resolution uses the TOCTOU-safe interface
> mandated in step 1.

### Step 4: side effects

For each side effect declared in the manifest's
`side_effects` (§4.3) field, schedule it for invocation at
transaction commit. Side effects are deduplicated and
batched across all operations in the transaction (§7.4.6).

### Step 5: register

Update the package database to record the package as
installed:

- Package identity (name, version, architecture).
- Originating repository.
- Install timestamp.
- The list of payload paths owned by this package.
- The package's manifest contents (or a reference to
  them, sufficient to reconstruct).

The database update MUST be part of the transaction and
MUST be visible only on transaction commit (§7.4.5).

## Side-effect timing

Side effects (§4.3) are NOT invoked during step 3
extraction. They are invoked at transaction commit, after
all packages in the transaction have completed extraction
and registration.

This permits the system to remain in a consistent state
during multi-package installs: ldconfig is invoked once
after every package's libraries are extracted, not after
each package individually. Same for depmod and mandb.

## Failure handling

A failure during any step of install MUST cause the
install to be considered aborted. The containing
transaction (§7.4) is responsible for rolling back any
partial state per §7.5.

Failures include but are not limited to:

- Hash mismatch on any payload file (§3.5.3 step 7)
- Disk space exhaustion during extraction
- Permission denied (parent directory not writable, SD
  inheritance forbids creation)
- I/O errors
- Database write failure

The package manager MUST report which step failed and
why.

## File ownership

A file is *owned by* the package whose install procedure
created it. Ownership is recorded in the package database
(step 5 above).

A path that already exists on the filesystem and is not
owned by any installed package SHOULD NOT be overwritten
by an install. The package manager MUST fail with an
explicit error rather than overwriting unowned files,
unless the user explicitly authorises overwrite.

> [!INFORMATIVE]
> Unowned existing files indicate either a previous
> non-package install (manual `cp` to `/usr/bin/`, for
> example) or filesystem state inherited from a non-Peios
> install. Either way, silently overwriting risks
> destroying user data or hand-curated state. Failing
> closed surfaces the situation for explicit resolution.
