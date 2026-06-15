---
title: Pre-Exec Sequence
---

This section defines the exact sequence of operations between
"peinit decides to start service X" and "service X's binary is
running." Every step is numbered. Failure at any step is handled
explicitly.

## Cgroup tree structure

Every service runs in its own cgroup tree:

```
/sys/fs/cgroup/peinit/<cgroup-id>/         (service root)
/sys/fs/cgroup/peinit/<cgroup-id>/main/    (main process)
/sys/fs/cgroup/peinit/<cgroup-id>/hooks/   (pre/post hooks)
/sys/fs/cgroup/peinit/<cgroup-id>/health/  (health checks)
```

`<cgroup-id>` is the service name with every character outside
`[A-Za-z0-9._-]` percent-encoded (`%` followed by the byte's two
uppercase hex digits). Service names are already restricted to that
character set (§3.1), so in practice the cgroup id equals the
service name; the encoding is a defensive, **injective** guarantee
that distinct names always map to distinct, cgroup-safe ids (unlike
a plain `/`->`-` substitution, where `a/b` and `a-b` would collide).
It is internal -- the user-facing name is unchanged.

The sub-cgroup structure satisfies cgroups v2's "no internal
processes" constraint (required when controllers are active) and
provides clean containment for hooks and health checks.

### Cgroup generations

If a service's previous cgroup tree has leaked sub-cgroups (D-state
processes that survived SIGKILL -- see §4.2),
`rmdir` on the old tree will fail with EBUSY. In this case, peinit
MUST create a generational cgroup tree:
`/sys/fs/cgroup/peinit/<cgroup-id>.gen<N>/` where N increments on
each restart that requires a new tree. Old leaked trees persist
until reboot.

## Pre-start evaluation

Before running hooks or the service process, peinit MUST evaluate
conditions and asserts. For a fresh start from Inactive, this
evaluation gates the Inactive → Starting transition. If activation
has already entered Starting (for example, the start phase of a
Restart after the stop phase completed), the evaluation happens
while the service remains in Starting and gates further pre-exec
progress.

1. Read the service definition from the in-memory cache (see the
   §3.5). This read MUST NOT block
   on the registry.
2. If the service has Conditions, evaluate all of them. If any
   condition fails, the service transitions to Skipped and the
   start is abandoned. Skipped services satisfy their dependents.
3. If all conditions pass and the service has Asserts, evaluate
   all of them. If any assert fails, the service transitions to
   Failed with cause AssertionError and the start is abandoned.

Only after conditions and asserts pass may the pre-exec sequence
below continue. For a fresh Inactive start this is when the service
transitions to Starting; for an activation already in Starting,
passing checks leaves the service in Starting.

### Non-blocking evaluation

peinit MUST NOT call a blocking syscall from its event loop while
evaluating checks (§3.2):

- `registry:` checks are evaluated against the in-memory model
  (§3.5). A non-cached key is a validation error (§3.2), so this
  evaluation never reads the registry live.
- `path:`/`file:`/`directory:` checks are performed by a short-lived
  **forked helper** in a dedicated cgroup -- not by `stat()` on the
  main loop. The helper stats the service's filesystem checks and
  reports the results over a pipe; peinit waits on the helper's
  pidfd and the pipe via epoll, never blocking. The helper is
  bounded by a timeout.

If the helper does not report within the timeout (e.g. `stat()` is
wedged in uninterruptible sleep on a hung mount), peinit MUST treat
the affected checks as **not satisfied** -- a Condition skips the
service, an Assert fails it with cause AssertionError -- and
continue. peinit SIGKILLs the helper; if it survives (D-state), its
cgroup is leaked and abandoned exactly as a service process that
survives SIGKILL (§4.2). The event loop is never held up by a hung
check.

## The sequence

The service is in Starting state for the duration of this sequence.

### Step 1: Start timeout

