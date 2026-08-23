---
title: The Control Descriptor
description: Shutdown and configuration reload are checked against peinit's own descriptor rather than any service's.
---

Two operations are not about any one service: shutting the system down,
and re-reading the configuration. They are checked against peinit's own
descriptor, stored at `Machine\System\Init\ControlSecurity` as a binary
value.

## Access rights

| Right | Bit | Grants |
|---|---|---|
| `SYSTEM_SHUTDOWN` | 0x0001 | Initiate poweroff, reboot or halt. |
| `SYSTEM_RELOAD_CONFIG` | 0x0002 | Re-read all definitions from the registry. |

The generic mapping:

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | nothing |
| `GENERIC_WRITE` | `SYSTEM_RELOAD_CONFIG` |
| `GENERIC_EXECUTE` | `SYSTEM_SHUTDOWN` |
| `GENERIC_ALL` | both |

`GENERIC_READ` maps to nothing because there is nothing to read: the
control descriptor governs two actions and no queries. A grant of
`GENERIC_READ` on it is not an error, it simply conveys no access.

## The default

Absent a value in the registry, peinit applies:

```
O:SY G:BA D:(A;;0x0003;;;SY)(A;;0x0003;;;BA)
```

SYSTEM and Administrators both get shutdown and reload-config. Unlike
the ServiceSecurity default, this one is symmetric — an administrator
who can stop services one at a time can already stop the system, so
withholding shutdown would be theatre.

## Loading

peinit loads the descriptor during Phase 2 boot and hot-reloads it on
registry change notification, on the same path as the service
descriptors. Until it is loaded — during Phase 1 and the early part of
Phase 2 — the built-in default applies, which matters because the
control socket exists from Phase 1 infrastructure setup onwards.
