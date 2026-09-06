---
title: Dispatch and Authorisation
description: The fixed sequence a parsed command runs before it does anything — the shutdown gate, the rights checked, and what is filtered rather than denied.
---

A parsed command runs a fixed sequence before it does anything.

1. **The shutdown gate.** If peinit is shutting down, everything except
   `status`, `list`, `operation-status`, `job-status`, `job-list` and
   `job-stop` is rejected. [*dispatch.the-shutdown-gate] The three job
   commands stay open because a
   shutdown stops every submitted job anyway (§12.2), and an
   administrator watching that happen, or wanting a job gone sooner
   than the shutdown will manage, has a reason to ask. The gate runs
   before the access check, so during shutdown a caller who would have
   been denied is told the command is invalid for the current state
   rather than that they lack the right.
   [*dispatch.the-gate-runs-before-the-access-check]
2. **Resolve the target.** A command naming no definition, and no
   addressable definition-removed entry, returns `UNKNOWN_SERVICE`;
   one naming no submitted job peinit holds returns `UNKNOWN_JOB`.
   [*dispatch.an-unresolvable-target-is-unknown] peinit does not
   synthesise a descriptor for something that does not exist.
3. **AccessCheck.** The caller's token, the target's descriptor, the
   generic mapping, and the right the command requires (§4.6, §4.7).
   For a job the descriptor is the job's own and the mapping is the
   job mapping (§8.5). [*dispatch.the-access-check-inputs]
4. **On denial**, return `ACCESS_DENIED` and record an `access.denied`
   event — `job.access_denied` for a job — carrying the caller's SID,
   the target, the requested right by name, and the access bits
   requested and granted. [*dispatch.a-denial-is-answered-and-audited]
   Silent denial is not acceptable; a denial an
   administrator cannot see is indistinguishable from a bug.
5. **On grant**, classify the command against the service's state
   (§10.3) and act.

## Rights

| Command | Right |
|---|---|
| `start` | `SERVICE_START` [*dispatch.right-start] |
| `stop` | `SERVICE_STOP` [*dispatch.right-stop] |
| `restart` | `SERVICE_START` and `SERVICE_STOP`, requested as one mask [*dispatch.right-restart] |
| `reload` | `SERVICE_INTERROGATE` [*dispatch.right-reload] |
| `reset` | `SERVICE_STOP` [*dispatch.right-reset] |
| `status` | `SERVICE_QUERY_STATUS` [*dispatch.right-status] |
| `list` | Filtered per service by `SERVICE_QUERY_STATUS` [*dispatch.right-list] |
| `operation-status` | `SERVICE_QUERY_STATUS` on the target service [*dispatch.right-operation-status] |
| `job-status` | `JOB_QUERY` on the job [*dispatch.right-job-status] |
| `job-list` | Filtered per job by `JOB_QUERY` [*dispatch.right-job-list] |
| `job-stop` | `JOB_STOP` on the job [*dispatch.right-job-stop] |
| `shutdown` | `SYSTEM_SHUTDOWN` [*dispatch.right-shutdown] |
| `reload-config` | `SYSTEM_RELOAD_CONFIG` [*dispatch.right-reload-config] |

`operation-status` resolves the operation before it checks the right, so
an unknown identifier is reported as unknown regardless of who asked.
[*dispatch.operation-status-resolves-before-it-checks]

`job-status` and `job-stop` resolve the job first too, and for them
that is the whole story: `UNKNOWN_JOB` for an identifier that names
nothing, `ACCESS_DENIED` for one that names a job the caller may not
touch. A job identifier is unguessable, so a caller that names one was
told it by something that had it, and there is no existence to hide.
`job-stop` creates no operation; it stops the job directly (§8.5) and,
with `wait`, registers a job wait on the connection answered by the
terminal view. [*dispatch.job-stop-creates-no-operation]

## Filtering

`list` checks every service and partitions the result. Services the
caller can query are returned; services it cannot are omitted, and the
denials become audit events rather than anything the caller sees. A
caller with no query rights anywhere gets an empty list and a successful
response, not a denial [*dispatch.list-filters-rather-than-denies] — the
filtering exists to avoid answering the
question "does this service exist", and reporting the denials would
answer it.

Definition-removed services are listed, and the list entry does not say
so. A `status` query on one does.
[*dispatch.a-definition-removed-service-is-listed-without-saying-so]

`job-list` is filtered the same way. The four request filters —
`submitter`, `identity`, `logon_session`, `state` — narrow the
candidates first; each survivor is then checked for `JOB_QUERY` against
its own descriptor, the denials become `job.access_denied` events, and
the response does not say whether a filter or a right removed an entry.
[*dispatch.job-list-filters-before-it-checks]
Terminal jobs still within their retention are listed; a caller that
wants only live ones filters by `state`.
[*dispatch.terminal-jobs-within-retention-are-listed]