peinit MUST start the StartTimeout timer. This timer covers the
entire remaining sequence: pre-hooks, fork/exec, and readiness
wait. If StartTimeout expires at any point during steps 2-10,
peinit MUST abort the start, kill the service's entire cgroup
tree, and transition the service to Failed with cause
ReadinessTimeout.

### Step 2: Create cgroup tree

peinit MUST create the service's cgroup tree (root, `main/`,
`hooks/`, `health/` sub-cgroups).

If cgroup creation fails, no child process exists. peinit MUST
transition the service to Failed with cause ParentSetupFailure
and return the error (including errno) to the control socket
caller.

### Step 3: Run pre-exec hooks

If ExecStartPre is configured, peinit MUST run each hook command
sequentially. Each hook is forked into the `hooks/` sub-cgroup.

For each hook, peinit MUST materialise a token at the point of
use: if HookIdentity is set, materialise a token for that identity;
otherwise, materialise a token for the service's Identity. Token
materialisation follows the rules in §3.3.
If token materialisation fails for a hook, the hook fails and the
service transitions to Failed with cause PreHookFailure.

If any hook exits non-zero, peinit MUST:

1. Kill the entire service cgroup tree (cleaning up any hook
   grandchildren).
2. Transition the service to Failed with cause PreHookFailure.

On success of all hooks, peinit MUST kill the `hooks/` sub-cgroup
to clean up any lingering hook descendants before the main process
starts.

### Step 4: Materialise service token

peinit MUST materialise the service's main process token as
defined in §3.3. For SYSTEM services, mint a token from peinit's
own SYSTEM identity (`kacs_create_token`). For all other
identities, request a token from authd. Apply RequiredPrivileges
restriction if configured.

If token materialisation fails (authd unreachable, identity not
found, KACS syscall error), no child process exists. peinit MUST
transition the service to Failed with cause ParentSetupFailure.

If token materialisation succeeds but any later parent-side setup
step fails before fork, peinit MUST close the materialised service
token fd exactly once before reporting ParentSetupFailure. A token-fd
close failure MUST be retained as cleanup evidence, but MUST NOT
change the start outcome classification.

### Step 5: Create error pipe

peinit MUST create a cloexec pipe (`pipe2(O_CLOEXEC)`). The parent
holds the read end; the child will hold the write end. This pipe
communicates pre-exec setup errors from the child back to the
parent.

If exec succeeds, the write end auto-closes (CLOEXEC) and the
parent reads EOF -- meaning setup succeeded. If any setup step
fails before exec, the child writes a structured error (step
identifier + errno) over the pipe before exiting.

The structured error payload MUST be exactly 8 bytes and MUST be
written with one `write(2)` call:

1. Bytes 0-3: little-endian `u32` child setup step identifier.
2. Bytes 4-7: little-endian `i32` positive Linux errno value.

The child MUST write at most one structured error payload: the first
reportable failed child setup step. The parent MUST treat any non-EOF
payload whose length is not exactly 8 bytes, whose step identifier is
unknown, or whose errno is less than or equal to zero as malformed
pre-exec error evidence and fail closed with cause PreExecFailure.

Child setup step identifiers are:

| Identifier | Step |
| --- | --- |
| 1 | Close read end of error pipe |
| 2 | Set service stdio (`/dev/null` stdin, stdout/stderr pipe write ends) |
| 3 | Reset signal environment |
| 4 | Install service KACS token |
| 5 | Set RLIMIT values |
| 6 | Set `oom_score_adj` |
| 7 | Set working directory |
| 8 | Set environment variables |
| 9 | Set `NOTIFY_SOCKET` |
| 10 | Inject stored file descriptors |
| 11 | Exec binary |

If `pipe2` fails, no child process exists. peinit MUST transition
the service to Failed with cause ParentSetupFailure.

### Step 6: Fork

