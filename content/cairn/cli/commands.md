---
title: CLI Commands
type: reference
order: 10
description: Complete reference for every Cairn CLI command — task management, milestones, queries, and the web server.
---

The Cairn CLI is the primary interface for automation and scripting. Every command reads from and writes to the `.cairn/` directory on disk.

## Task commands

### cairn init

Create a `.cairn/` directory in the current working directory.

```
cairn init
```

### cairn add

Create a global task or subtask.

```
cairn add "title" [flags]           # create global task
cairn add <parent-ref> "title" [flags]  # create subtask
```

**Flags:**

| Flag | Description |
|---|---|
| `--product <p>` | Categorisation tag |
| `--source <s>` | Provenance (proposal, audit, bug, idea) |
| `--spec <ref>` | Reference to authoritative document |
| `--milestone <m>` | Milestone name |
| `--priority <n>` | Integer priority (lower = higher) |
| `--depends-on <ids>` | Comma-separated task IDs |

**Examples:**

```
cairn add "Fix login bug" --product auth --priority 0
cairn add "Add caching" --milestone "v1.1" --depends-on 1,3
cairn add 1 "Write unit tests"     # subtask of task 1
```

### cairn show

Display task details including subtasks, dependencies, and docs.

```
cairn show <ref>
```

### cairn list

List tasks with optional filters.

```
cairn list [flags]
```

| Flag | Description |
|---|---|
| `--status <s>` | Filter by status (todo, active, done) |
| `--product <p>` | Filter by product |
| `--milestone <m>` | Filter by milestone |
| `--unblocked` | Only actionable tasks |
| `--blocked` | Only blocked tasks |
| `--all` | Include subtasks |

### cairn start / complete / reopen

Change a task's status.

```
cairn start <ref>       # todo -> active
cairn complete <ref>    # -> done (reports unblocked tasks)
cairn reopen <ref>      # -> todo
```

`cairn complete` scans for tasks that depended on the completed task and reports any that are now unblocked.

### cairn block / unblock

Manage dependencies.

```
cairn block <ref> --on <id> ["reason"]
cairn unblock <ref> --from <id>
```

`block` adds a dependency and optionally appends a reason to the description. `unblock` removes a dependency.

### cairn set

Update a single field.

```
cairn set <ref> <key> <value>
```

Valid keys: `title`, `status`, `description`, `product`, `source`, `spec`, `milestone`, `priority`, `order`.

### cairn describe

Set a task's description from stdin or an editor.

```
echo "Multi-line description" | cairn describe <ref>
cairn describe <ref>    # opens $EDITOR if stdin is a terminal
```

### cairn promote

Move a subtask to a new global task. Assigns a new global ID and moves the directory.

```
cairn promote <ref>
```

### cairn rm

Delete a task and all its subtasks.

```
cairn rm <ref>
```

## Query commands

### cairn status

Overview counts.

```
cairn status
```

### cairn next

List actionable tasks — unblocked and not done, sorted by priority.

```
cairn next
```

### cairn deps

Show what a task depends on and what depends on it.

```
cairn deps <ref>
```

### cairn log

Show recently updated tasks, newest first.

```
cairn log
```

## Milestone commands

### cairn milestone list / add / close / rm / show

```
cairn milestone list                    # list with task counts
cairn milestone add "name" ["desc"]     # create milestone
cairn milestone close "name"            # mark closed
cairn milestone rm "name"               # delete definition
cairn milestone show "name"             # tasks, progress, blockers
```

## Server

### cairn serve

Start the web board.

```
cairn serve [--port 3000]
```
