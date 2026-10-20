---
title: Versions
description: The structure of a package version string — epoch, upstream version and Peios revision — and how it is parsed.
---

Every package carries a version string that identifies one build of that
package. Version strings have a defined structure and a defined
comparison order (§5.6), so that "newer" and "older" are unambiguous
across every implementation.

## Structure

```
[<epoch>:]<upstream>-<peios_revision>
```

- **Epoch** — an OPTIONAL non-negative integer, separated from the rest
  by a colon. Absent means zero.
- **Upstream** — the version the upstream project assigned, or, for
  Peios-native software, the version Peios assigned as vendor.
- **Peios revision** — a REQUIRED positive integer identifying the build
  of this upstream version produced by the distributor.

```
1.26.2-3            upstream 1.26.2, revision 3
1.26.2-rc.1-1       upstream 1.26.2-rc.1, revision 1
2:0.5.0-1           epoch 2, upstream 0.5.0, revision 1
0.22-1              upstream 0.22, revision 1 (Peios-native)
```

## Epoch

The epoch MUST be encoded as ASCII decimal digits with no leading zeros,
except that zero is encoded as the single digit `0`. The separator is a
single colon.

Epoch exists solely to override the natural ordering of upstream version
strings when an upstream regression makes a later release compare as
older than an earlier one. Bumping it SHOULD be a deliberate, documented
decision; a routine version update MUST NOT bump it.

> [!NOTE]
> An upstream project releases v2.0, abandons that line, and releases
> v0.5 as its new stable branch. Without an epoch, v0.5 compares as
> older than v2.0 and nobody on v2.0 can upgrade. Bumping the epoch to 1
> says "v0.5 in this epoch is newer than anything in epoch 0".

## Upstream version

The upstream version is everything between the optional epoch separator
and the final hyphen preceding the revision.

It MUST consist of ASCII characters drawn from: letters `a`–`z` and
`A`–`Z`, digits `0`–`9`, period `.`, plus sign `+`, hyphen `-`, and
tilde `~`. It MUST start with a digit or a letter, and MUST NOT contain
whitespace or any character outside that set.

> [!NOTE]
> The set is permissive because upstream projects format versions in
> every way imaginable: numeric (`1.26.2`), hyphenated pre-release
> (`1.0.0-rc.1`), concatenated pre-release (`16beta1`), build metadata
> (`1.0+build.42`), and tilde-separated pre-release (`1.0~rc.1`).

## Peios revision

The peios revision MUST be a positive integer encoded as ASCII decimal
digits with no leading zeros. It is incremented when the distributor
produces a new build of the same upstream version — a backported
security patch, a build-configuration change, a dependency bump, a
packaging fix.

The first revision of any upstream version MUST be `1`. Revision `0` is
reserved and MUST NOT appear in a published package.

## Parsing

A version string is parsed as follows:

1. If the string contains a colon, split at the **first** colon: what
   precedes it is the epoch, what follows is the remainder. Otherwise
   the epoch is 0 and the remainder is the whole string.
2. Split the remainder at the **last** hyphen: what follows is the peios
   revision, what precedes is the upstream version.
3. The peios revision MUST parse as a positive integer.
4. The upstream version MUST satisfy the constraints above.

A version string that does not parse is invalid, and an implementation
MUST reject it.

## Stability

The comparison algorithm of §5.6 is frozen. Any two conforming
implementations MUST produce identical comparison results for every pair
of valid version strings. An implementation that disagrees with another
on any such pair is non-conformant, whichever of the two is at fault.
