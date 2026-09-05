---
title: Installing and removing packages
type: how-to
description: install puts packages on the system; remove takes them off. The plan-and-confirm flow, raw installs from a local .peipkg file, and cascade removals.
related:
  - peios/package-management/overview
  - peios/package-management/keeping-a-system-current
  - peios/package-management/dependency-resolution
  - peios/package-management/transactions-and-recovery
  - peios/package-management/claims
  - peios/package-management/named-roots
---

`peipkg install` puts packages on the system; `peipkg remove` takes them off. They are the two commands you reach for most, and they share one flow — peipkg works out the full set of changes, shows it to you, and waits for your approval before touching anything.

```
$ peipkg install nginx
$ peipkg remove oldtool
```

## Installing packages

```
peipkg install <package|file.peipkg>...
```

Each argument is either the **name** of a package to fetch from a configured repository, or the **path** of a local `.peipkg` file (recognised by its `.peipkg` suffix). You can mix the two in one command.

### Canonical package names

New Peios catalogue packages use canonical reverse-DNS names. The leading
segments identify the upstream namespace and the final segment preserves the
familiar package name, even when that deliberately repeats part of the
namespace:

```
com.amd.amd-ucode
org.gnu.bash
org.sourceware.elfutils
org.peios.peinit
```

Peios-built packages of third-party software retain the upstream namespace;
Peios-owned software and Peios-specific integration packages use `org.peios`.
The name identifies the packaged software, while the repository signature and
build provenance identify who packaged it. It does not imply that upstream
signed or endorsed a downstream package.

Related payloads retain that canonical base. For example,
`org.sourceware.elfutils-libs` carries libdw and libasm,
`org.sourceware.elfutils-libelf` carries libelf, and
`org.sourceware.elfutils-devel` carries their development interfaces without
requiring the command-line tools to be installed.

The eudev family follows the same rule: `io.github.eudev-project.eudev`
contains the daemon, tools, rules and Peios service integration;
`io.github.eudev-project.eudev-libudev` contains the runtime library; and
`io.github.eudev-project.eudev-devel` contains the public header, linker name
and pkg-config metadata. Installing libudev for an application therefore does
not pull in the system device manager. The device-manager package uses
`peiosutils` for the core applets in its coldplug hook; it does not install the
GNU Coreutils bootstrap package into the running system.

FIGlet is installed as `org.figlet.figlet`. Its commands, font catalogue and
manuals form one small runtime package; detached debugging symbols and sources
use the conventional `-debuginfo` and `-debugsource` suffixes.

The file-identification command is `com.darwinsys.file`. Its libmagic ABI,
architecture-independent format database and development interface are split
as `com.darwinsys.file-libmagic`, `com.darwinsys.file-magic` and
`com.darwinsys.file-devel`, so library consumers do not acquire the command.

GNU `find` and `xargs` are installed as `org.gnu.findutils`; their manuals are
in `org.gnu.findutils-common`. The `locate` and `updatedb` tools are omitted
until Peios has a service design for maintaining their global index. Because
Peipkg normalizes POSIX ownership and mode metadata, `find` predicates such as
`-user`, `-group` and `-perm` inspect that compatibility metadata; they do not
query KACS policy and must not be used as authorization checks.

The Flex scanner generator is `io.github.westes.flex`; its `flex++` frontend
is included with the command. The independently usable libfl runtime is
`io.github.westes.flex-libs`, while `io.github.westes.flex-devel` adds the C++
header, static archive and linker name without folding those development files
into either runtime package.

GNU Awk is installed as `org.gnu.gawk` and provides both the `gawk` and `awk`
command names. Loadable extensions and the password/group lookup helpers stay
with the interpreter, reusable Awk libraries and manuals are in
`org.gnu.gawk-common`, and `org.gnu.gawk-devel` provides `gawkapi.h` for
building additional extensions. Arbitrary-precision MPFR arithmetic and
persistent arrays are enabled; interactive debugger line editing will be
enabled once the catalogue has a production Readline package.

