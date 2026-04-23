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

`<cgroup-id>` is the service name with `/` replaced by `-` (e.g.,
`mount:/data` becomes `mount:-data`). This escaping is internal --
the user-facing name is unchanged.

The sub-cgroup structure satisfies cgroups v2's "no internal
processes" constraint (required when controllers are active) and
provides clean containment for hooks and health checks.

### Cgroup generations

If a service's previous cgroup tree has leaked sub-cgroups (D-state
processes that survived SIGKILL -- see the Health Checks section),
`rmdir` on the old tree will fail with EBUSY. In this case, peinit
MUST create a generational cgroup tree:
`/sys/fs/cgroup/peinit/<cgroup-id>.gen<N>/` where N increments on
each restart that requires a new tree. Old leaked trees persist
until reboot.

## Pre-start evaluation

Before entering the pre-exec sequence, peinit MUST evaluate
conditions and asserts while the service is still in Inactive
state. This evaluation gates the Inactive → Starting transition.

1. Read the service definition from the in-memory cache (see the
   Configuration Generations section). This read MUST NOT block
   on the registry.
2. If the service has Conditions, evaluate all of them. If any
   condition fails, the service transitions to Skipped and the
   start is abandoned. Skipped services satisfy their dependents.
3. If all conditions pass and the service has Asserts, evaluate
   all of them. If any assert fails, the service transitions to
   Failed with cause AssertionError and the start is abandoned.

Only after conditions and asserts pass does the service transition
to Starting and the pre-exec sequence below begins.

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
materialisation follows the rules in the Service Identity section.
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
defined in the Service Identity section. For SYSTEM services,
clone peinit's token. For all other identities, request a token
from authd. Apply RequiredPrivileges restriction if configured.

If token materialisation fails (authd unreachable, identity not
found, KACS syscall error), no child process exists. peinit MUST
transition the service to Failed with cause ParentSetupFailure.

### Step 5: Create error pipe

peinit MUST create a cloexec pipe (`pipe2(O_CLOEXEC)`). The parent
holds the read end; the child will hold the write end. This pipe
communicates pre-exec setup errors from the child back to the
parent.

If exec succeeds, the write end auto-closes (CLOEXEC) and the
parent reads EOF -- meaning setup succeeded. If any setup step
fails before exec, the child writes a structured error (step
identifier + errno) over the pipe before exiting.

If `pipe2` fails, no child process exists. peinit MUST transition
the service to Failed with cause ParentSetupFailure.

### Step 6: Fork

peinit MUST fork via `clone3(CLONE_PIDFD)` to atomically obtain
a pidfd for the child. There MUST be no window where the child
exists without a pidfd.

If `clone3` fails, no child process exists. peinit MUST transition
the service to Failed with cause ParentSetupFailure. Common causes:
EMFILE/ENFILE (fd exhaustion), EAGAIN (PID limit), ENOMEM.

### Step 7: Parent post-fork

Immediately after fork, in the parent:

1. Move the child into the `main/` sub-cgroup by writing the child
   PID to `main/cgroup.procs`. The parent does this -- not the
   child -- because cgroup writes require SYSTEM privileges that
   the child's token will not carry after token installation.
2. Close the write end of the error pipe.
3. Read from the error pipe:
   - **EOF:** exec succeeded. Record the child pidfd as the
     service's main process.
   - **Data:** pre-exec setup failed. Parse the step identifier
     and errno. Log the specific failure. Transition the service
     to Failed with cause PreExecFailure.

### Step 8: Child pre-exec

In the child process. This path MUST be minimal -- no heap
allocation, no complex library calls, no logging. Straight-line
setup then exec.

1. Close the read end of the error pipe.
2. Install the service's KACS token.
3. Set RLIMIT values (LimitNOFILE, LimitCORE) if configured.
4. Set `oom_score_adj`:
   - `-1000` (OOM-immune) for ErrorControl=Critical services.
   - `0` (default) for all others.
5. Set working directory.
6. Set environment variables (base environment + Environment
   values from the definition).
7. Set `NOTIFY_SOCKET` to the notify socket path. This is set
      unconditionally regardless of the Readiness field -- services
      use sd_notify for watchdog, STOPPING=1, FDSTORE, and
      EXTEND_TIMEOUT_USEC in addition to readiness signalling.
8. Inject stored file descriptors if the service has an fd store
   with entries from a previous run.
9. Exec the binary (`ImagePath` + `Arguments`).
10. If exec fails: write error to the pipe, `_exit(127)`.
11. If any step 2-8 fails: write error to the pipe, `_exit(126)`.

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
