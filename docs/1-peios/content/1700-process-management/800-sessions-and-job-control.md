---
title: Sessions and Job Control
type: concept
description: How processes are grouped for signal delivery, how terminal-attached process trees are bounded, and how a shell suspends and resumes pipelines.
related:
  - peios/process-management/understanding-process-creation
  - peios/process-management/process-lifecycle
  - peios/linux-compatibility/credential-projection
---

This page covers four mechanisms that together implement Unix-style terminal interaction: **process groups**, **sessions**, **controlling terminals**, and **job control**. They are mostly inherited from the substrate unchanged. The interesting Peios-specific points are the per-target access checks for group-targeted signals, the relationship between a Unix session and a KACS LogonSession (different concepts at different layers), and the fact that traditional Linux daemonisation is preserved but unnecessary on Peios.

## Four similar-sounding identifiers

Before going further: four terms come up in this area that look almost identical and identify completely different things. Disambiguating them is more useful than any single explanation that follows.

| Term | Stands for | What it identifies | Type | Layer |
|---|---|---|---|---|
| **UID** | User ID | A user (identity) | Integer | Linux ABI compatibility surface, projected from the token's user SID |
| **GID** | Group ID | A group of users (identity) | Integer | Linux ABI compatibility surface, projected from the token's primary group SID |
| **PGID** | **Process Group** ID | A group of processes (job control) | Integer (= the leader's PID) | Substrate signal delivery and terminal foreground/background management |
| **PGUID** | **Process GUID** | A specific process (Peios identity for the process itself) | UUID | KACS audit, supervision, IPC, security event records |

UID and GID are **identity** — who the process is acting as — and live entirely in the Linux compatibility layer (see [Credential projection](../linux-compatibility/credential-projection)). They are presentational; AccessCheck does not consult them.

PGID is **job control** — which signal-delivery bundle a process belongs to. It has no relationship to identity, no relationship to access control, and no relationship to KACS. The PGID happens to equal the PID of the process group leader; if process 1042 calls `setpgid()` to create a new group, every process in that group has PGID = 1042. This is purely substrate-level mechanism for shells.

PGUID is **process identity** — the Peios-native identifier for the process as a kernel object. Allocated when the process is created, never reused, used by KACS audit and IPC. The PGUID is what you see in lifecycle events, supervisor records, and per-process security state. UID changes when a token is installed; PGID changes when a shell rearranges pipelines; the PGUID never changes for the lifetime of a process.

The naming overlap (UID/GID/PGID/PGUID) is a historical accident — three different generations of Unix and Peios concepts all using the word "group" or "ID" for unrelated purposes. The distinctions are real even when the abbreviations look interchangeable.

## Process groups

A **process group** is a bundle of processes that can be signalled together. Every process belongs to exactly one process group at any time, identified by a PGID — which, by convention, is the PID of the **process group leader** (the process whose `setpgid()` call created the group).

Shells use process groups to manage pipelines. When you run `sleep 100 | grep foo`, the shell forks two children, then calls `setpgid()` to put both into a new process group whose PGID is `sleep`'s PID. Now the shell can signal the entire pipeline as a unit: `kill(-pgid, SIGINT)` reaches both children at once.

The relevant syscalls:

| Syscall | Purpose |
|---|---|
| `setpgid(pid, pgid)` | Move `pid` into process group `pgid`. With `pgid = pid`, creates a new group with `pid` as the leader. With `pgid = 0`, joins the group named by `pid`. |
| `getpgid(pid)` | Return the PGID of `pid`. |
| `setpgrp()`, `getpgrp()` | Older equivalents. `setpgrp()` is `setpgid(0, 0)`; `getpgrp()` is `getpgid(0)`. |

A process can change its own PGID or that of any of its children, with one constraint: a process cannot move into a group that lives in a different session. Process groups are containment-bounded by sessions.

## Sessions

A **session** is a collection of one or more process groups, normally corresponding to one login or one terminal-attached interactive context. A session is created by `setsid()`, which:

1. Makes the calling process the **session leader** of a new session
2. Puts the calling process into a new process group (PGID = its own PID)
3. Disassociates the calling process from any controlling terminal

Sessions are identified by a `sid` equal to the leader's PID. The session is what bounds reach for `SIGHUP` (delivered to every process in the session when the session leader dies) and what scopes job control (only the session leader can manipulate which group is foreground on the controlling terminal).

`setsid()` requires no privilege but has one constraint: the caller must not already be a process group leader. This is why traditional Unix daemonisation forks before calling `setsid()` — the fork ensures the caller is not a group leader.

## Sessions vs LogonSessions

A common point of confusion: a **Unix session** is *not* the same thing as a **KACS LogonSession**. They live at completely different layers and serve completely different purposes.

| | Unix Session | KACS LogonSession |
|---|---|---|
| What it represents | A terminal-attached process tree (or a daemon's detached "session") | An authentication context (who logged in, when, with what credentials) |
| Identifier | `sid`, equal to the session leader's PID | LUID (Locally Unique Identifier) |
| Created by | A process calling `setsid()` | authd at successful authentication |
| Lifetime | While the session leader is alive (or its descendants exist) | While any token references it |
| Bounds | `SIGHUP` reach, controlling-terminal ownership, job-control scope | Token's `auth_id`, credential lifetime |

When a user SSHes in:

1. **Authentication.** sshd calls into authd. authd creates a KACS LogonSession (LUID 1234). Every token issued for this login carries `auth_id = 1234`.
2. **Shell starts.** sshd execs the user's shell. The shell calls `setsid()`, becoming the leader of a new Unix session, and claims the pty as its controlling terminal.
3. **Inside the shell.** Process groups (one per pipeline) come and go as the shell runs commands. The Unix session persists. The KACS LogonSession persists.

The shell's token references LogonSession 1234. The shell is also the leader of a Unix session. These two facts are independent: the shell has both, and they happen to coincide for this typical login, but they are not the same object.

Counterexamples make the distinction clearer. A user who SSHes in twice gets **two LogonSessions** (two authentications) but each opens **its own Unix session** as well. A user who runs `tmux` inside their login shell creates **another Unix session** for the multiplexer — but it shares the same LogonSession (same login). A double-forking daemon detaches into a new Unix session but keeps the LogonSession of whoever started it.

The slogan: **LogonSession = "who", Unix Session = "where"**. KACS owns identity; the substrate owns terminal-attached process trees.

## Controlling terminals

Most Unix sessions have a **controlling terminal** — a tty (`/dev/tty1`, `/dev/pts/0`, etc.) bound to the session for input and signal delivery. The kernel routes keyboard input to the foreground process group on this tty, generates `SIGINT` / `SIGTSTP` / `SIGQUIT` from special characters (`^C` / `^Z` / `^\`), and dispatches `SIGHUP` to the entire session when the line drops.

A session leader acquires a controlling terminal by opening a tty without `O_NOCTTY`, or explicitly via `ioctl(fd, TIOCSCTTY)`. The constraints:

- A session has at most one controlling terminal.
- A terminal has at most one controlling session.
- Only the session leader can claim a tty as controlling.
- The tty must not already be controlling for another session.

`ioctl(fd, TIOCNOTTY)` releases the controlling terminal — used by daemons that want to dissociate themselves from any tty. After release, the session has no controlling terminal and the kernel will not deliver tty-driven signals to any of its members.

The **foreground process group** of a controlling terminal is the group that receives keyboard input and signals from special characters. It is set by `tcsetpgrp(fd, pgid)` and read by `tcgetpgrp(fd)`. Both calls require the caller to be in the same session as the terminal; `tcsetpgrp` additionally requires the target PGID to be a process group within the same session.

A background process group whose member tries to read from the controlling terminal receives `SIGTTIN`; tries to write (with the relevant termios setting) receives `SIGTTOU`. The default action of both is to stop the process. This is what makes background jobs notice they are background.

## Job control

**Job control** is the mechanism by which a shell suspends and resumes process groups within its session. The pieces:

| Action | Mechanism |
|---|---|
| User types `^C` | Kernel sends `SIGINT` to the foreground process group |
| User types `^Z` | Kernel sends `SIGTSTP` to the foreground process group; group stops |
| Shell command `bg` | Shell sends `SIGCONT` to the stopped group; it resumes in background |
| Shell command `fg` | Shell calls `tcsetpgrp` to make the group foreground, then sends `SIGCONT` |
| Background group reads tty | Kernel sends `SIGTTIN`; group stops |
| Background group writes tty (with TOSTOP) | Kernel sends `SIGTTOU`; group stops |

`SIGCONT` resumes a stopped group regardless of which signal stopped it (`SIGSTOP`, `SIGTSTP`, `SIGTTIN`, `SIGTTOU`). It is unblockable — even a process that has masked all other signals will resume on `SIGCONT`. Sending `SIGCONT` to an already-running group has no effect.

## Signal delivery to process groups

Sending a signal to a process group with `kill(-pgid, sig)` requests delivery to every member of the group. Peios diverges from Linux here in one respect: **each delivery goes through its own AccessCheck.**

Linux uses a "one-is-enough" model: if the sender has permission to signal at least one member of the group, the signal is delivered to every member. This is a longstanding quirk that occasionally allows an unprivileged sender to signal a privileged target through a shared process group.

Peios checks each target individually using the target's process security descriptor (`PROCESS_SIGNAL` or `PROCESS_TERMINATE` depending on the signal) and the PIP dominance check. Members the sender is allowed to signal receive the signal; members it isn't allowed to signal don't. The signal is silently skipped for denied targets — there is no aggregate failure code, because partial delivery is the meaningful outcome.

In practice this almost never matters for legitimate workloads — process group members are normally at the same trust level (a shell's pipeline children all share the user's identity). The deviation matters in adversarial cases that the security model wants to defend against anyway.

## Kernel-originated signals

Some job-control signals are sent by the kernel itself rather than by a userspace process: `SIGHUP` to a session when its leader dies, `SIGTTIN` / `SIGTTOU` to background groups attempting tty I/O, `SIGCONT` semantics for the special-character path, and so on.

These are exempt from AccessCheck. The kernel is the originator, not a userspace token; there is no caller to check against the target's SD, and PIP dominance is moot because the kernel runs at the highest possible trust. Subjecting kernel-originated signals to AccessCheck would either require fabricating a synthetic sender or breaking job control entirely. Neither is the right answer.

The exemption is narrow: it applies only to signals the kernel itself originates as part of session/terminal machinery. A userspace process invoking `kill(-pgid, SIGHUP)` is still subject to per-target AccessCheck, just like any other userspace-originated signal.

## Traditional Unix daemonisation

The standard pattern for a Linux process to detach from its controlling terminal and become a background daemon is:

1. `fork()` — the parent exits, leaving the child without a process group leader status.
2. `setsid()` — the child becomes a session leader of a new session, with no controlling terminal.
3. `fork()` again — the grandchild is no longer a session leader, so it can never reacquire a controlling terminal.
4. `chdir("/")`, close file descriptors, redirect stdin/stdout/stderr to `/dev/null`.

This sequence still works on Peios — every syscall in it is a substrate primitive that operates exactly as it does on Linux. Existing Linux daemons that perform this dance run without modification.

It is, however, **unnecessary for Peios-native services**. peinit launches services with a clean environment by design: no inherited controlling terminal, no inherited session, file descriptors set up correctly, working directory chosen explicitly. The whole point of having a structured supervisor is that services do not need to perform the daemonisation dance themselves; they start in the environment they need.

The substrate continues to support traditional daemonisation for the benefit of unmodified Linux software. Peios-native services should not use it — calling `setsid()` and double-forking when peinit has already arranged a clean environment is just adding moving parts.
