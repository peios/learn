---
title: Declaring Dependencies
type: how-to
description: How to declare what your package needs — runtime dependencies, optional dependencies, conflicts, virtual provides, and side-effect tools that run at install time.
related:
  - peios-packages/authoring-recipes/multi-package
  - peios-packages/authoring-recipes/anatomy
---

A `[[package]]` stanza can declare five kinds of relationships to other packages, plus a list of system-side maintenance operations to run on install. None are required — a recipe with no dependency declarations is valid — but most real packages have at least a `dependencies` list and one `side_effects` entry.

All of these fields go inside a `[[package]]` stanza:

```toml
[[package]]
name = "nginx"
architecture = "x86_64"
description = "HTTP and reverse proxy server"

dependencies = [
  { name = "libc" },
  { name = "libssl", constraint = ">= 3.0" },
  { name = "libpcre" },
]
optional_dependencies = [
  { name = "geoip-data" },
]
conflicts = [
  { name = "apache2" },
]
provides = [
  { name = "http-server", version = "1.27.0" },
]
replaces = [
  { name = "nginx-core" },
]
side_effects = ["ldconfig"]
```

## `dependencies`

Required at install time. The package manager refuses to install nginx without these.

The minimal entry has just a name:

```toml
{ name = "libc" }
```

To require a specific version range, add a constraint string:

```toml
{ name = "libssl", constraint = ">= 3.0" }
{ name = "libpcre", constraint = ">= 10.0, < 11.0" }
{ name = "openssl-config", constraint = "= 3.2.1-4" }
```

Constraint operators: `=`, `>`, `>=`, `<`, `<=`, `!=`. Multiple constraints combine with logical AND, separated by commas. A bare version string with no operator is the same as `=`.

Multi-package recipes use `same_build = true` on dependency entries that point at sibling stanzas — see [Multi-package recipes](./multi-package#the-same_build--true-shorthand).

## `optional_dependencies`

Declared but not required. Same schema as `dependencies`. Used to express "this package's functionality is enhanced by X, but it works without it."

`nginx` declaring `optional_dependencies = [{ name = "geoip-data" }]` means: nginx works without geoip-data, but if both are installed, nginx will use the geoip lookup database. The package manager won't auto-install optional deps; users opt in.

## `conflicts`

Packages that *must not* be installed alongside this one. The package manager refuses to install both simultaneously.

```toml
conflicts = [
  { name = "apache2" },
  { name = "lighttpd", constraint = "< 2.0" },
]
```

A bare-name conflict (no constraint) means "any version of this package conflicts." A constrained conflict means "specifically these versions conflict" — useful when the conflict is only with old versions that lacked some integration fix.

> [!CAUTION]
> Conflicts force-uninstall the conflicting package on the consumer's side, which is disruptive. Use them only for packages that genuinely cannot coexist (two HTTP servers binding port 80 by default, two implementations of the same `/etc/` config). Do not use conflicts for "I want my version to win"; that's what `replaces` is for.

## `provides`

Virtual capabilities this package fulfils. Other packages can `dependencies = [{ name = "<virtual>" }]` and any package providing that virtual satisfies the dep.

```toml
provides = [
  { name = "http-server", version = "1.27.0" },
  { name = "reverse-proxy" },
]
```

The version on a `provides` entry is the version of the *virtual capability*, not the package itself. It lets dependents express "I need http-server version >= 1.0" without naming a specific implementation.

## `replaces`

Packages this one supersedes. Used for renames: when `nginx-core` is renamed to `nginx`, the new `nginx` package declares `replaces = [{ name = "nginx-core" }]`. On upgrade, existing systems with `nginx-core` installed transition cleanly to `nginx`.

```toml
replaces = [
  { name = "nginx-core" },
  { name = "nginx-light", constraint = "< 1.20" },
]
```

`replaces` does not imply `conflicts` — they handle different scenarios. A renamed package replaces the old name (transitions cleanly); two genuinely-incompatible packages conflict (cannot coexist).

## `side_effects`

System-level maintenance operations that need to run after this package is installed (or removed). Drawn from a fixed enumerated list — packages cannot specify arbitrary install scripts.

The current set is:

| Identifier | When to declare it | What runs |
|---|---|---|
| `ldconfig` | Package installs shared libraries (`.so`, `.so.*`) under `/usr/lib/`. | Rebuilds `/etc/ld.so.cache`. |
| `depmod` | Package installs kernel modules (`.ko`) under `/usr/lib/modules/`. | Rebuilds the kernel-module dependency cache. |
| `man-db` | Package installs man pages under `/usr/share/man/`. | Rebuilds the man page index for `apropos` and `whatis`. |

The package manager invokes these tools from a fixed allowlist of trusted paths. They cannot be customised per package.

> [!NOTE]
> The fixed list is deliberate. It prevents packages from running arbitrary code at install time — a major attack surface in distros that allow custom maintainer scripts. If your package needs maintenance behaviour outside this list, the right answer is to express it through manifest fields the spec defines, not through arbitrary scripts.

The full normative list is in [PSD-009 §4.3](../../../specs/psd-009--peipkg/v0.22/4-dependencies/3-side-effects).

## What's not yet possible

The schema is forward-compatible; future versions of the spec may add more fields to dependency entries (e.g., explicit architecture qualifiers when multi-arch lands) and more side-effect identifiers. For v0.22:

- **No conditional dependencies.** You can't say "depend on libssl on x86_64 but on libtomcrypt on arm64" in one stanza. Use separate stanzas per architecture.
- **No transitive `provides`.** Providing `http-server` doesn't transitively provide whatever `http-server` itself provides.
- **No file-level dependencies.** You depend on packages, not on individual files. This matches Debian's model, not RPM's.
