---
title: Security Descriptor Overrides
description: Installed files inherit their descriptor by default — how a package declares an override, and the consumer's obligation when it does.
---

Every installed file and directory carries a security descriptor. A
consumer applies it at file-creation time, through the kernel's
file-creation interface — never through a tar attribute, which §5.11
rule 5 forbids outright.

## The default is inheritance

When a payload entry has no override, a consumer MUST create the entry
without supplying an explicit security descriptor, so that the kernel
computes one by inheritance from the parent directory's inheritable
entries at creation time.

Inheritance is the default for the overwhelming majority of installed
entries, and most packages declare no overrides at all. An override is
appropriate when a file needs more restrictive access than its parent
would give it, when it needs explicit access for a principal absent from
the parent's inheritable entries, or when a directory needs to begin a
new inheritance scope.

## Declaring an override

An entry in the manifest's `sd_overrides` array has the form:

```json
{
  "path": "<payload-relative path>",
  "sd": "<base64-encoded security descriptor>"
}
```

| Field | Description |
|---|---|
| `path` | Payload-relative path, matching a tar entry exactly. |
| `sd` | Base64-encoded binary self-relative security descriptor, per RFC 4648 §4 without padding. |

The `sd_overrides` array MUST be sorted lexicographically by `path`, and
MUST NOT contain two entries with the same `path`.

`path` MUST refer to a regular-file entry or a directory entry. An
override MUST NOT target a symlink entry, which carries no independent
descriptor (§5.17).

An override referring to a non-existent payload entry, or to a symlink
entry, is invalid and MUST cause the package to be rejected.

`sd` MUST decode to a syntactically valid binary self-relative security
descriptor. One whose decoded bytes do not parse is invalid and MUST
cause the package to be rejected.

A consumer MUST perform all three of those checks — entry existence,
entry type, and descriptor parseability — before installing anything
from the package. Deferring them to the moment the descriptor is applied
turns a malformed package into a partially completed install.

## The consumer's policy obligation

The kernel validates that a declared descriptor is well-formed. It does
**not** validate that the producer of a package had any authority to
declare that descriptor on behalf of the principals it grants access to.
A package can therefore declare a descriptor granting access to any
principal the system knows about. The format treats the bytes as opaque;
whether a given package may declare a given descriptor is policy, and
that policy is the consumer's to enforce.

A consumer MUST enforce a per-repository override policy:

1. Before applying any override, the consumer MUST surface it to the
   operator in human-readable form, including the payload path, the
   principals and rights granted, and a diff against what inheritance
   would have produced.
2. For a package from the system's official repository, overrides MAY be
   applied without per-operation confirmation, but the operator-visible
   install report MUST list every override applied.
3. For a package from any other repository, the consumer MUST require
   explicit operator confirmation before applying an override that
   grants rights to a principal outside a configured allowlist. The
   default allowlist contains the well-known system principals, plus any
   principal the operator has added to that repository's allowlist. It
   MUST NOT contain any principal derived from the package itself —
   from its manifest fields, its build metadata, or its payload. A
   package cannot elect its own principals into the allowlist.
4. A package whose overrides the policy rejects MUST be refused. A
   consumer MUST NOT silently drop the overrides and proceed with
   inheritance defaults.

## Inherited descriptors are covered too

The policy applies both to explicitly declared descriptors and to
descriptors that *result from* inheritance from a directory whose own
descriptor was declared by any package's overrides.

Specifically: when installing a file under a directory whose descriptor
was overridden by any package — from any repository — the resulting
inherited descriptor MUST pass the policy as if the installing package
had declared it.

> [!NOTE]
> Without this, package A declares an override on a directory that
> grants A's author rights, and package B's files installed under that
> directory silently inherit it with the operator never prompted. The
> check fires on *what descriptor ends up on the file*, regardless of
> how it got there — which also closes the case where a
> carefully-mimicked "looks like the default" override would have
> evaded a test for non-default descriptors.

## Failure

If file creation fails because the kernel rejects the descriptor — most
often because it references a principal the system does not know — the
install MUST be treated as failed and any partial state rolled back.

A package MUST NOT be installed into a parent directory whose descriptor
denies the caller the access required to create the entry. A consumer
detects this at install time and treats it as an install failure.
