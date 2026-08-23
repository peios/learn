---
title: corrupt-sd
description: What FACS emits on finding a structurally invalid descriptor on a file, why it is rate-limited, and the related events that do not exist.
---

Fires when FACS encounters a structurally invalid security descriptor on
a file.

Event type string: `corrupt-sd`.

| Key | Type | Meaning |
|---|---|---|
| `subject` | map | Subject record (§2.1) for the access that triggered detection. |
| `object_context` | bin or nil | Identifier of the object whose descriptor was corrupt. |
| `reason` | string | What was wrong — `sd_too_large`, `acl_malformed`, `sid_invalid`. |
| `process` | map | Process record (§2.2). |

Every field is always present.

The subject is whoever happened to touch the file, not whoever caused
the corruption. Nothing records that.

## Rate-limited by design

One event **per inode per cache population**. A corrupt descriptor read
a thousand times during one mount's life produces one event, not a
thousand.

This is deliberate: a filesystem with many corrupt descriptors would
otherwise drown the audit stream at exactly the moment the stream is
most needed. The consequence is that event count says nothing about
access count — one event does not mean one access.

## Informational only

The kernel denies the access regardless. A corrupt descriptor fails
closed, and this event is not part of that decision — it is what tells
an administrator the corruption exists at all.

Without it, a file with a broken descriptor is simply inaccessible, with
nothing anywhere explaining why.

## Events that do not exist

Three absences in the KACS set are worth stating, because each is a
reasonable thing to look for:

- **No `logon-session-created`.** Sessions are announced only when they
  end (§3.5). Track creation through authd's own records or by polling
  `/sys/kernel/security/kacs/sessions`.
- **No `token-created`.** A token's existence is observable through
  process inspection, not through an event.
- **No periodic or heartbeat events.** Audit here is entirely
  event-driven. A silent stream means nothing happened, not that
  anything is broken.

These are intentional. The kernel's audit surface covers access
decisions and session endings; other lifecycle tracking belongs to the
layers above it.
