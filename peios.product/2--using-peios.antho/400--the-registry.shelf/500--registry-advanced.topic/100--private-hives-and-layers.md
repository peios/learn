---
title: Private hives and layers
type: concept
description: Understand why a service or sandbox can see different registry values, and find the token and layer boundaries that govern its private view.
related:
  - peios/registry-administration/lcs-and-sources
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-concepts/overview
---

A service or sandbox can see different registry data from an administrator
looking up the same path. Before concluding that the store is inconsistent,
check whether the workload uses a private hive or private layer through
its effective thread credentials.

This page explains the diagnostic distinction. It does not provide a
command for creating private views; `reg` does not manage their attachment.
Use the workload's documented isolation mechanism and the technical
references below.

## Private hives

A private hive is visible to threads whose tokens carry its scope identity.
Private hives are considered before global hives, so a private `Machine`
can shadow the global `Machine` for that thread without changing the path.

An operator reading the global path therefore has not necessarily inspected
the workload's configuration. Identify which credentials and scope the
workload actually uses before comparing values or planning recovery.
Do not assume a global-hive backup captures a separate private hive.

## Private layers

A disabled layer can be active for a thread whose credentials name it.
It then competes using the normal precedence-and-write-order rules.
Disabling it globally does not remove it from those private views.

This is per thread, not necessarily per process: different impersonation
tokens can give threads in one process different views. Check the relevant
request or service identity rather than only the process's nominal identity.

Typical uses are session-specific overrides, test settings and sandbox
configuration. Those uses do not establish who may attach a private view.

## Authorisation lives in KACS

The token mechanism governs attachment. The kernel TRM documents scope
GUIDs and private-layer names entering credentials at token creation,
gated by `SeCreateTokenPrivilege`. That is a broad token-creation gate,
not per-scope ownership authorization.

> [!WARNING]
> Do not assume attaching a disabled high-precedence layer performs a
> separate `SeTcbPrivilege` check. The current TRM explicitly documents
> that this precedence check is absent on the attachment path. Review
> the token-creation boundary before relying on private views for isolation.

Use the [private-hive](~peios/lcs/the-data-model/private-hives) and
[private-layer](~peios/lcs/layers/private-layers) TRM sections for the
credential model and its documented limitations. Configured limits can
also reject a registry operation when the token carries too many scopes
or private layers; this is not automatically a key-permission problem.

## Where to go next

- [Effective values and layers](~peios/registry-layers/layers)
- [Key and layer permissions](~peios/registry-security/access-control)
- [Private-layer attachment and limits](~peios/lcs/layers/private-layers)