peinit MUST fork via `clone3(CLONE_PIDFD | CLONE_INTO_CGROUP)`,
targeting the service's `main/` sub-cgroup (created in Step 2). This
atomically (a) obtains a pidfd for the child and (b) places the
child directly into `main/` at creation. There MUST be no window
where the child exists without a pidfd, and none where it runs or
execs in peinit's own cgroup before being placed.

If `clone3` fails, no child process exists. peinit MUST transition
the service to Failed with cause ParentSetupFailure. Common causes:
EMFILE/ENFILE (fd exhaustion), EAGAIN (PID limit), ENOMEM.

In the parent execution path, peinit MUST close the materialised service
token fd and its `main/` cgroup fd exactly once immediately after
`clone3` returns, whether `clone3` succeeded or failed. The child path
relies on each fd's close-on-exec flag and process exit for cleanup.
A parent token-fd or cgroup-fd close failure MUST be retained as cleanup
evidence, but MUST NOT change whether the start is classified as clone
success, clone failure, missing-pidfd failure, or pre-exec failure.

### Step 7: Parent post-fork

Immediately after fork, in the parent:

1. Close the write end of the error pipe.
2. Read from the error pipe:
   - **EOF:** exec succeeded. Record the child pidfd as the
     service's main process.
   - **Data:** pre-exec setup failed. Parse the step identifier
     and errno. Log the specific failure. Transition the service
     to Failed with cause PreExecFailure.

The child is already in the `main/` sub-cgroup -- `CLONE_INTO_CGROUP`
(Step 6) placed it there atomically at creation, so the parent
performs no post-fork cgroup move. This removes the window in which
a child could exec in peinit's cgroup, and avoids requiring the
child to write its own `cgroup.procs`, which its post-installation
token could not do.

### Step 8: Child pre-exec

In the child process. This path MUST be minimal -- no heap
allocation, no complex library calls, no logging. Straight-line
setup then exec.

1. Close the read end of the error pipe.
2. Set standard streams: redirect stdin from `/dev/null`, redirect
   stdout to the service stdout pipe write end, redirect stderr to
   the service stderr pipe write end, and close inherited pipe ends
   that are not needed after duplication.
3. Reset the signal environment: restore the signal mask to unblock
   all signals and reset every resettable signal disposition to `SIG_DFL`.
   peinit blocks all signals for its signalfd (§10.1) and the child
   inherits that mask across fork; a service MUST NOT start with
   signals blocked or with peinit's handlers installed.
4. Install the service's KACS token.
5. Set RLIMIT values (LimitNOFILE, LimitCORE) if configured.
6. Set `oom_score_adj`:
   - `-1000` (OOM-immune) for ErrorControl=Critical services.
   - `0` (default) for all others.
7. Set working directory.
8. Set environment variables (base environment + global
   `Machine\System\Init\EnvVars` values + `Environment` values from
   the definition). Global `EnvVars` override the compiled-in base
   environment; service `Environment` entries override both.
9. Set `NOTIFY_SOCKET` to the notify socket path. This is set
      unconditionally regardless of the Readiness field -- services
      use sd_notify for watchdog, STOPPING=1, FDSTORE, and
      EXTEND_TIMEOUT_USEC in addition to readiness signalling.
10. Inject stored file descriptors if the service has an fd store
   with entries from a previous run.
11. Exec the binary (`ImagePath` + `Arguments`).
12. If exec fails: write error to the pipe, `_exit(127)`.
13. If any step 1-10 fails: write error to the pipe, `_exit(126)`.

### Inherited execution context

A service MUST inherit only the execution context peinit explicitly
hands it: its stdio (the stdout/stderr pipes and the `/dev/null`
stdin -- see §12.1) and any file descriptors injected from the fd
store (sub-step 9). Every other file descriptor peinit holds -- the
control socket, the notify socket, the epoll fd, the JFS device fd,
and the registryd/authd/eventd connections -- MUST be created with
`O_CLOEXEC` (or have CLOEXEC set immediately on creation) so that it
closes automatically at exec and never leaks into a service. The
signal reset (sub-step 2) and the CLOEXEC discipline together
guarantee a service starts from a clean context, not from peinit's
privileged one.

