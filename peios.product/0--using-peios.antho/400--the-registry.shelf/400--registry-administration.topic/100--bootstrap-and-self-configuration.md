---
title: Registry startup and configuration
type: how-to
description: Inspect registry subsystem settings, understand startup defaults and missing-value behavior, and find early registry-source failures.
related:
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-administration/backup-and-restore
  - peios/registry-concepts/watches
  - peios/registry-administration/lcs-and-sources
  - peios/registry-layers/layers
  - peios/registry-concepts/overview
---

LCS uses compiled-in defaults at startup, then reads its settings from
`Machine\System\Registry` when the `Machine` hive becomes available.
For routine tuning, inspect and document the specific parameter before
changing it:

```sh
reg get Machine/System/Registry
regman 'Machine\System\Registry'
```

Use the [normal change-and-verification workflow](~peios/registry-concepts/configuration-and-meaning).
These parameters affect the registry itself, so keep changes narrow and
record a recovery value before modifying them.

## What startup defaults do and do not mean

The kernel's registry machinery and base layer can operate before there
is stored configuration. That does not make hives available before their
source registers. Until a source supplies a hive, a path naming it cannot
be opened.

The `registryd` role, supplied by `loregd` by default, starts early so the
rest of the system can read configuration. Its backing database paths
come from startup arguments rather than registry settings. See
[LCS and sources](~peios/registry-administration/lcs-and-sources).

## When a registry parameter change applies

LCS watches its configuration and validates changes before publishing
new operational parameters; the normal transition needs no LCS restart.
Use the parameter's manual and the
[LCS operational-parameters reference](~peios/lcs/bootstrap/operational-parameters)
for type, range and effect. That reference also describes the limits of
in-flight parameter snapshots; do not assume every ongoing operation
changes at exactly the same instant.

## It applies reject-or-keep to itself

A valid parameter is adopted. An invalid value, wrong type or missing
parameter leaves the previously active value in force, which may be the
compiled default or a previously accepted value. Values are not clamped.
The documented rejection event is `lcs.config.value.rejected`.

> [!WARNING]
> Deleting a registry tuning value is not a reliable way to reset its
> running value to the compiled default. Read the parameter documentation,
> write the intended valid value if a reset is needed, and verify the result.

Read-back shows stored data, so inspect the registry's events too. A
missing whole configuration key during first boot differs from individual
missing parameters in an existing key; the TRM describes that distinction.

## First boot, with no data

The source creates hive roots with their initial security descriptors.
LCS keeps its defaults while configuration is absent. The init system
then restores a seed containing the initial configuration; LCS notices
it, reads the settings and validates them.

For a machine that does not reach normal startup, examine the source's
early diagnostic output and the init-system failure information. With
`loregd`, peinit relays output to the console if the source fails before
readiness; after logging starts, its buffered output reaches eventd.
Do not assume missing configuration alone proves that the databases need
to be replaced or seeded again.

## Where to go next

- [Source availability and recovery checks](~peios/registry-administration/lcs-and-sources)
- [Backup and restore, including destructive replacement](~peios/registry-administration/backup-and-restore)
- [Kernel boot sequence](~peios/lcs/bootstrap/the-boot-sequence) and
  [self-watch implementation](~peios/lcs/bootstrap/the-self-watch)
