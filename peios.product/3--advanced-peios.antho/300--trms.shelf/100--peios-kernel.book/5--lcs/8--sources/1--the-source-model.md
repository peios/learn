---
title: The Source Model
description: A source is a userspace process holding registry data and answering LCS over RSI — the trust boundary, and why loregd is not special.
---

A source is a userspace process that holds registry data and answers
LCS's questions about it over the Registry Source Interface. LCS is
source-agnostic: it does not know or care how a source stores anything.

The division is the sixth semantic rule (§5.1). A source stores path
entries, key records, value entries and blanket tombstones, and returns
**all** of them on request. It does not evaluate access, resolve layers,
dispatch watches, interpret paths beyond the parent and child names it
is given, or see the identity of any caller. LCS does all of that.

A source may back several hives; a hive is backed by exactly one source
(§5.2.1).

## The interface is specified elsewhere

The RSI — its channel, framing, operations, error vocabulary, and the
obligations binding on a conforming source — is a normative
specification, because the userspace side is a role a third party can
implement. It is a chapter of PSPK, and it is where the wire format
lives.

This section covers the kernel's side: how LCS admits a source, how it
dispatches requests and accounts for them, what it refuses to believe,
and what it does when a source dies or answers late.

## The trust boundary

Sources are in the TCB. LCS trusts the data a source returns —
descriptors, values, symlink targets, key metadata — because it has no
independent copy of any of it.

A compromised source therefore has complete control over access
decisions for its hives. It can return a permissive descriptor for any
key and AccessCheck will grant access that should have been denied. LCS
validates that responses are structurally correct, but it cannot detect
data that is well-formed and wrong: a descriptor granting Everyone
`KEY_ALL_ACCESS` on a sensitive key is a perfectly valid descriptor.

Three consequences are worth naming specifically.

**Layer table poisoning.** A compromised source backing `Machine\` can
fabricate the `Precedence` and `Enabled` values under
`Machine\System\Registry\Layers\`, and so control which layer wins
every resolution contest system-wide. The `SeTcbPrivilege` check at
write time does nothing about a fabricated read.

**Layer authorization bypass.** The same source can return permissive
descriptors for layer metadata keys, granting any process write access
to any layer (§5.3.4).

**`SeRestorePrivilege` implies descriptor control.** Restore replaces a
subtree including every descriptor in it, so granting
`SeRestorePrivilege` effectively grants `WRITE_DAC` and `WRITE_OWNER`
over everything in reach of a restore. Operators should understand it
that way.

The mitigations are operational rather than architectural: sources run
with tightly scoped privileges, protected by descriptors on their
service definitions, and managed by peinit with Process Integrity
Protection where available. LCS emits audit events for every source
data validation failure. A harder guarantee — checksumming descriptors
LCS computed during inheritance and verifying them on retrieval — is
possible but not implemented.

## loregd is not special

loregd is the first source and the one that provides `Machine\` and
`Users\` at boot, which puts it on the critical path to a running
system. Nothing in LCS knows that. Its details are its own manual's
business; what LCS requires of it is exactly what it requires of any
source.
