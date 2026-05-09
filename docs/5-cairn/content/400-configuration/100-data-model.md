---
title: Data Model
type: concept
description: The task and milestone data model — fields, statuses, dependencies, and how blocking is computed.
---

Cairn's data model is designed around two tiers of tasks and a separate milestone system.

## Task fields

Every task is stored in a `meta.toml` file with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Human-readable task name |
| `status` | enum | Yes | `todo`, `active`, or `done` |
| `product` | string | No | Categorisation tag (e.g., `auth`, `infra`) |
| `source` | string | No | Where the task came from (`proposal`, `audit`, `bug`, `idea`) |
| `spec` | string | No | Reference to authoritative document |
| `milestone` | string | No | Milestone name |
| `priority` | integer | No | Arbitrary integer, lower = higher priority |
| `order` | integer | No | Position within milestone column (sparse integers) |
| `created` | date | Yes | Creation date |
| `updated` | date | No | Last modification date |
| `depends_on` | int array | No | IDs of tasks this task depends on |
| `description` | string | No | Detailed description |

The `[cairn]` section contains tool-managed state:

| Field | Type | Description |
|---|---|---|
| `next_subtask` | integer | Counter for next subtask ID |

## Statuses

Cairn stores three statuses:

| Status | Meaning |
|---|---|
| `todo` | Not started |
| `active` | Work has begun |
| `done` | Completed |

**Blocked** is a fourth visual state, but it is never stored. A task is blocked when any ID in its `depends_on` list points to a task that is not done. The web board and CLI compute this at query time.

This means you never need to manually unblock a task. Complete the dependency and the blocked state resolves automatically.

## Global tasks vs subtasks

**Global tasks** are top-level work items. They get IDs from a global auto-incrementing counter and carry the full schema.

**Subtasks** are locally scoped within a parent. Their IDs come from the parent's `next_subtask` counter. A subtask is addressed by its full path: `12/1` means subtask 1 of task 12.

Subtasks share the same schema as global tasks. By convention, subtasks don't set `milestone` or `product` — these are implied by the parent. If set, they act as overrides.

A subtask can be promoted to a global task with `cairn promote`. This assigns a new global ID and moves the directory to the top level.

## Milestones

Milestones are defined in `milestones.toml`:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Milestone identifier |
| `description` | string | No | What this milestone delivers |
| `order` | integer | Yes | Display order on the board |
| `status` | enum | Yes | `open` or `closed` |

Tasks reference milestones by name. Tasks whose milestone name doesn't match any definition appear in the Backlog column on the web board.

## Task ordering

Tasks within a milestone have a movable order controlled by the `order` field. Values are sparse integers (e.g., 100, 200, 300) so that inserting between existing tasks doesn't require renumbering.

When dragging a card between two adjacent tasks, Cairn calculates a midpoint value. If no gap exists (consecutive integers), all tasks in that milestone are renumbered to restore sparse intervals.

Tasks without an `order` value sort to the bottom, ordered by ID.
