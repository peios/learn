---
title: Process lifecycle reference
type: reference
description: The precise contract for ending a process and collecting its result — exit, _exit and exit_group, the exit-status encoding, and the wait family.
related:
  - peios/threads-and-processes/process-lifecycle
  - peios/threads-and-processes/creating-processes
  - peios/security-fundamentals/tokens/lifecycle
---

This is the detailed counterpart to
[Process lifecycle](~peios/threads-and-processes/process-lifecycle). That page
explains how a process ends and is cleaned up; this one gives the exact calls — how
a process terminates, what its exit status encodes, and how a parent collects it.

## Ending a process

A process can end itself in a few ways, differing in how much tidying happens first:

| Call | What it does |
|---|---|
| `exit()` | The orderly end. Runs every handler registered with `atexit`/`on_exit` (in reverse order of registration), flushes and closes the standard I/O streams, removes temporary files, then terminates. |
| `_exit()` / `_Exit()` | The immediate end. Terminates at once — no registered handlers run and the standard I/O streams are not flushed — though open file descriptors are still closed. Used when a process must stop without running cleanup, such as a child after a failed `exec`. |
| `exit_group()` | Ends the **whole process** — every thread in it — not just the calling one. This is what ordinary termination uses: a normal `exit()`, and a return from the program's entry point, both end the entire process. |

Returning from the program's entry point is equivalent to calling `exit()` with the
returned value.

At the lowest level the raw `_exit` system call ends only the calling thread; the
library `_exit` and ordinary termination route through `exit_group` so the whole
process ends. Ending one thread while the rest of the process keeps running is the
unusual case.

A process can also be ended **from outside**, by a signal rather than by a call of
its own — covered under signals. Either way, it leaves an exit status behind.

## The exit status

When a process ends it leaves a small **exit status** for its parent to read. It
records one of two outcomes:

- **Ended on its own** — carries an exit code: the low 8 bits of the value passed to
  `exit`/`_exit` (so 0–255, with 0 conventionally meaning success).
- **Ended by a signal** — carries the number of the signal that ended it, plus a
  flag for whether the process produced a core dump.

The status is a packed value, read not directly but through a set of macros:

| Macro | Tells you |
|---|---|
| `WIFEXITED` | the process ended on its own — if so, `WEXITSTATUS` gives its exit code |
| `WIFSIGNALED` | the process was ended by a signal — if so, `WTERMSIG` gives the signal number and `WCOREDUMP` whether it dumped core |
| `WIFSTOPPED` | the process was **stopped** (not ended) by a signal — `WSTOPSIG` gives which |
| `WIFCONTINUED` | the process was resumed by a continue signal |

## Collecting the result

A parent collects a finished child's status — and in doing so clears the
[zombie](~peios/threads-and-processes/process-lifecycle) — with one of the wait
calls. They differ in which child they target and how much they report:

| Call | What it offers |
|---|---|
| `wait` | Wait for **any** child to end; return its PID and status. The simplest form. |
| `waitpid` | Wait for a chosen target (see below). Options adjust the behaviour: `WNOHANG` returns immediately if nothing is ready (a poll rather than a wait), and `WUNTRACED`/`WCONTINUED` also report children that have stopped or resumed, not only ended. |
| `waitid` | The most precise form. It can target a child by a **pidfd** (`P_PIDFD`) — the reliable handle from [Creating processes](~peios/threads-and-processes/creating-processes) — as well as by PID, by process group, or any child. It reports through a structured record (which child, and what happened: ended, killed, core-dumped, stopped, continued). Which kinds of change to wait for are chosen explicitly — `WEXITED` for children that have ended, `WSTOPPED` for those stopped by a signal, `WCONTINUED` for those resumed — and its `WNOWAIT` option peeks at the result while leaving the child collectable again later. |
| `wait4` | Like `waitpid`, and additionally returns the child's **resource usage** — processor time consumed, peak memory, and so on. |

`waitpid`'s target is chosen by a single number: a positive value waits for that
exact PID; `-1` for any child; `0` for any child in the caller's own process group;
and a value below `-1` for any child in the process group whose ID is its absolute
value.

Two further options matter for threads and other `clone`-created children, which may
not notify their parent with `SIGCHLD` the way an ordinary child does: `__WCLONE`
waits only for such clone children, and `__WALL` waits for every child regardless
of type.

## See also

- [Process lifecycle](~peios/threads-and-processes/process-lifecycle) — the conceptual counterpart to this page.
- [Process creation reference](~peios/threads-and-processes/process-creation-reference) — fork, clone, exec, and the pidfd calls.