GNU Gettext's catalog commands are installed as `org.gnu.gettext`, with
manuals, extraction rules, project templates and the commands' translated
messages in `org.gnu.gettext-common`. Project maintainers install
`org.gnu.gettext-devel` for `autopoint`, `gettextize`, the Autoconf macros and
public headers. The independently usable `libasprintf`, `libgettextpo` and
`libtextstyle` ABIs are separate runtime packages. Glibc supplies Peios's
`libintl`; Gettext therefore does not install a competing implementation,
while its commands and shell integration retain full native-language support.
Java, C#, Emacs and terminal-styling integrations are not included. The
optional `po-fetch` and AI-assisted `spit` helpers are also omitted until their
complete runtime dependencies are available as Peios packages.

GNU gperf is installed as `org.gnu.gperf`. Its generated C and C++ source has
no gperf runtime dependency, so no development or runtime-library subpackage
is needed; debugging symbols and their matching source are available through
the conventional `org.gnu.gperf-debuginfo` and `org.gnu.gperf-debugsource`
packages.

GNU GMP's C runtime is `org.gnu.gmp`; the C++ wrapper is the independently
installable `org.gnu.gmp-c++`, so C-only consumers do not acquire libstdc++.
Headers and linker names are in `org.gnu.gmp-devel`, while static archives are
in `org.gnu.gmp-static`. Builds use GMP's generic x86-64 runtime dispatch
rather than instructions selected from the package builder's CPU, so the
published libraries remain portable across Peios x86-64 systems.

GNU Grep is installed as `org.gnu.grep` and provides the `grep`, `egrep` and
`fgrep` command names. Its manuals and translated messages are in
`org.gnu.grep-common`. Basic, extended and fixed-string regular expressions
are supported; Perl-compatible `grep -P` matching is deliberately unavailable
until the catalogue has a production PCRE2 package.

GNU gzip is installed as `org.gnu.gzip`, containing `gzip`, `gunzip`, `zcat`
and `uncompress`; its manuals are in `org.gnu.gzip-common`. The optional
`org.gnu.gzip-utils` package adds the non-interactive shell helpers such as
`zgrep`, `zdiff`, `zforce`, `znew` and `gzexe` together with their declared
command dependencies. `zless` and `zmore` are omitted until the catalogue has
a pager provider, so installing the utilities never leaves unusable commands.

The Integer Set Library runtime is installed as `io.sourceforge.libisl.isl`.
Headers, the linker name and pkg-config metadata are in
`io.sourceforge.libisl.isl-devel`; the static archive and its static GMP
closure are in `io.sourceforge.libisl.isl-static`. Published builds use ISL's
portable mode rather than selecting instructions from the package builder's
CPU.

Kernel module administration commands are installed as `org.kernel.kmod`;
the independently usable libkmod runtime is `org.kernel.kmod-libs`. Headers
and pkg-config metadata are in `org.kernel.kmod-devel`, with the static archive
in `org.kernel.kmod-static`. The tools support gzip-, xz- and zstd-compressed
modules and PKCS#7 signature reporting. `depmod` is a machine-facing command
at `/libexec/depmod`; package transactions invoke it when a kernel-module
payload changes.

The Linux capabilities runtimes libcap and libpsx are installed as
`org.kernel.libcap`. Capability inspection and file-capability commands are in
`org.kernel.libcap-tools`, development interfaces in
`org.kernel.libcap-devel`, and both static archives in
`org.kernel.libcap-static`. Go and PAM integrations are not included in this
package family.

Libconfig's C runtime is installed as `io.github.hyperrealm.libconfig`; its
self-contained C++ runtime is `io.github.hyperrealm.libconfig-c++`. Headers,
linker names, pkg-config and CMake metadata for both interfaces are in
`io.github.hyperrealm.libconfig-devel`, while the static archives are in
`io.github.hyperrealm.libconfig-static`.

The libnl protocol-library family is installed as
`io.github.thom311.libnl`. Its command suite, CLI support library, dynamically
loaded traffic-control modules and lookup databases are in
`io.github.thom311.libnl-tools`. Install `io.github.thom311.libnl-devel` for
the complete public header and pkg-config surface, and
`io.github.thom311.libnl-static` for the seven static libraries.

