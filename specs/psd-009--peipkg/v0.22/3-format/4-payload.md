---
title: Payload Layout
---

The payload is the set of files, directories, and symlinks
that a package installs on the target system. This section
specifies the install paths, permissions, and structural
conventions that payload entries MUST follow.

## Filesystem layout

Peios uses a usrmerged filesystem layout: the historical
distinction between `/bin` and `/usr/bin`, between `/lib`
and `/usr/lib`, and between `/sbin` and `/usr/sbin` does not
exist. Packages MUST install only under `/usr/`, with
exceptions for conventional system paths listed below.

Permitted top-level install destinations:

| Path | Purpose |
|---|---|
| `/usr/bin/` | Executable binaries (user-facing and system) |
| `/usr/lib/<triplet>/` | Architecture-specific libraries and arch-dependent data |
| `/usr/share/` | Architecture-independent data |
| `/usr/include/` | Header files (typically in `-dev` packages) |
| `/etc/` | Default configuration files |
| `/var/` | Runtime variable state directories (typically empty at install time) |
| `/opt/` | Self-contained third-party software trees |

Payload entries MUST NOT install under any other top-level
path.

> [!INFORMATIVE]
> Notably absent from this list: `/bin`, `/sbin`, `/lib`,
> `/lib64`, `/usr/sbin`, `/usr/local`, `/srv`, `/home`,
> `/root`, `/tmp`. These are either symlinks to permitted
> paths in the running system, runtime-only directories, or
> reserved for purposes other than package installation.

## Architecture triplet for libraries

Packages whose architecture is not `noarch` MUST install all
of the following under `/usr/lib/<triplet>/` where
`<triplet>` is the architecture triplet defined in §2.3.3:

- Shared libraries (`.so`, `.so.*`)
- Static libraries (`.a`)
- Loadable modules (plugin shared objects, kernel modules
  outside of `/usr/lib/modules/`)
- Helper binaries not on user PATH (`libexec`-style content)
- Any other arch-dependent files that are not user-facing
  binaries

Packages whose architecture is `noarch` MUST NOT install any
files under `/usr/lib/<triplet>/`. A `noarch` package whose
contents includes any of the above categories is INVALID.

> [!INFORMATIVE]
> Example: an `x86_64` nginx package installs the binary at
> `/usr/bin/nginx` and its modules under
> `/usr/lib/x86_64-linux-peios/nginx/modules/`. A `noarch`
> documentation package for nginx installs man pages under
> `/usr/share/man/` and contains no library content.

## Architecture-independent data

The `/usr/share/` tree holds architecture-independent files
shared across all architectures of a system. Typical content:

- Documentation (`/usr/share/doc/<package>/`)
- Man pages (`/usr/share/man/<section>/`)
- Locales (`/usr/share/locale/`)
- Default configuration templates (`/usr/share/<package>/`)
- Static data (icons, images, fonts)

Both `noarch` packages and arch-specific packages MAY
install under `/usr/share/`. Files installed by an arch-
specific package under `/usr/share/` MUST be byte-identical
across architecture builds of the same upstream version.

## Configuration files

Default configuration files MAY be installed under `/etc/`.
Configuration files installed by a package are referred to
as *seed configuration*: they represent the package's
defaults, not the running system's effective configuration.

> [!INFORMATIVE]
> Effective configuration on Peios is materialised by
> reconciller daemons from registry state (PSD-005). A
> package's seed configuration in `/etc/` is consulted by
> reconcillers as a default; runtime changes go through the
> registry. Detailed semantics are out of scope for this
> specification.

The package format does not distinguish "config files" from
other files at the format level. Reconcillers and higher-
level integration mechanisms determine which `/etc/` files
are managed and how.

### Drop-in directories

Several `/etc/` subdirectories are *drop-in directories*:
their contents are interpreted as code or configuration
by other tools (notably side-effect tools per §4.3 and
system daemons that read configuration drop-ins). A
package writing to a drop-in directory has indirect
influence on the behaviour of other components that
read those drop-ins.

Packages from non-official repositories MUST NOT install
files at the top level of any of the following drop-in
directories. The list MAY be extended by operator
configuration:

