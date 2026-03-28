---
title: Project Structure
type: concept
order: 30
description: How Cairn organises data on disk — the .cairn/ directory, task directories, milestones, and configuration.
---

Cairn stores everything in a `.cairn/` directory at the root of your project. There is no database — every piece of data is a file you can read, edit, or version control.

## Directory layout

```
.cairn/
  cairn.toml              # global config and ID counter
  milestones.toml         # milestone definitions
  tasks/
    1/
      meta.toml           # task 1's metadata
      docs/               # attached documents (optional)
      tasks/
        1/
          meta.toml       # subtask 1/1
        2/
          meta.toml       # subtask 1/2
    2/
      meta.toml           # task 2
    3/
      meta.toml           # task 3
```

## cairn.toml

The global config file. Currently contains only the ID counter:

```toml
[cairn]
next_id = 4
```

The `next_id` field is incremented each time a global task is created. IDs are never reused, even after deletion.

## milestones.toml

Milestone definitions, ordered by the `order` field:

```toml
[[milestone]]
name = "v1.0"
description = "First release"
order = 1
status = "open"

[[milestone]]
name = "v1.1"
description = "Polish and fixes"
order = 2
status = "open"
```

## Task directories

Each task is a directory named by its integer ID. The directory contains:

| File/Directory | Purpose |
|---|---|
| `meta.toml` | Task metadata — title, status, dependencies, etc. |
| `docs/` | Optional directory for attached documents |
| `tasks/` | Optional directory containing subtask directories |

## meta.toml

A task's metadata file:

```toml
title = "Implement login flow"
status = "active"
product = "auth"
milestone = "v1.0"
priority = 1
created = "2026-03-27"
updated = "2026-03-27"
depends_on = [3]
description = "OAuth2 flow with PKCE. Needs the session store from task 3."

[cairn]
next_subtask = 4
```

The `[cairn]` section contains tool-managed state. `next_subtask` is the counter for the next subtask ID under this task.

## Task IDs

Global tasks get IDs from the global counter in `cairn.toml`. The directory name **is** the ID — there is no ID field inside `meta.toml`.

Subtasks get locally scoped IDs from their parent's `next_subtask` counter. Subtask 1 of task 12 lives at `.cairn/tasks/12/tasks/1/meta.toml` and is addressed as `12/1`.

## Addressing tasks

Tasks are addressed by their **ref** — a slash-separated path of IDs:

| Ref | Meaning | Disk path |
|---|---|---|
| `12` | Global task 12 | `.cairn/tasks/12/meta.toml` |
| `12/1` | Subtask 1 of task 12 | `.cairn/tasks/12/tasks/1/meta.toml` |
| `12/1/5` | Sub-subtask 5 of subtask 1 of task 12 | `.cairn/tasks/12/tasks/1/tasks/5/meta.toml` |