The hardware performance-event discovery and encoding runtime is
`net.sourceforge.perfmon2.libpfm`. Its public headers, linker name and API/PMU
manuals are in `net.sourceforge.perfmon2.libpfm-devel`; the static encoder is
in `net.sourceforge.perfmon2.libpfm-static`. Python bindings are not included.

GNU Libtool's command-line tools, macros and support files are installed as
`org.gnu.libtool`. The independently usable libltdl runtime is
`org.gnu.libtool-ltdl`; its headers and linker metadata are in
`org.gnu.libtool-ltdl-devel`, with the static archive in
`org.gnu.libtool-ltdl-static`.

GNU M4 is installed as `org.gnu.m4`. The package includes the command,
localised messages and manual; matching source, debuginfo and debugsource
packages are published alongside it.

GNU Make is installed as `org.gnu.make`. Its `gnumake.h` loadable-module
interface is included with the command; Guile integration is not included.
Recipes use Peios' `/usr/bin/sh` system-shell path by default.

Meson is installed as `com.mesonbuild.meson`. The package includes the
`meson` command and manual, and declares Ninja as a runtime dependency because
Meson's normal build workflow invokes it. Meson's Python implementation is
private to the application rather than exposed as a system-wide Python
library.

GNU MPFR's shared runtime is installed as `org.gnu.mpfr`. Its public headers,
linker name and pkg-config metadata are in `org.gnu.mpfr-devel`; the static
archive and its static GMP closure are in `org.gnu.mpfr-static`. The library is
built with thread-safe storage and publishes matching source, debuginfo and
debugsource packages.

ncurses terminal-information utilities are installed as `org.gnu.ncurses`.
The wide-character ABI 6 libraries are in `org.gnu.ncurses-libs`, while the
terminal database and tabset files are in `org.gnu.ncurses-terminfo`. Headers,
linker names, pkg-config metadata and API manuals are in
`org.gnu.ncurses-devel`; static libraries are in `org.gnu.ncurses-static`.
Narrow-character, C++ and Ada compatibility surfaces are not included.

The Ninja build executor is installed as `org.ninja-build.ninja`. Its Bash and
Zsh completions, Vim syntax file, README and source manual are included with
the command. Ninja uses the system shell to execute build rules, so the
package depends on `dash`; matching source, debuginfo and debugsource packages
are published alongside it.

The numactl command suite is installed as `io.github.numactl.numactl`. The
shared libnuma runtime is `io.github.numactl.libnuma`; its headers, linker
name, pkg-config metadata and API manuals are in
`io.github.numactl.libnuma-devel`, while the static archive and its static
libatomic closure are in `io.github.numactl.libnuma-static`. Matching source,
debuginfo and debugsource packages are published alongside the family.

OpenSSL's general cryptography runtime, providers, engines and vendor
configuration are installed as `org.openssl.libcrypto`; the TLS runtime is
`org.openssl.libssl`. The `openssl` command and its user manuals are in
`org.openssl.openssl`, while certificate-management Perl utilities are in the
architecture-independent `org.openssl.openssl-perl` package. Headers, linker
names, pkg-config and CMake metadata, and API manuals are in
`org.openssl.openssl-devel`; static libraries are in
`org.openssl.openssl-static`. Package-owned configuration is stored beneath
`/usr/etc/ssl` and appears at OpenSSL's compiled `/etc/ssl` lookup path through
Peios's merged configuration view. Matching source, debuginfo and debugsource
packages are published alongside the family.

The kernel DWARF and BTF tool suite is installed as `org.kernel.pahole`. It
includes `pahole` and the accompanying dwarves inspection tools, shell
utilities and runtime data. The public libdwarves ABI is split into
`org.kernel.libdwarves`, with headers and linker names in
`org.kernel.libdwarves-devel`, so library consumers do not acquire the command
suite. Release builds use upstream's signed tarballs because those contain the
embedded libbpf sources needed for a complete build; matching source,
debuginfo and debugsource packages are published alongside the family.

