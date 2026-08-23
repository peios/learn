---
title: Dispatch and Authorisation
description: The fixed sequence a parsed command runs before it does anything — the shutdown gate, the rights checked, and what is filtered rather than denied.
---

A parsed command runs a fixed sequence before it does anything.

1. **The shutdown gate.** If peinit is shutting down, everything except
   `status`, `list` and `operation-status` is rejected. The gate runs
   before the access check, so during shutdown a caller who would have
   been denied is told the command is invalid for the current state
   rather than that they lack the right.
2. **Resolve the target.** A command naming no definition, and no
   addressable definition-removed entry, returns `UNKNOWN_SERVICE`.
   peinit does not synthesise a descriptor for something that does not
   exist.
3. **AccessCheck.** The caller's token, the target's descriptor, the
   generic mapping, and the right the command requires (§4.6, §4.7).
4. **On denial**, return `ACCESS_DENIED` and record an `access.denied`
   event carrying the caller's SID, the target, the requested right by
   name, and the access bits requested and granted. Silent denial is not
   acceptable; a denial an administrator cannot see is
   indistinguishable from a bug.
5. **On grant**, classify the command against the service's state
   (§10.3) and act.

## Rights

| Command | Right |
|---|---|
| `start` | `SERVICE_START` |
| `stop` | `SERVICE_STOP` |
| `restart` | `SERVICE_START` and `SERVICE_STOP` |
| `reload` | `SERVICE_INTERROGATE` |
| `reset` | `SERVICE_STOP` |
| `status` | `SERVICE_QUERY_STATUS` |
| `list` | Filtered per service by `SERVICE_QUERY_STATUS` |
| `operation-status` | `SERVICE_QUERY_STATUS` on the target service |
| `shutdown` | `SYSTEM_SHUTDOWN` |
| `reload-config` | `SYSTEM_RELOAD_CONFIG` |

`operation-status` resolves the operation before it checks the right, so
an unknown identifier is reported as unknown regardless of who asked.

## Filtering

`list` checks every service and partitions the result. Services the
caller can query are returned; services it cannot are omitted, and the
denials become audit events rather than anything the caller sees. A
caller with no query rights anywhere gets an empty list and a successful
response, not a denial — the filtering exists to avoid answering the
question "does this service exist", and reporting the denials would
answer it.

Definition-removed services are listed, and the list entry does not say
so. A `status` query on one does.
