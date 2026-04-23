---
title: Quick Start
type: how-to
description: Create a Cairn project, add tasks and milestones, and serve the web board in under five minutes.
---

This guide walks through creating a Cairn project from scratch, adding tasks, and viewing them on the web board.

## Prerequisites

Cairn is a Go binary. Build it from the Peios repository:

```
cd cairn && go build -o cairn .
```

## Initialise a project

Cairn stores data in a `.cairn/` directory. Create one in your project root:

```
cairn init
```

This creates `.cairn/` with a `cairn.toml` config file, `milestones.toml`, and an empty `tasks/` directory.

## Add milestones

Milestones are release targets. They become columns on the web board.

```
cairn milestone add "v1.0" "First release"
cairn milestone add "v1.1" "Polish and fixes"
```

## Add tasks

Create a task with a title. Cairn assigns an auto-incrementing integer ID.

```
cairn add "Implement login flow" --milestone "v1.0" --product auth --priority 1
```

Output: `created #1`

Add a few more:

```
cairn add "Write API documentation" --milestone "v1.0" --priority 2
cairn add "Set up CI pipeline" --milestone "v1.0" --product infra
cairn add "Add rate limiting" --milestone "v1.1" --depends-on 1
```

Task 4 depends on task 1 — it will show as blocked until task 1 is marked done.

## Add subtasks

Break a task into smaller pieces:

```
cairn add 1 "Design login form"
cairn add 1 "Implement auth API"
cairn add 1 "Add session management"
```

These are subtasks of task 1, addressed as `1/1`, `1/2`, `1/3`.

## Work on tasks

```
cairn start 1          # 1 -> active
cairn complete 1/1     # subtask done
cairn complete 1       # 1 -> done, auto-reports unblocked tasks
```

When task 1 is completed, Cairn reports that task 4 is now unblocked.

## View your project

List all tasks:

```
cairn list
```

See what's actionable right now:

```
cairn next
```

Check milestone progress:

```
cairn milestone show "v1.0"
```

## Start the web board

```
cairn serve
```

Open `http://localhost:3000` in a browser. The board shows milestones as columns with task cards. Drag tasks between milestones, click cards to edit, and create new tasks from the panel.

Changes you make via the CLI appear on the board automatically — no refresh needed.

## What's next

- Read the [CLI reference](~cairn/cli/commands) for the full command list.
- Learn about the [web board](~cairn/web-board/overview) and its features.
- See [project structure](~cairn/getting-started/project-structure) to understand the `.cairn/` directory layout.
