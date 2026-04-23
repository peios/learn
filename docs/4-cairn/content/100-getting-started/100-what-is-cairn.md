---
title: What Is Cairn
type: concept
description: Cairn is a file-based project tracker with two first-class interfaces — a CLI for automation and a milestone-centric web board for visual planning.
---

Cairn is a project tracking tool built for solo developers working on large projects. It stores tasks as TOML files on disk, provides a CLI for scripting and automation, and serves a milestone-centric web board for visual planning.

## Why Cairn exists

Most project trackers are built for teams. They assume multiple users, role-based permissions, sprint ceremonies, and cloud sync. For a solo developer working on an ambitious project, that overhead adds friction without adding value.

At the other end, a plain text TODO file works until it doesn't. Once you have 50+ tasks across multiple milestones with dependencies between them, a flat list stops being useful.

Cairn fills the gap. It provides real project tracking — milestones, dependencies, priorities, subtasks — without the complexity of a team tool. Everything is a file on disk. There is no database, no server to run (except the optional web board), and no account to create.

## Two interfaces, one data model

Cairn has two primary interfaces that operate on the same `.cairn/` directory:

| Interface | Audience | Purpose |
|---|---|---|
| **CLI** | Automation, scripting, AI assistants | Create tasks, change status, query dependencies. Every operation is a single command. |
| **Web board** | The developer | Visual overview of milestones, drag-and-drop organisation, inline editing, live updates. |

The CLI and web board are peers. Changes made through either interface are immediately visible in the other. The web board uses Server-Sent Events to update live when files change on disk.

## Key concepts

**Tasks** have integer IDs, a status (todo, active, or done), and optional metadata: product, priority, milestone, dependencies, and a description. Tasks are stored as directories named by their ID, each containing a `meta.toml` file.

**Subtasks** are locally scoped within a parent task. Task 12's first subtask is addressed as `12/1`. Subtasks share the same schema as global tasks but exist as decomposition of their parent's work.

**Milestones** are ordered release targets. The web board organises tasks into columns by milestone. Tasks without a milestone appear in a Backlog column.

**Blocking is computed, not stored.** Tasks have a `depends_on` field listing the IDs of tasks they depend on. If any dependency isn't done, the task shows as blocked. There is no "blocked" status to set manually — it's derived from the dependency graph.

## How it compares

| | Cairn | GitHub Issues | Linear | Plain text |
|---|---|---|---|---|
| **Storage** | Local files | Cloud | Cloud | Local file |
| **Offline** | Yes | No | No | Yes |
| **Dependencies** | Built-in | Manual labels | Built-in | Manual |
| **Milestones** | Built-in, visual | Built-in | Cycles | Manual |
| **Subtasks** | Built-in, hierarchical | Checklists | Built-in | Manual |
| **Web board** | Built-in | Projects board | Built-in | No |
| **CLI** | Built-in | gh CLI | Linear CLI | Any editor |
| **Multi-user** | No | Yes | Yes | No |
| **Dependencies** | Zero | Internet | Internet | Zero |
