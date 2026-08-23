---
title: Service Security Descriptors
description: A service carries two independent descriptors answering different questions — the rights, the default, the check, and hot reload.
---

A service carries two independent descriptors, and they answer different
questions.

**The registry key descriptor** on `Machine\System\Services\<name>`
controls who may read and write the service's *definition*. It is
enforced by LCS at key-open time and is not peinit's concern — peinit
reads definitions as SYSTEM.

**The ServiceSecurity descriptor** controls who may perform *runtime
operations* on the service through the control interface. It is stored
as a binary `ServiceSecurity` value on the same registry key, but
enforced by peinit rather than by LCS.

The two are genuinely independent. An administrator might be able to
query a service's status without being able to read its configuration,
or the reverse. Runtime control and configuration access are separate
concerns and there is no reason for one to imply the other.

## Access rights

| Right | Bit | Grants |
|---|---|---|
| `SERVICE_QUERY_STATUS` | 0x0001 | Query state, PID, cause, health, warnings. |
| `SERVICE_START` | 0x0002 | Start the service. |
| `SERVICE_STOP` | 0x0004 | Stop the service. |
| `SERVICE_INTERROGATE` | 0x0008 | Reload the service. |
| `SERVICE_ALL_ACCESS` | 0x000F | The union of the four. |

Restart requires `SERVICE_START` and `SERVICE_STOP` together. Reset
requires `SERVICE_STOP`, because clearing a Failed or Abandoned state is
the tail of stopping something rather than the head of starting it.

The generic mapping peinit passes to AccessCheck:

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | `SERVICE_QUERY_STATUS` |
| `GENERIC_WRITE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_EXECUTE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_ALL` | `SERVICE_ALL_ACCESS` |

## Inheritance and the default

A service whose definition carries no `ServiceSecurity` value takes the
one on `Machine\System\Services` itself. The lookup is a single step to
that key, not a walk up the hierarchy, which is exact for the flat
layout definitions actually use.

If that key has no `ServiceSecurity` either, peinit applies a built-in
default:

```
O:SY G:SY D:(A;;GA;;;SY)(A;;0x0005;;;BA)
```

SYSTEM gets full access. Administrators get `SERVICE_QUERY_STATUS` and
`SERVICE_STOP` — query and stop, but not start and not reload. The
asymmetry is deliberate: stopping something that is misbehaving is a
containment action, and starting something is a change.

## The check

When a control command arrives, peinit:

1. Takes the caller's token, captured when the connection was accepted.
2. Resolves the target service and its ServiceSecurity descriptor. A
   command naming no definition and no addressable definition-removed
   entry returns `UNKNOWN_SERVICE`; peinit does not invent a descriptor
   to check against.
3. Calls AccessCheck with the caller's token, that descriptor, the
   generic mapping above, and the right the command needs.
4. On denial, returns `ACCESS_DENIED` and records the attempt as an
   `access.denied` event carrying the caller's SID, the target, the
   requested right by name, the requested access bits and the granted
   bits.
5. On grant, proceeds.

## Hot reload

`ServiceSecurity` changes take effect on the next control request, with
no restart. A registry change notification triggers a configuration
reload, and the reload re-reads every descriptor. There is no cached
decision to invalidate — the check runs against the current descriptor
every time.

## Filtering, not denying

`list` returns only the services the caller has `SERVICE_QUERY_STATUS`
on. Services the caller cannot query are **omitted**, not denied: a
caller with no query rights anywhere receives an empty list and a
successful response. The denials are recorded as audit events rather
than surfaced to the caller, because reporting them would answer the
question the filtering exists to avoid answering.
