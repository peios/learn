---
title: LCS and sources
type: how-to
description: Recognize the registryd source dependency, investigate unavailable hives, and read back state after a source failure or timed-out write.
related:
  - peios/registry-concepts/overview
  - peios/registry-layers/layers
  - peios/registry-security/access-control
  - peios/registry-administration/backup-and-restore
  - peios/registry-administration/bootstrap-and-self-configuration
  - peios/registry-advanced/transactions
  - peios/registry-advanced/private-hives-and-layers
  - peios/registry-advanced/registry-links
---

The registry depends on both the kernel's **LCS** subsystem and a userspace
**source** that persists hive data. On a standard installation, `loregd`
provides the `registryd` role and serves `Machine` and `Users`.

For ordinary configuration, use `reg` or Registry Editor. Do not edit a
source's database to bypass the registry's access checks, layer handling
or notifications.

## Which component to investigate

| Symptom or question | Start with |
|---|---|
| What is a setting and when does it apply? | `regman` and its owning component. |
| Why does a stored value lose to another? | [Layers](~peios/registry-layers/layers). |
| Why is one operation denied? | [Key and layer access](~peios/registry-security/access-control). |
| Why are a hive's reads and writes unavailable? | Its source's startup and failure diagnostics. |
| Why did a source response get rejected? | LCS events and the [validation reference](~peios/lcs/sources/validation-and-trust). |

LCS owns routing, access decisions, effective layer resolution, watches
and transaction coordination. Sources persist and return entries; each
hive has one source, and one source may serve several hives. Programs
reach the registry through LCS rather than talking directly to a source.

## The base source: registryd

`registryd` is a replaceable role, not a second daemon alongside `loregd`.
peinit starts its provider early because later services need the registry.
The default provider takes one `HiveName=DatabasePath` argument per hive;
its own startup does not depend on reading registry configuration.

The documented default database paths are
`/var/state/registry/machine.regdb` and `/var/state/registry/users.regdb`.
Inspect the deployed startup configuration before assuming those are the
paths on a particular installation. Do not launch another source against
the same databases as an exploratory repair step.

The [loregd command-line reference](~peios/loregd/startup/command-line)
covers arguments and validation. The
[loregd overview](~peios/loregd/introduction/overview) covers packaging
and its boot role. Alternative source implementations may have different
storage diagnostics.

## When a source goes away

Its hives become unavailable. Open key handles remain, but operations
requiring source access fail until it returns. Watches stay armed and
receive overflow recovery on re-registration, so consumers must re-read.

To investigate:

1. Save the exact failed operation, key and error. `reg` exit status `3`
   means access denied; `5` includes source and syscall failures. Avoid
   treating every failure as a permissions problem.
2. Check the source's diagnostic output and init-system status. For
   `loregd`, peinit relays failures before readiness to the console and
   carries buffered output into eventd once logging starts.
3. Establish why the source failed before restarting it or replacing data.
   When reads work again, re-read the affected keys and verify consumers.
4. After a timeout or source failure during a mutation, check state before
   retrying. The source may have applied it even though the caller did not
   receive success.

A transaction commit timeout is especially important: neither the timeout
nor the transaction's timed-out status proves the writes were rolled back.
See [Transactions](~peios/registry-advanced/transactions) and the
[LCS late-response reference](~peios/lcs/sources/failure-and-late-responses).

## The trust boundary

A source is part of the trusted computing base. LCS checks access using
the descriptors the source returns. It validates response structure, but
cannot detect well-formed false data, such as fabricated permissions or
layer metadata. Protect the source's service definition, privileges,
process and storage as critical system components.

Do not interpret "sources make no access decisions" as "sources need
no trust". The [LCS source model](~peios/lcs/sources/the-source-model)
explains that boundary.

## Two operations the kernel coordinates

- [Transactions](~peios/registry-advanced/transactions) group changes to one
  hive into a commit. A source must support the needed transaction mode.
- [Backup and restore](~peios/registry-administration/backup-and-restore)
  use the source's storage operations, with LCS enforcing privileges and
  the backup format. Restore replaces a subtree, including descriptors.

These are administrative interfaces; the private source protocol is not
a troubleshooting command surface.

## Where to go next

- [Registry startup and self-configuration](~peios/registry-administration/bootstrap-and-self-configuration)
- [LCS source registration and dispatch](~peios/lcs/sources/registration-and-slots)
- [Registry Source Interface specification](~peios/registry-source-interface/scope)
- [SDK guide for source authors](~peios/registry-sources/overview)
