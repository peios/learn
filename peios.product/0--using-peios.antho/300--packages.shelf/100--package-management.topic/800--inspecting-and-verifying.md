---
title: Inspecting and verifying
type: how-to
description: Find installed software and file owners, check package contents after a change, interpret verification differences, and optionally clean the metadata cache.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/transactions-and-recovery
---

Use the query commands to identify installed software and its source, or
`verify` to compare installed files with peipkg's records. These checks are
read-only. The optional `clean` command below does delete cache data.

Run them against the same root as the change you are checking, with
`peipkg --root TARGET ...` when that is not `/`.

| Question | Command |
|---|---|
| What is installed? | `peipkg list` |
| Which version and source supplied a package? | `peipkg info <package>` |
| Which files does it own? | `peipkg files <package>` |
| Who owns this path? | `peipkg owns <path>` |
| What can my repositories install? | `peipkg search <term>` |
| Did files change or disappear? | `peipkg verify [package]...` |
| What operation ran? | [`peipkg history`](~peios/package-management/transactions-and-recovery#the-transaction-log) |

A successful file check does not test service health, feature state or user
data. After a failed transaction, read the
[recovery limits](~peios/package-management/transactions-and-recovery)
even if history says `rolled-back`.

## Listing what is installed

```
peipkg list
```

`list` prints every installed package — name, version, and architecture.

```
$ peipkg list
nginx  1.27.5  x86_64
pcre2  10.44   x86_64
zlib   1.3.2   x86_64
```

With `--json` it emits the same set as a JSON array. Each package has `name`, `version`, `architecture`, `origin` (the repository it came from, empty for a local file), `orphaned`, `installed_at`, `size_installed` in bytes, and `description` where its manifest has one.

## Showing one package's details

```
peipkg info <package>
```

`info` prints the full record of one installed package: its version and architecture, the repository it came from (or `(local file)` if it was installed from a `.peipkg` directly), when it was installed, and — from its manifest — its description, license, and homepage.

```
$ peipkg info nginx
name:         nginx
version:      1.27.5
architecture: x86_64
origin:       official
installed:    2026-05-19T14:02:10Z
description:  HTTP and reverse proxy server
license:      BSD-2-Clause
homepage:     https://nginx.org
```

With `--json` it emits the same record as one JSON object: the members `list --json` gives, and — where the manifest has them — `license`, `license_class`, `homepage`, `alternate_upgrade`, `dependencies` (each a name and any version constraint) and `provides`.

## Listing the files a package owns

```
peipkg files <package>
```

`files` prints every filesystem object the package owns — the files, directories, and symlinks that were placed by its install and are tracked against it. This is the record peipkg uses to remove the package cleanly and to verify it.

```
$ peipkg files zlib
/usr/lib/libz.so.1
/usr/lib/libz.so.1.3.2
/usr/include/zlib.h
```

With `--json` it emits an array of objects, each with `path`, `type` (`file`, `dir` or `symlink`) and, for a symlink, `target`.

## Finding which package owns a path

```
peipkg owns <path>
```

`owns` is the reverse lookup: given a path, it reports which installed package placed it.

```
$ peipkg owns /usr/lib/libz.so.1
zlib
```

If no installed package owns the path, `owns` says so and exits non-zero. A path that nothing owns is either not part of any package or was created outside peipkg. With `--json` it emits the owners' names as an array, empty when nothing owns the path.

## Searching the repositories

```
peipkg search <term>
```

`search` looks through the configured repositories' active indexes for packages whose name or description contains the term, case-insensitively. It searches what is available, not what is installed — it is how you find a package before installing it.

```
$ peipkg search proxy
nginx     1.27.5  [official]  HTTP and reverse proxy server
haproxy   2.9.7   [official]  Reliable, high-performance TCP/HTTP load balancer
```

`search` reads the cached repository metadata, so run [`peipkg refresh`](~peios/package-management/keeping-a-system-current) first if you want it to reflect the latest catalog. A repository with no usable cached metadata is skipped with a warning rather than failing the search. `--json` emits the matches as an array, empty when nothing matches. Each has `name`, `version`, `architecture`, `repository`, `size_download` and `size_installed` in bytes, and `description`, `license` and `homepage` where the repository gives them.

## Verifying installed files

```
peipkg verify [package]...
```

`verify` checks that what is on disk still matches what was recorded when each package was installed. For every file a package owns it checks:

- a **regular file** — that it is present and its content still hashes to the recorded value;
- a **symlink** — that it is present and still points where it was recorded to point;
- a **directory** — that it is still present and still a directory.

With no arguments, `verify` checks every installed package. With package names, it checks only those.

```
$ peipkg verify nginx
nginx: /etc/nginx/nginx.conf has been modified since install
verify: 1 problem(s) found
```

A reported file is not necessarily a fault. A configuration file you edited on purpose will show up — `verify` is telling you the file diverged from the package's version. `verify` reports; it does not judge intent and it does not change anything.

If every checked file is intact, `verify` says so and exits `0`. If anything diverged, it lists each problem and exits non-zero — which makes it usable as a check in a monitoring script.

With `--json` it emits the problems as an array, each a `package` and a `problem`, and exits `0` whether or not it found any: an empty array means every checked file is intact.

## Investigate an unexpected verification result

1. Use `info` and `files` to establish the package, version and affected paths.
2. Compare the result with intended edits. For configuration under
   `/usr/etc/` or legacy `/etc/`, a `.peipkg-new` sibling can mean an upgrade
   preserved your edit and wrote a new default beside it. That original path
   can continue to report a mismatch against the new recorded hash.
3. If the difference is unexpected, consider an interrupted rollback, storage
   corruption or tampering; a hash mismatch alone does not distinguish them.
   Preserve files you need before attempting replacement.
4. Repair deliberately, then verify again. There is no `reinstall` command;
   the [file-mismatch reference](~peios/peipkg/failure-modes/a-file-that-does-not-match)
   describes removal and installation as separate transactions or a version
   change and change back. Preview dependency and removal consequences first.

`verify` does not repair anything, and an unowned `.peipkg-new` or backup is
not proof that the current package's recorded files are intact.

## Cleaning the metadata cache

```
peipkg clean
```

`clean` deletes unused metadata-cache data; it is a write operation, not a
package verification or recovery command. The [cache reference](~peios/peipkg/repositories/the-index-cache#structure)
describes content-addressed objects, with pointers naming each repository's
current metadata, and collection of objects no pointer references.

```
$ peipkg clean
removed 2 orphaned cache file(s)
```

Earlier operator guidance described deletion solely by removed repository;
the technical reference instead describes unreferenced-object collection,
which can also cover superseded objects from a still-configured source. Do
not rely on a repository being configured to preserve every old cached object.
This guide does not establish which cache layout your tool version uses.
Cleaning is optional housekeeping, not a way to recover a pending transaction;
it does not replace reviewing `history`, running `recover` or checking files.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The command succeeded. For plain `verify`, every checked file was intact. `verify --json` also exits `0` when it finds problems: inspect the array. |
| `1` | The command failed — a named package is not installed, a path is owned by nothing, or, for plain `verify`, at least one file had diverged. |
| `2` | A usage error — an unknown command or a malformed option. |
