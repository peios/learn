---
title: Work Branches
type: reference
description: Task branch names, branch types, and where completed work is
  merged.
---

Feature work, fixes, and maintenance use task branches:

```text
<type>/<acta-task-number>-<brief-title>
```

The types are:

- `feat`: feature work.
- `fix`: bug fixes.
- `chore`: general maintenance.

Start a task branch from the component development or maintenance branch it
targets, and merge the completed work back there. Task branch names identify
the work rather than requiring a component prefix. Changes should be coherent
and include the relevant tests and documentation.