### Step 9: Wait for readiness

After successful fork and exec:

- **Simple, Readiness=Notify:** peinit waits for `READY=1` via
  sd_notify. On receipt, the service transitions to Active.
- **Simple, Readiness=Alive:** the service transitions to Active
  immediately (the process exists).
- **Oneshot:** peinit waits for the process to exit. Exit code 0
  (or a code in SuccessExitCodes) transitions to Completed. With
  RemainAfterExit=1 the service remains in Completed; without
  RemainAfterExit it transitions Completed -> Inactive after
  dependents are released. Non-zero exit transitions to Failed.

### Step 10: Post-readiness

On readiness (Simple) or successful exit (Oneshot):

1. Run ExecStartPost commands. Each hook is forked into the
   `hooks/` sub-cgroup. Hook failure is logged but MUST NOT fail
   the service.
2. Release dependent services (they become eligible to start).
3. Start the watchdog timer if WatchdogTimeout > 0 (Simple only).
4. Start the health check timer if HealthCheck is set (Simple
   only).

## Base environment

peinit constructs each service or hook process's environment in
layers, lowest precedence first:

1. **Compiled-in base.** A fixed floor peinit always provides:

   | Variable | Value |
   |---|---|
   | `PATH` | `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin` |

2. **Global `EnvVars`.** Each value under
   `Machine\System\Init\EnvVars\` is injected as a variable (value
   name = variable name, `REG_SZ` data = value). An `EnvVars\PATH`
   value overrides the compiled-in `PATH`; other names add. Because
   this key is served by registryd, it is available only to services
   started in Phase 2: the Phase 1 / early-Phase 2 platform services
   (registryd, authd, lpsd, eventd) are launched with the
   compiled-in base only, since the registry is not yet readable
   when they start.
3. **Per-service `Environment`.** The definition's `Environment`
   values, which override layers 1-2.
4. **Protocol variables.** `NOTIFY_SOCKET` (always) and `LISTEN_FDS`
   / `LISTEN_FDNAMES` (only when stored fds are injected), set by the
   pre-exec sequence above. These have the highest precedence and
   MUST NOT be overridable by `EnvVars\` or a service's
   `Environment` -- a service overriding `NOTIFY_SOCKET` would break
   sd_notify.

A change to `EnvVars\` takes effect on a service's next start (like
the per-service `Environment` field); it is not applied to
already-running services.

peinit does NOT set `HOME`, `USER`, `LOGNAME`, `SHELL`, or `TERM`
by default. Peios identity is a KACS token (a SID), not a passwd
entry, so there is no canonical home directory or login shell to
populate; a service that needs any of these supplies it via
`EnvVars\` or its `Environment` field. peinit's own minimal startup
environment (`TERM=linux` only; see §2.1) is NOT passed through --
the environment is constructed by peinit, not inherited.

**Security.** Write access to `Machine\System\Init\EnvVars\` lets a
principal inject environment into every service peinit starts
(`LD_PRELOAD`, `LD_LIBRARY_PATH`, and the like), so it is equivalent
to compromising those services. peinit MUST NOT filter variable
names -- the key's Security Descriptor is the control boundary,
consistent with the registry's write-authority threat model. That
SD MUST NOT be permissive; the recommended default is SYSTEM full,
Administrators read-only.

## Parent-side failure summary

Steps 2, 4, 5, and 6 can fail before any child process exists.
In all four cases, peinit handles the failure entirely in the
parent:

- Clean up any partially created cgroup tree.
- Transition the service to Failed with cause ParentSetupFailure.
- Return the error (including errno) to the control socket caller.

These failures are system-level resource exhaustion (fd limits, PID
limits, memory, cgroup filesystem errors), not service-specific
failures.
