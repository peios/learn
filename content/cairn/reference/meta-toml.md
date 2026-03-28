---
title: meta.toml Reference
type: reference
order: 10
description: Complete field reference for task meta.toml files.
---

Every task directory contains a `meta.toml` file. This is the complete field reference.

## Example

```toml
title = "Implement login flow"
status = "active"
product = "auth"
source = "proposal"
spec = "auth-proposal.md S3.2"
milestone = "v1.0"
priority = 1
order = 200
created = "2026-03-27"
updated = "2026-03-27"
depends_on = [3, 5]
description = """
OAuth2 flow with PKCE.
Needs the session store from task 3 and the user model from task 5.
"""

[cairn]
next_subtask = 4
```

## Fields

### title (required)

Human-readable task name. Set at creation, editable via `cairn set` or the web board.

### status (required)

One of `todo`, `active`, or `done`. Set via `cairn start`, `cairn complete`, `cairn reopen`, or `cairn set`.

### product

Free-form categorisation string. Used for filtering on the CLI (`--product`) and web board. Examples: `auth`, `infra`, `pkm`.

### source

Where the task originated. Common values: `proposal`, `audit`, `bug`, `idea`. Used for filtering.

### spec

Reference to an authoritative document. Typically a proposal section reference like `KACS.md S8.1`.

### milestone

Name of a milestone defined in `milestones.toml`. Determines which column the task appears in on the web board. If the name doesn't match any defined milestone, the task appears in Backlog.

### priority

Arbitrary integer. Lower values indicate higher priority. Used for sorting in `cairn next` and within milestone columns. Tasks without a priority sort after those with one.

### order

Integer controlling position within a milestone column on the web board. Sparse values (100, 200, 300) allow insertion. Managed primarily by drag-and-drop on the board. Tasks without an order sort to the bottom by ID.

### created

Date string in `YYYY-MM-DD` format. Set automatically at creation time.

### updated

Date string in `YYYY-MM-DD` format. Set automatically when any field changes.

### depends_on

Array of global task IDs. If any referenced task is not `done`, this task is computed as blocked.

### description

Free-form text. Can contain multiple lines. Set via `cairn describe` (stdin or editor) or the web board.

### [cairn] section

Tool-managed state. Do not edit manually unless you know what you're doing.

**next_subtask**: The next integer ID to assign when creating a subtask under this task. Incremented on each subtask creation, never reused.
