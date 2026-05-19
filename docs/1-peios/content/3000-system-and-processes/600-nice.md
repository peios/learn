---
title: nice
type: reference
description: Run a command at an adjusted scheduling priority.
related:
  - peios/system-and-processes/overview
---

`nice` runs a command at an adjusted **scheduling priority** — making it more, or less, willing to give the processor up to other work.

```
nice [option] [command [arg]...]
```

```
$ nice -n 15 big-batch-job
```

With no command, `nice` prints the current niceness.

## Niceness

A process has a *niceness* — a number from **-20** to **19**:

- A **high** niceness (toward 19) means the process is "nicer" to others — it yields the processor readily. Good for background work that should not get in the way.
- A **low** niceness (toward -20) means the process is favoured — it gets the processor more often.

By default `nice` adds **10** to the niceness, making the command run in the background more gracefully.

| Option | Effect |
|---|---|
| `-n`, `--adjustment=N` | Add `N` to the niceness instead of 10. `N` may be negative. |

Raising a command's niceness — running it *lower* priority — is always allowed. Lowering the niceness, to claim a *higher* priority than normal, is a privileged request and may be refused; when it is, `nice` warns and runs the command at the priority it was permitted.

## Exit status

`nice` exits with the command's own status. If no command is given, it prints the niceness and exits `0`. A `nice`-level failure — a bad adjustment value, or a command that could not be run — exits `125`, `126`, or `127`.
