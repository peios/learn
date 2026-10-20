---
title: Interpreting Audit Evidence
type: how-to
description: Read access and privilege records without confusing a logged observation with authorization or complete history.
---

Use audit evidence to reconstruct a particular operation. Start with its
process instance, effective subject, object, requested rights, result, and
observation interval. Preserve the original record before translating SIDs
or event fields into display names.

## Identify the trigger

| Trigger | What the record establishes |
|---|---|
| Access audit ACE | A matching SACL rule observed an access check and outcome. |
| Continuous alarm ACE | An operation overlapped the audit mask retained on its handle. |
| Token object-access policy | The checked token required a success or failure record, even without a matching SACL ACE. |
| Privilege-use policy | A privilege contributed rights, with success or failure determined after the narrowing passes. |
| Central policy diagnostic | A SACL could not be evaluated or staged and effective policy differed. |

Audit rules do not grant or deny access. Their success and failure flags
select observations. Conditional audit expressions that are UNKNOWN use the
conservative audit behavior; ordinary conditional allow rules differ.
An inherit-only ACE is a template for children, not an immediate observation
rule on the parent.

Continuous records identify the operation-time subject, which can differ from
the opener after impersonation or descriptor transfer. Their stored audit mask
comes from the open. Changing the object's SACL does not turn every existing
handle into a fresh open with the replacement mask.

## Preserve the limits of attribution

The token ID, authentication ID, process GUID, and PID identify different
things. Resolve names as annotations; do not replace original SIDs. A process
can act with an impersonation token, and a single logon session can contain
many tokens. Cross-boot correlation needs boot context.

A userspace AccessCheck record is an advisory check of caller-supplied data,
not proof that the kernel opened that object. Its userspace-attestation marker
matters. On that syscall path, SACL-generated records require the emitter's
enabled audit privilege; token-policy and other event families have separate
rules. The [kernel audit
reference](~kernel/internals/kacs/access-check/auditing-in-accesscheck)
defines these distinctions and the [event
schemas](~kernel/internals/kacs/auditing/event-families-and-delivery)
define the fields. Absent object information must remain unknown.

Do not treat a privilege-use record as proof that removing that privilege
would have denied the operation. Backup and restore accounting can record a
contribution even where the DACL independently permits access. Maximum-access
queries also differ from concrete operation requests.

## Check delivery before drawing conclusions

A required event-construction or delivery failure can fail an audited call;
auditing is not universally best-effort. Transport buffering, loss,
persistence, retention, and query permissions are separate stages. Neither
a successful call nor an empty event query establishes a complete history.

Collect both the event and any loss or ingestion diagnostics for the same
interval. Check query scope and retention, and distinguish an inaccessible
field from an absent field. Follow the
[event evidence workflow](~peios/reading-records/saving-evidence) for collection
and the raw event catalog for schema interpretation. A sequence gap alone in
a filtered view is not proof of loss.
