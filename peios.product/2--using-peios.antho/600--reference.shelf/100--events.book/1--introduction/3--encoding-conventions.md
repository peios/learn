---
title: Encoding Conventions
description: Every payload is a msgpack map with string keys — how the recurring value types are represented, and the three event-type naming styles.
---

Every KMES payload in this book is a **msgpack map with UTF-8 string
keys**. The key set is stable per event type.

## Value representations

The same conceptual types appear across many events and are always
encoded the same way.

| Conceptual type | msgpack representation |
|---|---|
| SID | **bin** holding the binary SID, 8–68 bytes. |
| GUID | **bin**, exactly 16 bytes. |
| ACE | **bin** holding the binary ACE, copied from the descriptor. |
| Access mask | **uint**, 32-bit. |
| Boolean | **bool**. |
| Privilege name | **string**, UTF-8, e.g. `SeBackupPrivilege`. |
| Process ID | **uint**. |
| Path or name | **string**, UTF-8. |
| Timestamp | **uint**, unless an event's schema says otherwise. |
| Object context | **bin** or **nil**. An opaque caller-supplied blob; its contents are service-specific. |

Binary SIDs, GUIDs and ACEs are carried as bytes rather than as text
because they are compared as bytes. A textual SID would have to be
parsed back before it could be matched.

## Event type strings use three different styles

There is no single convention. What an event type looks like depends on
which component emits it:

| Style | Emitters | Examples |
|---|---|---|
| `kebab-case` | KACS | `access-audit`, `logon-session-destroyed` |
| `dotted.snake` | peinit, peipkg, eventd | `job.created`, `peipkg.repo-add`, `synthetic.config_change` |
| `SCREAMING_SNAKE` | StrataFS, LCS | `STRATAFS_COPY_UP`, `LCS_BACKUP_START` |

The dotted family is not internally consistent either: `peipkg.repo-add`
is dotted-then-kebab while `synthetic.config_change` is
dotted-then-snake.

This is recorded because a consumer matching event types has to know it,
not because it is defended. Match the exact strings in this book rather
than deriving one from a pattern.
