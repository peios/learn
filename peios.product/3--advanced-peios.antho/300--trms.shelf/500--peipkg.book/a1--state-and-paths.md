---
title: State and Paths
description: Every path peipkg reads or writes — per root, transient names, composition, side-effect tools and producer files.
---

## Per installation root

| Location | Content |
|---|---|
| `<root>/var/state/peipkg/db.sqlite` | The package database: installed packages, owned files, repositories, claims, named roots, and the transaction journal (§2.5) |
| `<root>/lcl/conf/peipkg/<name>.repo` | One repository configuration file per configured repository |
| `<root>/var/state/peipkg/cache/` | The index cache: content-addressed index and signature objects, and a pointer file naming the current object per repository |

The database is the only authoritative state. The configuration
directory is the operator's, and the cache is disposable.

## Transient names

| Pattern | Meaning |
|---|---|
| `<destination>.peipkg-staged-<txnid>` | A file written but not yet committed, a sibling of its destination |
| `<destination>.peipkg-backup-<txnid>` | A displaced original, a sibling of its destination |
| `<name>.peipkg-new` | A package's new default beside a configuration file the operator had edited |

The first two are removed at commit or at rollback. The third is
permanent and is owned by nothing.

Where a destination's basename is long enough that adding the marker
would exceed the filesystem's name limit, the basename is truncated to
fit.

## Composition

| Location | Content |
|---|---|
| `<manifest-stem>.lock.toml` | The pinned closure a composition resolves to |
| `<out>.peipkg-compose-tmp` | The tree under construction, renamed into place on success |
| `<out>/usr/share/licenses.json` | The license inventory the composer writes, owned by no package |

## Side-effect tools

| Identifier | Invoked |
|---|---|
| `ldconfig` | `/bin/ldconfig` |
| `depmod` | `/libexec/depmod -a` |
| `man-db` | `/bin/mandb -q` |

Each with a cleared environment of `LC_ALL=C` and `PATH=/bin`, and with
input closed.

`depmod` sits in `/libexec` rather than `/bin` because it is machine-facing:
this and the kernel's own `make modules_install` are its only callers, and no
documented workflow has a person running it. The fixed-path property the design
depends on is unaffected — `/libexec` is a merged view with the same
local-stratum protection as `/bin`, so a package still cannot shadow the tool.

## Producer files

| File | Role |
|---|---|
| `pekit.toml` | The recipe |
| `workspace.pekit.toml` | The workspace marker |
| `package.pekit.toml`, `<selector>.package.pekit.toml` | Package definitions, layered |
| `packages.pekit/` | An alternative directory for the above |
| `env.pekit.toml`, `<name>.env.pekit.toml` | Build environments |
| `<name>.keyring.pekit.toml` | Secrets, including the package signing key |
| `pekit.lock` | The source pin |
| `<patches>/series` | The patch series |