- `/etc/ld.so.conf.d/`
- `/etc/profile.d/`
- `/etc/sudoers.d/`
- `/etc/cron.d/`, `/etc/cron.daily/`, `/etc/cron.hourly/`,
  `/etc/cron.weekly/`, `/etc/cron.monthly/`
- `/etc/sysctl.d/`
- `/etc/modules-load.d/`
- `/etc/modprobe.d/`
- `/etc/binfmt.d/`
- Any directory the system declares as a drop-in
  directory via a registry-managed list

The drop-in directory list MUST be stored in a registry
key (or equivalent file) under a security descriptor
that grants write access only to a recovery-class
operator principal, not to the package manager
principal itself. Operator configuration MAY add
entries to the list but MUST NOT remove entries
required by this specification; the list is purely
additive.

A non-official-repo package whose payload installs to one
of these paths MUST be rejected at install time.

A non-official-repo package MAY install drop-in files
under its own subdirectory of the drop-in path (e.g.,
`/etc/ld.so.conf.d/peios-<repo-name>/<package>.conf`)
provided that:

- The subdirectory is namespaced by the repository's
  name and the package's name to prevent collision.
- The package's `sd_overrides` (§3.3.5) reflect the
  intent that the subdirectory's contents are
  attributable to a specific non-official-repo
  package.
- Side-effect tools that consume the drop-in directory
  are configured to require the operator's explicit
  acknowledgement of non-official drop-ins (operational
  policy outside this specification).

> [!INFORMATIVE]
> The drop-in restriction prevents a class of attack
> where a low-trust custom repo installs a config file
> at `/etc/ld.so.conf.d/attacker.conf` that extends
> ldconfig's library search path. When a side effect
> like `ldconfig` runs at the next transaction (whether
> the next transaction is from the same repo or not),
> the drop-in is honoured and the loader's behaviour is
> influenced. Restricting top-level drop-in writes to
> the official repo, with subdirectory-namespaced
> escape hatches for legitimate non-official content,
> closes the chain.

## Variable state directories

A package MAY install empty directories under `/var/` to
establish locations its runtime will write to (e.g.,
`/var/log/<service>/`, `/var/lib/<service>/`).

A package MUST NOT install populated content under `/var/`.
Variable state is owned by the runtime, not the package.

## Permissions

Tar entry permission bits in a peipkg are distribution-format
metadata only. They do not establish access control on the
installed file. Access control is the consumer's
responsibility: on Peios, via KACS (PSD-004) applied at
file-creation time per §3.4.7; on other systems extracting
a package for inspection or migration, via that system's
native mechanism applied after extraction.

Tar entry permission bits MUST be `0777` (octal) for every
payload entry. Any other value MUST cause the package to be
rejected.

The setuid and setgid bits MUST NOT be set on payload
entries. Privilege escalation on Peios is mediated by KACS,
not by filesystem-level setuid; setuid bits are meaningless
to the access-check path and MUST NOT appear in installed
content.