The ELF metadata editor is installed as `org.nixos.patchelf`. It includes the
`patchelf` command, manual and Zsh completion, with matching source, debuginfo
and debugsource packages. The command can inspect and change an ELF object's
interpreter, run path, dynamic dependencies, SONAME and executable-stack
state. Upstream release archives are not maintainer-signed, so newly
discovered releases use an explicit HTTPS trust-on-first-use exception and
become immutable once recorded in Pekit's SHA-256 lock.

PCI inspection and configuration tools are installed as `cz.ucw.pciutils`.
It includes `lspci`, `setpci`, `pcilmr`, `update-pciids` and their manuals.
The shared libpci ABI and bundled PCI ID database are in `cz.ucw.libpci`;
headers, linker input, pkg-config metadata and the API manual are in
`cz.ucw.libpci-devel`, while the static archive is in
`cz.ucw.libpci-static`. Builds enable compressed ID files, explicit DNS
lookups, kernel-module lookup through libkmod and udev HWDB fallback. Matching
source, debuginfo and debugsource packages are published alongside the family,
using release archives authenticated by maintainer Martin Mares's OpenPGP key.

Standard network-name databases are installed as `org.debian.netbase`. The
package places the protocol, service and Ethernet-type registries in `/usr/etc`;
Peios's merged configuration view exposes those vendor defaults as
`/etc/protocols`, `/etc/services` and `/etc/ethertypes` for libc and networking
tools. The RPC registry remains part of glibc at `/usr/etc/rpc`. Locally managed
configuration can therefore override these files without modifying package
payloads. Perl's shared runtime depends on netbase because its Socket, IO and
Net::Ping modules perform named protocol and service lookups.

Perl is installed as `org.perl.perl`, which also provides the `perl` virtual
capability used by existing build dependencies. Architecture-independent core
modules are in `org.perl.perl-modules`; the shared embedding library and XS
modules are in `org.perl.libperl`; and public CORE headers and linker names are
in `org.perl.perl-devel`. Language, utility and module manuals are split into
`org.perl.perl-doc`. The threaded interpreter uses stable major.minor module
paths so a patch update does not abandon locally installed modules, and links
the catalogue's zlib and bzip2 rather than bundled copies. Crypt, GDBM and DB
extensions remain disabled until their libraries have production packages.
Matching source, debuginfo and debugsource packages are published alongside the
family. CPAN currently offers Sigstore bundles rather than a detached OpenPGP
signature Pekit can verify, so discovered releases become immutable through
their Pekit SHA-256 lock after HTTPS retrieval until Sigstore verification is
available.

For now, commands require the complete canonical name:

```
peipkg install com.amd.amd-ucode
```

References to concrete packages in package metadata likewise record complete
canonical names; virtual capability names remain unqualified. Unqualified-name
resolution may be added in future when the final component identifies exactly
one package, but it is not part of the current command contract.

Installing a package rarely means installing just that package. peipkg works out everything the request implies — the dependencies the package needs, and the dependencies of those in turn — and presents the whole set. How that set is computed is the subject of [Dependency resolution](~peios/package-management/dependency-resolution); this page is about the flow around it.

### The plan-and-confirm flow

`install`, `remove`, and the commands on [Keeping a system current](~peios/package-management/keeping-a-system-current) all work the same way. peipkg first produces a **plan** — the ordered list of changes that satisfy your request — and prints it:

```
$ peipkg install nginx
the following changes will be made:
  install    pcre2 10.44
  install    zlib 1.3.1
  install    nginx 1.27.4
proceed? [y/N]
```

Nothing has been downloaded and nothing on the system has changed. peipkg waits for an answer. Anything other than `y` or `yes` — including pressing Enter, or end-of-input — is a refusal, and the command exits having done nothing.

Answer `y` and peipkg carries the plan out as a single [transaction](~peios/package-management/transactions-and-recovery): it downloads and verifies every package, then commits the change atomically.

