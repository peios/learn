---
title: Access Decisions
description: Every access decision is recorded by the kernel's audit, including a daemon's about objects it guards — the audit context a component passes, asserted fields, default SACLs on guarded objects, and keeping those SACLs intact.
---

Every access decision is recorded the same way: by the kernel's access
audit, under the SACL of the object decided on. That holds for a decision
a userspace component makes about objects it guards itself — a service
manager's services, an event store's namespaces — as much as for a file.
"Who was refused what" is then one query, and a SACL governs a daemon's
objects as it governs a file.

## A component that guards objects

An emitter that decides access to objects of its own:

- MUST make each decision through the kernel's access check, against the
  object's security descriptor;
- MUST pass the object's identity as the check's audit context (below);
- MUST NOT write an event of its own recording the decision, whether it
  granted or refused. It MAY write a log line about a refusal for its own
  debugging; that line is not the audit record.

## The audit context

The audit context is one MessagePack map:

| Key | Value |
|---|---|
| `kind` | The kind of object, a kebab-case string: `service`, `job` |
| `<kind>` | Optional. A map of the object's identifying fields, under a key equal to the value of `kind` |

```text
{kind: "service", service: {name: "jellyfin"}}
```

The map MUST contain `kind`, MAY contain the map named by it, and MUST
contain nothing else. The kernel rejects a context that is not exactly
this shape: `kind` must be a string matching the segment grammar of
§6.3, the map under the kind's key must not be empty, and every key in
that map must match the same grammar, because each becomes a segment of
`object.<kind>.<key>`. A context with no body map is accepted; an empty
body map is not. Each field in that map MUST be a field the
component's fragment defines beneath `object.<kind>`, and MUST be marked
asserted there (§6.10).

The kernel's record of the decision then carries `object.kind` and the
object's fields as `object.service.name` and so on, beside the subject,
the access requested and granted, and the trigger, exactly as for any
other object. How the kernel's access-check interface accepts and copies
the context is described in the Peios Kernel TRM.

## Asserted fields

The kernel cannot verify that a descriptor belongs to the service a
component names. A field the kernel copies from userspace is therefore
the component's claim: it is the identity of what the component actually
enforced, but the kernel did not observe it.

A kernel-originated record that carries any asserted value MUST carry
`fields.attestation.userspace` with the value `true`. A record that
carries none MUST omit the field. A record written by userspace never
carries it, because the origin class in its header (§6.4) already says
that the whole payload is the emitter's word.

A consumer MUST NOT present an asserted field as observed by the kernel.

## The emitter and the subject

On a decision a component requests for a client, the record's header
names the component, as `emitter.*`, and the payload's `subject.*` names
the client whose access was checked (§6.4). The component's process
details are `emitter.process.*`.

## Default SACLs

A component that guards objects SHOULD give each a default SACL with an
audit ACE that records failed access by Everyone, so that a refusal is
recorded without configuration. An administrator can narrow or remove it
per object like any other SACL. The exception is a kind of object so
numerous that recording every refusal would bury the record, which is
why files and registry keys carry no default SACL.

A component that stores a descriptor where writing the stored value
replaces the SACL without the privilege that normally guards a SACL —
for example, a whole descriptor kept as one registry value — MUST allow
that store to be written only by principals trusted to change audit
policy. A tool that edits such a descriptor's DACL MUST keep its SACL
intact.

> [!NOTE]
> Two other ways of recording refusals were considered. Adding a SACL to
> every descriptor just before the check would make the record's
> `trigger.ace` name an ACE that is not in the object's descriptor, could
> not be changed per object, and would be done differently by every
> component. Turning on failure auditing in every token's audit policy
> would record every refusal on every object, files included; that
> remains the tool for auditing everything one principal does.