> [!INFORMATIVE]
> The 0777 rule is honest signalling. A 0644 or 0755 mode in
> a peipkg would imply a permission contract that the format
> does not enforce and the Peios kernel does not consult.
> Fixing every entry to 0777, combined with uid=0/gid=0 and
> owner/group "root" (§3.1.4 #3, #4), treats payloads as
> identity-free, permission-free transport bytes. Access
> control is applied by the consumer at install time, not
> declared by the package.
>
> A consequence: extracting a peipkg with a generic tar tool
> on a non-Peios host produces world-writable files. This is
> intentional. Tooling that needs sensible host-native
> permissions on extracted files (for inspection or
> migration) is responsible for applying them after
> extraction.

## Security descriptors

Each installed file or directory has a security descriptor
as defined in PSD-004 §3.12. The package manager applies SDs
at file-creation time via the kernel's file-creation
interface (PSD-004 §11.2), not via tar attributes
(§3.1.4).

### Default: inheritance

When a payload entry has no manifest-declared SD override
(§3.3.5), the package manager MUST create the entry without
supplying an explicit SD. The kernel computes the new
entry's SD by inheritance from the parent directory's
inheritable ACEs at creation time (PSD-004 §3.6).

Inheritance is the default for the overwhelming majority of
installed entries. Most packages declare no SD overrides at
all.

### Manifest-declared overrides

When a payload entry has a corresponding entry in the
manifest's `sd_overrides` array (§3.3.5), the package
manager MUST create the entry with the explicit SD supplied
via the kernel's file-creation interface.

Overrides are appropriate when:

- A file or directory requires more restrictive permissions
  than its inherited SD provides
- A file requires explicit access for a service principal
  that does not appear in the parent directory's
  inheritable ACEs
- A directory's inheritable ACEs need to differ from those
  of its own parent (creating a new inheritance scope)

### SD override policy

KACS (PSD-004) validates the syntactic well-formedness of a
declared SD but does NOT validate that the producer of the
package had authority to declare that SD on behalf of the
SIDs it grants access to. A package can therefore declare
an SD that grants access to any service principal known to
the system. The package format treats the SD bytes as
opaque; the policy of "should this package be allowed to
declare this SD?" is enforced at install time by the
package manager, not by the kernel.

The policy applies both to *explicitly declared* SDs (via
`sd_overrides`) AND to SDs that result from inheritance
from a directory whose own SD was declared via any
package's `sd_overrides`. Specifically: when a package
extraction creates a file under a directory whose SD
was overridden by *any* `sd_overrides` declaration (the
declaring package may be from any repository), the
resulting inherited SD MUST pass the policy hook below
as if it were declared by the inheriting package. This
prevents "cross-package SD inheritance" from bypassing
the operator-confirmation gate, and explicitly closes
the edge case where a carefully-mimicked "looks-like-
default" override would have evaded a non-system-default
test.

> [!INFORMATIVE]
> Without the inheritance check, attacker package A
> could declare an SD override on a directory that
> grants the attacker rights, and victim package B's
> files installed under that directory would silently
> inherit the attacker SD without the operator ever
> being prompted. The check ensures the policy hook
> fires on *what SD ends up on the file*, regardless
> of how the SD got there.

A package manager MUST enforce a per-repository SD-override
policy:

1. Before applying any `sd_overrides` entry, the package
   manager MUST surface the override to the operator in
   human-readable form. The display MUST include the
   payload path, the SIDs and rights granted by the
   override, and a diff against what the inherited SD
   would have produced.
2. For packages from the official Peios repository, SD
   overrides MAY be applied without per-operation
   confirmation, but the operator-visible install report
   MUST list every override applied.
3. For packages from custom repositories, the package
   manager MUST require explicit operator confirmation
   before applying any `sd_overrides` entry that grants
   rights to SIDs outside a configured allowlist. The
   default allowlist contains:
   - The well-known SIDs defined by PSD-004 (SYSTEM,
     Administrators, etc.).
   - SIDs explicitly added to the per-repository
     allowlist by operator configuration.

   The default allowlist MUST NOT include any SID
   derived from the package itself (manifest fields,
   build metadata, or payload content). A package
   cannot self-elect SIDs into the allowlist; doing so
   would defeat the policy hook by letting any package
   declare its own privileged principal.
4. A package whose `sd_overrides` are rejected by the
   policy MUST be refused at install time. The package
   manager MUST NOT silently drop overrides and proceed
   with inheritance defaults.

> [!INFORMATIVE]
> The policy hook is an application-level defence against
> a class of supply-chain attack KACS does not prevent at
> the kernel level: a low-trust custom repo declaring an
> SD that grants its own service principals
> KEY_ALL_ACCESS to a system-managed file. Surfacing
> overrides to the operator at install time, and gating
> non-system-principal grants from non-official repos
> behind explicit confirmation, contains the blast
> radius without forbidding legitimate use cases (custom
> roles needing custom SDs).

### Symlinks

Symlinks do not carry independent SDs. Access to a symlink
is governed by access to its target. SD overrides MUST NOT
target symlink payload entries (§3.3.5).

### Failure handling

If file creation fails because the explicit SD is rejected
by the kernel (for example, because it references a SID
that does not exist in the system's KACS state), the
package manager MUST treat the install as failed and roll
back any partial state. The handling of failed installs
is specified in §7.

A package MUST NOT install to a parent directory whose SD
denies the package manager the access required to create
the entry. This condition is detected at install time and
treated as an install failure.

## Symlinks

Symlinks are first-class payload entries. The tar entry's
linkname is the symlink target.

### Symlink target constraints

Symlink targets MUST be relative paths.

Symlink targets MUST resolve, when joined with the
symlink's parent directory, to a path that is either
within the package's own payload tree or under one of
the permitted top-level install destinations listed in
§3.4.1. Absolute targets, and targets whose resolution
escapes §3.4.1's permitted destinations entirely (e.g.,
landing under `/tmp/`, `/home/`, `/srv/`, or `/`), are
FORBIDDEN.

> [!INFORMATIVE]
> Format-level validation cannot distinguish a symlink
> whose resolved target is a peipkg-installable path no
> peipkg actually installs (for example, a target like
> `/etc/passwd` reached via `..` traversal — `/etc/` is
> a permitted §3.4.1 destination, but `/etc/passwd` is
> typically a system-bootstrap file that no peipkg owns).
> Such targets pass format-level validation but install-
> time consumer checks (§7) detect them: a peipkg whose
> symlink resolves to a path no installed peipkg owns
> produces a dangling symlink, and a peipkg whose symlink
> would overwrite an existing system-managed file is
> rejected by collision detection (§3.4.13).

Symlink targets are subject to the same path-validity
constraints as payload paths (§3.2.7): valid UTF-8, no
NUL bytes, no ASCII control characters, no backslashes,
NFC normalisation, length limits.

A consumer MUST validate symlink targets against these
constraints before extracting the entry. A package
containing a non-conforming symlink target MUST be
rejected.

Producers MAY emit symlinks whose target resolves into a
different package's payload tree, provided the resolved
path is under §3.4.1's permitted destinations. The
canonical use case is the conventional Linux library
split, where a `-dev` package contains a developer-link
symlink (e.g. `libfoo.so`) whose target (e.g.
`libfoo.so.1`) lives in the corresponding runtime
package. Producers SHOULD declare the target's owning
package as a dependency so that the target is guaranteed
present at extraction time. The format does not require
producers to record this dependency relationship at the
symlink level; it is captured at the package level via
the `dependencies` field (§3.3.2).

> [!INFORMATIVE]
> The classic symlink TOCTOU attack — install
> `/usr/share/foo` as a symlink to `/etc/passwd`, then
> have a later write at `/usr/share/foo/bar` traverse the
> symlink — is prevented in two layers. First, the format
> forbids symlink targets that resolve outside the
> peipkg-managed tree (this section). Second, extraction
> MUST use TOCTOU-safe filesystem interfaces (§7.1.2.3) so
> even an in-tree symlink cannot redirect a later write.

> [!INFORMATIVE]
> Cross-package symlinks were considered for prohibition
> (which would have forced restructured -dev splits where
> developer links live in runtime packages instead) and
> rejected. Forbidding them would deviate from the
> universal Linux convention without a corresponding
> security gain: the TOCTOU defence above operates on
> resolved-target validity, not on whether the resolution
> crosses a package boundary. Producers and install-time
> consumers share responsibility for ensuring the target's
> owning package is co-installed; the format does not
> enforce this from inside the symlink-bearing package.

### Symlink integrity

Symlink targets are integrity-checked via the tar entry's
linkname directly during extraction. The linkname stored
in the tar header is the bytes the consumer compares; it
is not separately hashed in `files.json` because symlinks
have no content body.

## Empty directories

A package MAY install empty directories. Empty directories
are tar entries of type `directory` with no content. They
are useful for establishing required paths for runtime
state.

## Conflict prevention

Two packages MUST NOT install files at the same install
path. Such a conflict is detected at install time (§7.1)
and rejected.

A package MAY install content into a directory created by
another package; directory creation is idempotent. Conflict
applies to non-directory entries only.

## Forward compatibility with multi-architecture systems

The architecture triplet path convention (§3.4.2) is
designed so that a future multi-architecture system MAY
install packages of foreign architectures alongside native
ones without filesystem-level collisions.

In v0.22 of this specification, only one architecture's
packages may be installed on a given system at a time
(§2.3.5). The triplet path convention applies regardless,
to ensure that a v0.22-conformant package is forward-
compatible with a future multi-architecture extension.