| Option | Effect |
|---|---|
| `--dry-run` | Produce and print the plan, then stop — never prompt, never change anything. |
| `--yes`, `-y` | Skip the `proceed?` prompt and apply the plan. |
| `--no-claim` | Install a provider without taking any claim it offers. |
| `--allow-stale` | Proceed although a repository's trust state exceeds its maximum trusted age. See [Repositories and trust](~peios/package-management/repositories-and-trust). |
| `--claim <names>` | Comma-separated claims to force-claim, overriding the current holder(s). |
| `--claim-all` | Force-claim every claim the installed packages provide, overriding incumbents. |
| `--dangerously-bypass-path-restrictions` | Permit packages that declare `special_system_package` to install outside the payload layout rules. Exempts nothing that has not declared itself special, and never reaches `/lcl/policy`. Needed only for the handful of packages whose job is to lay down the filesystem structure those rules protect. |

`--dry-run` is the safe way to see what a command would do. `--yes` is for scripts and unattended runs — but note that it skips only the routine prompt. A plan that contains an action needing deliberate authorisation will still stop and ask; `--yes` does not override that. See [Elevated authorisation](~peios/package-management/dependency-resolution) for which actions those are and why.

`--claim-all` cannot be combined with `--claim` or `--no-claim`. Claims — shared names exactly one package may hold — are covered in [Claims](~peios/package-management/claims).

An install can also target a root other than the current one — either explicitly with `--root`, or because a package declares its own default root. See [Named roots](~peios/package-management/named-roots) for how roots are named and nested.

### Installing from a local file

When an argument is a path ending in `.peipkg`, peipkg installs that file directly:

```
$ peipkg install ./nginx-1.27.4.peipkg
```

This is a **raw install**, and it differs from a repository install in one specific way: it skips the repository **trust layer**. There is no signed index to check the file against, no signing key to verify it under, and none of the freshness or rollback protection a repository provides. You are vouching for the file yourself.

Everything else still happens. The package format is fully verified: the archive structure, the manifest, the integrity manifest, and the hash of every payload file are all checked before anything is staged. A corrupt or truncated `.peipkg` is rejected in the same way as one from a repository. The file's dependencies still resolve normally against your configured repositories — a locally-installed package can pull in repository packages to satisfy what it needs.

A package supplied as an explicit local file takes precedence over any repository's version of the same package, so `install ./foo.peipkg` installs that file even if a repository offers `foo` too. In the plan, a local-file operation is marked so the choice is visible:

```
  install    nginx 1.27.4  (local file)
```

In the future, peipkg will be able to consult system policy to decide whether raw installs are permitted at all, and that gate will be configurable. For now a raw install is always allowed; the verification above is what stands behind it.

## Removing packages

```
peipkg remove <package>...
peipkg uninstall <package>...
```

`remove` and `uninstall` are the same command. Each argument names an installed package; peipkg plans the removal — the files to take off disk — and runs the plan-and-confirm flow described above.

A removal leaves shared directories in place and removes only the files the package owns. peipkg knows which files those are from its database, so a removal is clean and complete.

### Removing something that is depended on

peipkg will not, by default, leave the system inconsistent. If you ask to remove a package that another installed package depends on, the plan is refused: peipkg tells you what still needs it, and stops.

| Option | Effect |
|---|---|
| `--cascade` | Also remove every installed package that depends on the ones named. |
| `--dry-run` | Print the plan and stop. |
| `--yes`, `-y` | Skip the `proceed?` prompt. |

`--cascade` turns that refusal into a wider plan: peipkg computes the full set of packages that would be left with a broken dependency and adds them to the removal. The plan then shows everything that will be removed. Review it before approving, because a cascade can reach further than expected.

```
$ peipkg remove --cascade libfoo
the following changes will be made:
  remove     toolA 2.1
  remove     toolB 1.0
  remove     libfoo 3.3
proceed? [y/N]
```

## Exit status

| Code | Meaning |
|---|---|
| `0` | The operation succeeded — or, for `--dry-run`, the plan was produced. A declined prompt is also `0`: nothing failed. |
| `1` | The operation failed — a package was not found, a dependency could not be satisfied, a download or verification failed, or a file operation was denied. |
| `2` | A usage error — an unknown command or a malformed option. |
