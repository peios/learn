---
title: Shutdown
---

## Shutdown triggers

Shutdown is initiated through three paths.

### Control socket command

An administrator sends a shutdown command via peinit's control
socket. The command specifies the type:

| Type | Behaviour |
|---|---|
| poweroff | Stop all services, unmount, power off. |
| reboot | Stop all services, unmount, reboot. |
| halt | Stop all services, unmount, halt (CPU stopped, system stays powered). |

The shutdown command is access-controlled via peinit's control SD.
Only principals with SYSTEM_SHUTDOWN may initiate shutdown.

### Signals

PID 1 handles two shutdown-related signals:

| Signal | Behaviour |
|---|---|
| SIGINT | Reboot request. Sent by the kernel on Ctrl+Alt+Del. |
| SIGTERM | Poweroff request. PID 1 cannot be killed by SIGTERM but may choose to handle it. |

Repeated SIGINT within a short window (3 presses in 5 seconds)
MUST trigger an immediate forced shutdown -- skip the graceful
stop sequence, SIGKILL all services, sync, reboot.

### Critical service failure

When a Critical service enters Failed state (restart budget
exhausted), peinit MUST sync filesystems and reboot immediately.
This is NOT a graceful shutdown -- there is no service stop
ordering. The system is in an undefined state and the fastest path
to a known state is a reboot.

## Graceful shutdown sequence

When peinit receives a poweroff, reboot, or halt command:

### Step 1: Enter shutdown state

peinit MUST set an internal shutdown flag. While the flag is set:

- No new services may be started.
- Timer triggers are disarmed.
- New control socket commands are rejected (except status queries).
  Rejected commands return `INVALID_STATE`.

### Step 2: Suspend Critical failure semantics

If a Critical service fails during shutdown, the failure is logged
but MUST NOT trigger a reboot. The system is already shutting down
-- rebooting would create an infinite loop.

### Step 3: Clear Completed services

Oneshot services with RemainAfterExit that are in the Completed
state have no running process. peinit MUST transition them to
Inactive. This releases any dependency relationships they
participate in, allowing their dependents to be stopped cleanly.

### Step 4: Stop services in reverse dependency order

After Step 3, peinit MUST classify remaining service states for
shutdown stop eligibility:

- Services in Active or Reloading are graceful-stop eligible and
  enter the reverse dependency stop waves.
- Services in Stopping are already in a stop path. They participate
  in the shutdown stop waves for ordering and timeout/escalation
  purposes, but peinit MUST NOT send an additional initial SIGTERM
  to a service already in Stopping.
- Services in Starting are not graceful-stop eligible. peinit MUST
  cancel the startup path and send SIGKILL to the service cgroup if
  one exists; they do not receive graceful shutdown ordering.
- Services in Inactive, Failed, Skipped, Backoff, or Abandoned do not
  enter graceful stop waves. Abandoned cgroups remain leaked and
  shutdown continues.
- Completed services have already been cleared to Inactive by Step 3
  and do not enter stop waves.

peinit MUST build the reverse dependency graph for graceful-stop
eligible and already-stopping services and stop them in waves:

1. Each graceful-stop eligible service receives SIGTERM.
   Already-stopping services do not receive an additional initial
   SIGTERM.
2. Each service has StopTimeout seconds to exit.
3. If StopTimeout expires, SIGKILL is sent to the service's entire
   cgroup.
4. A service MUST NOT be stopped until all services that depend on
   it (via Requires or BindsTo) have stopped.

If the operation object for a later-wave shutdown Stop expires while
it is still Pending, peinit fails that operation and notifies waiters
according to §8.1. This does not override the wave ordering above:
peinit MUST NOT send SIGTERM or SIGKILL to that service until all
dependent services have stopped and the service's wave is eligible.

Services that send `STOPPING=1` via sd_notify are acknowledged.
Services that send `EXTEND_TIMEOUT_USEC=...` during shutdown get
additional time, capped by both the per-service StopTimeout (x4)
and the global shutdown timeout.

For a service that is already in Stopping when graceful shutdown
classification runs, peinit MUST NOT reset the service's stop timeout
clock at shutdown entry or at wave eligibility. If an in-flight Stop
operation or in-flight Restart operation currently executing its stop
leg exists, that operation's retained timing evidence governs the
StopTimeout enforcement for the already-Stopping participant. If no
operation object exists for the active stop path, peinit MUST use
retained service-level Stopping timeout evidence from the stop path that
placed the service in Stopping, and that retained evidence MUST include the
cause that initiated the `Stopping` transition (`ExplicitStop`,
`ShutdownWave`, `ConflictEviction`, or `BindsToPropagation`). Missing,
stale, or ambiguous timing or stop-cause evidence for such a no-operation
already-Stopping service MUST fail closed for timeout scans and child-reap
completion until stronger retained evidence is available.

