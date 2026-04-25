---
title: Terminology
---

- **GUID** (Globally Unique Identifier): A 128-bit identifier with
  global uniqueness guarantees. Used to identify registry hives,
  layers, object types, and other entities that require stable
  identity across systems and reboots.

- **LUID** (Locally Unique Identifier): A 64-bit identifier with
  boot-scoped local uniqueness. Used to identify transient entities
  such as logon sessions and privilege instances that do not persist
  across reboots.

- **Nil GUID**: The GUID with all 128 bits set to zero. A sentinel
  value meaning "no GUID" or "unset."

- **Nil LUID**: The LUID with all 64 bits set to zero. A sentinel
  value meaning "no LUID" or "unset."
