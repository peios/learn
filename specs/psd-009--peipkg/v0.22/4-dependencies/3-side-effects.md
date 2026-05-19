---
title: Side Effects
---

Some standard Linux maintenance operations need to run after
files are installed or removed in order for the system to
function correctly. Examples include rebuilding the shared
library cache after a library is added, rebuilding the
kernel module dependency cache after kernel modules change,
and rebuilding the man page index after man pages are added.

These operations are not arbitrary install scripts. The
package format does not permit packages to specify their
own install scripts. Instead, packages declare the standard
maintenance operations they require via the manifest's
`side_effects` field, and the package manager invokes them
from a fixed enumerated set.

## Schema

The `side_effects` field of the manifest is an array of
strings:

```json
"side_effects": ["ldconfig", "man-db"]
```

Each string MUST be drawn from the enumerated set defined in
§4.3.4. Unknown values are INVALID and cause the package to
be rejected.

The array MAY be empty (or the field omitted entirely) for
packages that require no maintenance operations.

The array MUST NOT contain duplicate values.

## Semantics

The package manager invokes each declared side effect once
per transaction, after the transaction's database commit
(§7.4.5 step 4) — that is, after all of the transaction's
file operations are in place.

Side effects are deduplicated across packages within a
single transaction: if multiple packages in the same
transaction declare `ldconfig`, the operation runs once for
the transaction, not once per package.

A side effect MUST be idempotent: running it multiple times
in succession MUST produce the same final system state as
running it once. The fixed set of recognised side effects
have this property by construction.

A side effect MUST be safe to invoke from a non-interactive
context. The package manager runs side effects without user
prompting.

The package manager MUST invoke side-effect tools with:

- A **fixed absolute path** to the tool. The recognised
  side effects are a closed set (§4.3.4); the package
  manager invokes each from its known absolute location
  and MUST NOT search `PATH`.
- A cleared environment containing only well-defined
  variables (e.g. `LANG=C`, `LC_ALL=C`, `PATH=/usr/bin`).
  Inherited environment from the invoking shell MUST NOT
  be passed through.
- Standard input closed.

> [!INFORMATIVE]
> If the package manager located `ldconfig` via `PATH`, a
> package that had earlier installed a hostile
> `/usr/local/bin/ldconfig` could shadow the legitimate
> tool. Because the side-effect set is closed, the package
> manager needs no configurable allowlist — a fixed
> absolute path per tool both eliminates the shadowing
> path and guarantees the *real* tool runs, so the cache
> is genuinely rebuilt. Cleared environment prevents
> environment-variable injection from affecting tool
> behaviour.

## Failure handling

Side effects run *after* the transaction's database commit
(§7.4.5 step 4), so a side-effect failure does not — and
cannot — roll the transaction back: the transaction is
already committed. If a side effect fails (the underlying
tool exits non-zero or is unavailable), the package manager
MUST report the failure to the operator, but the
transaction stands.

Because side effects are idempotent, a failed side effect
is self-correcting: re-invoking it — explicitly, or as part
of the next transaction that declares it — reaches the
correct state. The package manager SHOULD make a failed
side effect straightforward to re-invoke.

> [!INFORMATIVE]
> Side-effect failures are rare in practice — `ldconfig`,
> `depmod`, and `mandb` are stable tools with few failure
> modes outside system-level corruption. Rolling a
> committed transaction back because, say, `mandb` exited
> non-zero would be a disproportionate response: the
> packages installed correctly, only a cache rebuild
> lagged, and that rebuild is idempotently recoverable.

## Recognised side effects

This version of the specification recognises the following
side effect identifiers:

### `ldconfig`

Rebuilds the shared library cache (`/etc/ld.so.cache`) and
updates symlinks for shared libraries.

A package MUST declare `ldconfig` in its `side_effects` if
its payload contains any of:

- Shared library files (`.so`, `.so.*`)
- Files installed under any directory listed in
  `/etc/ld.so.conf` or its includes

A package MUST NOT declare `ldconfig` if its payload contains
none of the above.

The package manager invokes the system's ldconfig tool with
arguments equivalent to `ldconfig` (no flags), which scans
the standard library directories and rebuilds the cache.

### `depmod`

Rebuilds the kernel module dependency cache
(`modules.dep` and related files in `/usr/lib/modules/<ver>/`).

A package MUST declare `depmod` in its `side_effects` if
its payload contains kernel module files (`.ko`, `.ko.*`)
under `/usr/lib/modules/`.

A package MUST NOT declare `depmod` if its payload contains
no kernel modules.

The package manager invokes depmod against the kernel
version corresponding to the modules being installed. If
the package contains modules for multiple kernel versions,
depmod is invoked once per affected version.

### `man-db`

Rebuilds the man page index (`/var/cache/man/index.db` or
equivalent), permitting fast lookup by `apropos` and `whatis`.

A package SHOULD declare `man-db` in its `side_effects` if
its payload contains man pages under `/usr/share/man/`.

The package manager invokes the system's man-db tool with
arguments equivalent to `mandb -q` (quiet mode).

> [!INFORMATIVE]
> `man-db` is SHOULD-declared rather than MUST-declared
> because man page lookup degrades gracefully without it
> (queries fall back to filesystem scans). A package omitting
> `man-db` for a payload containing man pages is suboptimal
> but does not break.

## Reservation for future side effects

The set of recognised side effects in this version is
deliberately small. Future versions of this specification
MAY introduce additional side effects for other standard
maintenance operations.

A v0.22-conformant implementation MUST reject manifests
declaring side effect identifiers outside the set defined in
§4.3.4.

> [!INFORMATIVE]
> Likely candidates for future addition include
> `update-mime-database`, `update-desktop-database`, and
> `udev-reload`. These were excluded from v0.22 because they
> are not relevant to the infrastructure-server-OS scope of
> Peios v1.

## What side effects are not

Side effects are NOT:

- A general install-script mechanism. The fixed enumeration
  prevents arbitrary code execution at install time.
- A way to register services with peinit. Service
  integration is the concern of higher-level artifacts that
  compose packages, not of packages themselves (§1.1).
- A way to seed registry state. Registry seeds are managed
  by higher-level artifacts and applied by reconciller
  daemons, not by package install.
- A way to apply KACS xattrs or SDs. SDs are applied at
  file-creation time per §3.4.7.

A package whose required behavior cannot be expressed via
the manifest schema (including `side_effects`) is incomplete
and cannot be installed via the package format alone. Such
behavior MUST be supplied by the higher-level artifact that
composes the package.