When peinit services a retained shutdown StopTimeout timerfd for
already-Stopping participants, it MUST validate that the retained scheduler
deadline and retained timerfd topology describe the same timeout before
consuming the timerfd. If the timerfd has been read successfully, the timeout
firing is consumed evidence and peinit MUST NOT continue to treat the old
timerfd deadline as armed. Timerfd or epoll cleanup failure after such a
successful read MUST be retained or reported as cleanup failure evidence, but
it MUST NOT suppress the timeout effects for the consumed firing.

### Step 5: Global timeout enforcement

The entire shutdown sequence is bounded by a global timeout:

| Registry key | Default | Description |
|---|---|---|
| `Machine\System\Boot\ShutdownTimeout` | 90 | Maximum seconds for the entire shutdown sequence. |

If the global timeout expires:

1. All remaining services receive SIGKILL via cgroup kill.
2. Services whose cgroups do not empty within the post-kill timeout
   (default 5 seconds) are marked Abandoned -- their cgroups are
   leaked.
3. Continue to step 6 regardless of Abandoned services.

### Step 6: Unmount filesystems

After all services have stopped:

1. Unmount the Phase 1 virtual filesystems peinit mounted (`/run`,
   `/dev/shm`, `/dev/pts`, `/sys/fs/cgroup`).
2. `/dev`, `/sys`, `/proc` are left mounted (kernel needs them).
3. Remount root filesystem read-only.

### Step 7: Sync and final action

1. `sync()` -- flush all pending writes.
2. Call `reboot(2)` with the appropriate command:
   - `RB_POWER_OFF` for poweroff.
   - `RB_AUTOBOOT` for reboot.
   - `RB_HALT_SYSTEM` for halt.

## Shutdown during boot

If a shutdown is requested while peinit is still in Phase 2 boot,
peinit MUST enter shutdown immediately:

- Services in Starting state are killed (SIGKILL -- they never
  reached Active, no graceful stop).
- Services that reached Active are stopped gracefully per the
  normal sequence.
- The boot is abandoned.

## Signal summary

PID 1 handles all signals via signalfd. All signals are blocked
and read from the event loop -- no signal handlers, no
async-signal-safety concerns.

On Linux, "all signals are blocked" means peinit MUST build a mask
containing every blockable Linux signal in the supported signal-number
range. SIGKILL and SIGSTOP are not blockable and are not expected to be
delivered through signalfd. peinit MUST install the mask with
`rt_sigprocmask(SIG_BLOCK, ...)` before entering the main event loop, then
create the PID 1 signal fd with `signalfd4(-1, mask, ...)`.

The PID 1 signalfd MUST be created with close-on-exec and nonblocking
semantics (`SFD_CLOEXEC | SFD_NONBLOCK`). The same signal mask used for
`rt_sigprocmask` MUST be used for signalfd creation. If signal blocking,
signalfd creation, retained fd installation, or event-loop registration
fails, peinit MUST fail closed and MUST NOT fall back to async signal
handlers.

| Signal | Behaviour |
|---|---|
| SIGCHLD | Reap children via `waitpid`. Match to tracked services. Also reaps orphaned processes (not tracked by any service). |
| SIGINT | Reboot request. Repeated = forced reboot. |
| SIGTERM | Poweroff request. |
| SIGHUP | Ignored. PID 1 has no controlling terminal. |
| SIGPIPE | Ignored. Broken pipes on the control socket MUST NOT crash PID 1. |

When SIGCHLD reaping observes a child exit status, peinit MUST normalize the
Linux wait status before applying service or job policy:

- exited children carry the exact 0-255 exit code;
- signalled children carry the terminating signal number and whether the Linux
  core-dump bit was present;
- stopped or continued statuses are invalid for the normal Peinit reaping path
  because Peinit does not request them with `waitpid`; observing one MUST fail
  closed.

All other signals are ignored. PID 1 cannot be killed by any
signal -- the kernel protects PID 1 from fatal signals.

## STOPPING=1 acknowledgement

When a service sends `STOPPING=1` via sd_notify, peinit MUST
authenticate the sender (§11.1) and acknowledge the notification
by logging it.

After receiving `STOPPING=1`, peinit MUST NOT send additional
SIGTERM signals to the service. The service has indicated that it
is already shutting down gracefully -- a redundant SIGTERM is
unnecessary and may interfere with the service's shutdown sequence.

The StopTimeout continues to apply after `STOPPING=1` is received.
`STOPPING=1` does not extend or reset the stop timeout. If the
service needs additional time to shut down, it MUST send
`EXTEND_TIMEOUT_USEC` (§5.3). If StopTimeout expires without the
process
exiting, peinit escalates to SIGKILL regardless of whether
`STOPPING=1` was received.

> [!INFORMATIVE]
> STOPPING=1 is a courtesy notification, not a timeout mechanism.
> Its purpose is to prevent peinit from sending a SIGTERM to a
> service that is already in its shutdown path -- for example, a
> service that begins graceful shutdown in response to a health
> check failure or an internal error before peinit sends the stop
> signal. The service should use EXTEND_TIMEOUT_USEC if it needs
> more time.
