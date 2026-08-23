---
title: Side-Effect Declarations
description: The closed set of maintenance operations a package may request after install or removal — depmod and man-db — and how they are hardened, plus why Peios needs no shared-library cache.
---

Some standard maintenance operations must run after files are installed
or removed for a system to function: rebuilding the kernel module
dependency cache when modules change, rebuilding the man page index when
man pages are added.

These are not install scripts. **The format does not permit a package to
specify its own install script.** A package instead declares which of a
closed, enumerated set of maintenance operations it requires, and the
consumer invokes them.

## Schema

`side_effects` is an array of strings:

```json
"side_effects": ["depmod", "man-db"]
```

Each string MUST be drawn from the set below. An unknown value is
invalid and MUST cause the package to be rejected. The array MUST NOT
contain duplicates. It MAY be empty, or omitted entirely, for a package
requiring no maintenance operation.

## The recognised set

### `depmod`

Rebuilds the kernel module dependency cache for a kernel release.

A package MUST declare `depmod` if its payload contains kernel module
files (`.ko`, `.ko.*`) under `/usr/lib/modules/`. A package MUST NOT
declare it if its payload contains no kernel modules.

The consumer MUST invoke it once **per affected kernel release**, naming
that release. A package shipping modules for two releases causes two
invocations.

> [!NOTE]
> Naming the release matters more than it appears to. An invocation with
> no release operand acts on the *running* kernel, which during a kernel
> update or an image build is precisely not the kernel whose modules
> were installed — leaving that release's dependency cache unbuilt and
> its modules unloadable.

### `man-db`

Rebuilds the man page index, so that lookups by keyword are fast.

A package SHOULD declare `man-db` if its payload contains man pages
under `/usr/share/man/`.

> [!NOTE]
> `man-db` is SHOULD rather than MUST because man page lookup degrades
> gracefully without it — queries fall back to a filesystem scan. A
> package omitting it is suboptimal, not broken.

## Semantics

A side effect MUST be idempotent: running it several times in succession
MUST leave the system in the same state as running it once. The
recognised set has this property by construction.

A side effect MUST be safe to invoke non-interactively.

A consumer MUST invoke each declared side effect **once per
transaction**, after every file operation in that transaction is in
place and after the transaction has committed. Side effects MUST be
deduplicated across the packages in a transaction: several packages each
declaring `man-db` cause one invocation, not several.

A consumer MUST also invoke a side effect when a transaction *removes*
files whose absence affects that effect's target — removing a kernel
module requires `depmod`, removing a man page requires `man-db` —
whether or not any package in the transaction declared it.

## Why there is no shared-library cache

Other systems carry an `ldconfig` side effect to rebuild
`/etc/ld.so.cache`. Peios has no such cache and no such side effect, and
this is a property of the layout rather than an omission.

A cache exists to do two things: make lookup fast when the loader must
search many directories, and let it find libraries in directories it
would not otherwise search. Peios has neither problem. The C library is
configured with its library directory, its system library directory and
its runtime-loader directory all set to `/usr/lib/<triplet>`, and the
loader carries that path compiled in as its default. **There is exactly
one shared-library directory, and it is the one the loader already
searches.**

So the rule that replaces the declaration is a layout rule, and it is
normative: a package shipping a shared library MUST install it into
`/usr/lib/<triplet>`. A library installed anywhere else will not be
found, and no maintenance operation exists to make it findable.

Reintroducing a cache would mean reintroducing everything a cache brings
with it — a file to keep coherent with the filesystem, a tool in the
base to regenerate it, and a failure mode where the two disagree. That
trade is only worth making if Peios ever needs more than one library
directory.

## Ordering

Side effects are invoked in an implementation-defined order. The
recognised set is chosen so that order between distinct effects is not
significant, and a consumer MAY invoke them concurrently.

## Invocation hardening

A consumer MUST invoke a side-effect tool with:

- a **fixed absolute path** to the tool. The set is closed, so the
  consumer knows each tool's location; it MUST NOT search a path
  variable.
- a **cleared environment** containing only well-defined variables.
  Environment inherited from the invoking context MUST NOT be passed
  through.
- **standard input closed**.

> [!NOTE]
> If a consumer located the tool by searching a path variable, a package
> could shadow the intended tool through an inherited search path.
> Because the set is closed the consumer needs no configurable
> allowlist — it invokes a known path. A cleared environment closes the
> matching injection route.

A consumer MUST invoke the tool against the **installation root the
transaction acted on**, not against the root the consumer itself is
running from.

## Failure

Side effects run after the transaction commits, so a side-effect failure
does not — and cannot — roll the transaction back. A consumer MUST
report the failure to the operator; the transaction stands.

Because side effects are idempotent, a failed one is self-correcting:
re-invoking it, explicitly or as part of the next transaction that
declares it, reaches the correct state. A consumer SHOULD make
re-invocation straightforward.

> [!NOTE]
> Rolling a committed transaction back because a cache rebuild exited
> non-zero would be disproportionate: the packages installed correctly
> and only a cache lagged, recoverably.

## Extension

A future version MAY recognise further identifiers — likely candidates
include `update-mime-database`, `update-desktop-database`, and
`udev-reload`, all excluded here as irrelevant to the scope Peios is
built for. A conforming implementation of this version MUST reject a
manifest declaring any identifier outside the set above.

A future version introducing a new identifier MUST state whether it is
order-independent with respect to the existing set. An order-dependent
side effect, if one is ever added, MUST be specified with a normative
ordering relative to every other recognised effect.

## What side effects are not

- Not a general install-script mechanism. The closed enumeration is what
  prevents arbitrary code execution at install time.
- Not a way to register a service with the init system. Service
  integration belongs to the higher-level artifacts that compose
  packages.
- Not a way to seed registry state.
- Not a way to apply security descriptors, which are applied at
  file-creation time (§5.20).

A package whose required behaviour cannot be expressed through the
manifest is incomplete and cannot be installed through the package
format alone. That behaviour MUST be supplied by the higher-level
artifact that composes the package.
