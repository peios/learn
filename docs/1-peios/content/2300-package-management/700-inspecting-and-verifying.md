---
title: Inspecting and verifying
type: reference
description: The read-only peipkg commands — list, info, files, and owns to see what is installed, search to find a package in the repositories, verify to check installed files are intact, and clean to tidy the metadata cache.
related:
  - peios/package-management/overview
  - peios/package-management/installing-and-removing
  - peios/package-management/repositories-and-trust
  - peios/package-management/transactions-and-recovery
---

The commands on this page change nothing. They report what is installed, look up a package in the repositories, check that installed files are still intact, and tidy the metadata cache. They are the tools for answering "what is on this system?" and "is it still as it should be?".

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

With `--json` it emits the same set as JSON, with each package's origin repository included.

## Showing one package's details

```
peipkg info <package>
```

`info` prints the full record of one installed package: its version and architecture, the repository it came from (or `(local file)` if it was installed from a `.peipkg` directly), when it was installed, and — from its manifest — its description, licence, and homepage.

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

## Finding which package owns a path

```
peipkg owns <path>
```

`owns` is the reverse lookup: given a path, it reports which installed package placed it.

```
$ peipkg owns /usr/lib/libz.so.1
zlib
```

If no installed package owns the path, `owns` says so and exits non-zero. A path that nothing owns is either not part of any package or was created outside peipkg.

## Searching the repositories

```
peipkg search <term>
```

`search` looks through the configured repositories' active indexes for packages whose **name or description** contains the term, case-insensitively. It searches what is *available*, not what is installed — it is how you find a package before installing it.

```
$ peipkg search proxy
nginx     1.27.5  [official]  HTTP and reverse proxy server
haproxy   2.9.7   [official]  Reliable, high-performance TCP/HTTP load balancer
```

`search` reads the cached repository metadata, so run [`peipkg refresh`](~peios/package-management/keeping-a-system-current) first if you want it to reflect the latest catalogue. A repository with no usable cached metadata is skipped with a warning rather than failing the search. `--json` emits the matches as JSON.

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

A reported file is not necessarily a fault. A configuration file you edited on purpose will show up — that is `verify` doing its job, telling you the file diverged from the package's version. `verify` reports; it does not judge intent and it does not change anything.

If every checked file is intact, `verify` says so and exits `0`. If anything diverged, it lists each problem and exits non-zero — which makes it usable as a check in a monitoring script.

## Cleaning the metadata cache

```
peipkg clean
```

peipkg keeps a verified copy of each repository's metadata in a local cache. When you remove a repository, its cached metadata is no longer needed. `clean` deletes exactly those orphaned cache files — the ones belonging to repositories that are no longer configured.

```
$ peipkg clean
removed 2 orphaned cache file(s)
```

`clean` never touches the metadata of a repository that is still configured, so it cannot leave you needing a refresh. It is pure housekeeping; run it whenever you like, or never.

## Exit status

| Code | Meaning |
|---|---|
| `0` | The command succeeded. For `verify`, every checked file was intact. |
| `1` | The command failed — a named package is not installed, a path is owned by nothing, or, for `verify`, at least one file had diverged. |
| `2` | A usage error — an unknown command or a malformed option. |
