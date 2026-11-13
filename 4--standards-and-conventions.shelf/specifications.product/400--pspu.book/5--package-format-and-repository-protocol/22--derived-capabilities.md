---
title: Derived Capabilities
description: The requirements and provides a producer derives from a package's ELF objects, sonames and symbol-version floors, and how they join what it was told.
---

A producer reads each ELF object among a package's files and adds to the
manifest what it needs and provides. Derivation is the producer's job, done
once when the package is packed: a consumer doesn't read a package's files
to find what it needs.

## Sonames

An object's `DT_NEEDED` sonames become requirements, for any version, and
its `DT_SONAME` becomes a capability the package provides. A soname the
package provides is not also required.

Files under `src/`, which hold source rather than installed objects, are not
read, nor are symbolic links, which alias an object packed at its own path.
Files that are not ELF are passed over.

## Symbol-version floors

For the glibc libraries, `ld-linux-x86-64.so.2`, `libanl.so.1`,
`libc.so.6`, `libdl.so.2`, `libm.so.6`, `libmvec.so.1`, `libnsl.so.1`,
`libpthread.so.0`, `libresolv.so.2`, `librt.so.1` and `libutil.so.1`, and
for `libgcc_s.so.1`, whose symbol versions are numbered as their package
is, the highest symbol version an object needs is a floor: an object
needing `GLIBC_2.34` of `libc.so.6` gives the requirement
`libc.so.6 >= 2.34`. A package that provides one of these libraries provides
it at its own version.

The versions of `libstdc++.so.6` are not numbered as gcc is, so each is an
exact capability instead, `elfver(libstdc++.so.6:<version>)`. A package
providing `libstdc++.so.6` provides each version it defines, and an object
needing a version requires it, unless the need is weak.

## Joining what the producer was told

What derivation finds joins what the producer was given. Where both name one
capability, the given entry is kept, unless it gives no version or holds for
any version, when the derived one is. A given requirement on one of the
floor libraries for anything but any version MUST be refused, because its
floor comes only from the payload, and so MUST a given provide of one at a
version other than the package's.

An object that can't be read, or whose version tables are inconsistent, is
an error, and so is a package providing `libstdc++.so.6` that needs a
version of it that it doesn't define. The same files MUST give the same
requirements and provides.
