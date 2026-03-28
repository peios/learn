---
title: Web Board Overview
type: concept
order: 10
description: The Cairn web board is a milestone-centric visual interface for managing tasks — drag-and-drop, inline editing, and live updates.
---

The web board is Cairn's visual interface. It runs as a local HTTP server and provides a milestone-centric view of your project.

## Starting the board

```
cairn serve
```

The board is available at `http://localhost:3000` by default. Use `--port` to change the port.

## Layout

The board displays milestones as columns, ordered left to right by release sequence. A **Backlog** column appears for tasks with no milestone or an unrecognised milestone name.

Each column shows:

- The milestone name (click to edit name, description, or close the milestone)
- A progress count (done / total)
- Task cards sorted by order, then priority, then ID

## Task cards

Each card shows the task title, ID, and metadata tags (product, priority). The left border indicates status:

| Border colour | Status |
|---|---|
| Grey | Todo |
| Blue | Active |
| Green | Done |
| Red | Blocked |

Blocked status is computed from dependencies — if any task in `depends_on` isn't done, the card shows as blocked.

## Interactions

### Editing tasks

Click a card to open the detail panel. From the panel you can:

- Change the title
- Set status (todo, active, done)
- Change milestone, product, priority, source, and spec
- Write or edit the description
- Add and remove dependencies with autocomplete search
- Add, toggle, and delete subtasks
- Delete the task

### Drag and drop

Drag cards between milestone columns to reassign milestones. Drag within a column to reorder. A blue indicator line shows where the card will land.

### Creating tasks

Click the **+ Task** button to open a create panel with the same layout as the edit panel. After creation, the panel switches to the full edit view.

### Managing milestones

Click a milestone header to edit its name, description, or close it. Drag milestone headers to reorder columns. Click **+ Milestone** at the end of the board to create a new milestone.

### Filtering

Use the header controls to filter by product, status, or hide completed tasks. Filters apply across all columns. Empty columns remain visible with a count showing how many tasks are hidden.

## Live reload

The board updates automatically when tasks change on disk. If you create or complete a task via the CLI, the board reflects the change without a manual refresh.

This is implemented with Server-Sent Events. The server polls `.cairn/` for filesystem changes and pushes notifications to the browser, which fetches fresh data and patches the DOM.
