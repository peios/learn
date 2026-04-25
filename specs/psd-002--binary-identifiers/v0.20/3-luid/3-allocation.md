---
title: Allocation
---

LUIDs MUST be allocated by the kernel.

## Uniqueness scope

Each LUID MUST be unique within a single boot session.

LUID values MUST NOT be assumed unique across reboots. A value
allocated in one boot session MAY be reused in a subsequent boot
session.

## Monotonicity

The kernel MUST allocate LUIDs in strictly monotonically increasing
order within a boot session, treating the two fields as a single
unsigned 64-bit integer (HighPart << 32 | LowPart).

The starting value of the allocation sequence after each boot is
implementation-defined.

> [!INFORMATIVE]
> Subsystems that define well-known LUID values (such as privilege
> identifiers) typically reserve values below the allocation starting
> point. The starting value should be chosen to leave room for
> current and future well-known values.

## Fabrication prohibition

Userspace code MUST NOT fabricate LUID values. All LUIDs MUST be
obtained through the kernel allocation interface or from well-known
constants defined in a Peios specification.
