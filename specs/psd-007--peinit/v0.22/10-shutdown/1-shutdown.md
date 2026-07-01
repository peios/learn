---
title: Shutdown
---

## Shutdown triggers

Shutdown is initiated through four paths.

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

PID 1 handles three shutdown-related signals:

| Signal | Behaviour |
|---|---|
| SIGINT | Reboot request. Sent by the kernel on Ctrl+Alt+Del. |
| SIGTERM | Poweroff request. PID 1 cannot be killed by SIGTERM but may choose to handle it. |
| SIGPWR | Poweroff request. Compatibility path for environments that surface power failure or power-button policy as a signal. |

Repeated SIGINT within a short window (3 presses in 5 seconds)
MUST trigger an immediate forced shutdown -- skip the graceful
stop sequence, SIGKILL all services, sync, reboot.

### Power-button event

On Linux, peinit MUST treat an `EV_KEY` / `KEY_POWER` press from a
readable `/dev/input/event*` input device as a graceful `poweroff`
request.

Only key press events (`value == 1`) initiate shutdown. Key release
events (`value == 0`), key repeat events (`value == 2`), other keys,
and other input event types MUST be ignored by peinit's minimal
power-button path.

Power-button input is a fail-soft runtime source. If `/dev/input` is
absent, an event device cannot be opened or registered, or a registered
input fd later fails while being read, peinit MUST continue normal
operation. A failed registered input fd SHOULD be removed from the
runtime event loop so repeated read failures do not spin PID 1. Such
failures degrade only direct power-button handling; shutdown via the
control socket and signal paths remains available.

This path is intentionally minimal. It is not a complete power-management
policy engine and does not replace a future acpid/logind-equivalent
daemon. Such a daemon may translate richer policy into peinit control
socket shutdown commands.

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
  one exists; they do not receive graceful shutdown ordering. They
  enter Failed with cause ShutdownWave while post-kill verification is
  pending. If the service cgroup remains populated after the post-kill
  timeout, peinit MUST transition the service to Abandoned with cause
  ProcessUnkillable and leak the cgroup.
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

### Step 6: Save persisted random seed

After all services have stopped, and before remounting or unmounting
filesystems, peinit MUST attempt to save a fresh persisted random seed to
`/var/lib/peinit/random-seed` for the next boot.

The saved seed MUST be generated from the kernel CSPRNG on the running
machine. It MUST NOT be copied from a packaged image, live ISO, VM template,
or any other shared artifact. peinit MUST store it as a machine-local object
protected by Peios file security so that only SYSTEM-equivalent authority can
read or replace it.

The write MUST be crash-conscious: write the new seed to a temporary path on
the same filesystem, flush it, atomically replace the previous seed, and flush
the containing directory where the platform supports directory flush. Failure
to save the seed MUST be retained or logged, but MUST NOT abort final shutdown
and MUST NOT enter Recovery mode.

Forced shutdown and Critical-service immediate reboot paths MAY skip seed
save. Those paths are required to reach `sync()` and the final kernel action
with minimal additional work.

### Step 7: Unmount filesystems

After all services have stopped:

1. Snapshot the current mount table before beginning unmounts. peinit
   MUST attempt to unmount every remaining non-root mount in its mount
   namespace, not only mounts that peinit personally mounted during
   Phase 1. This includes the Phase 1 mount set (`/proc`, `/sys`,
   `/dev`, `/dev/pts`, `/dev/shm`, `/run`, `/sys/fs/cgroup`) whenever
   those mount points are still present.
2. Unmount child mount points before parent mount points. Implementations
   SHOULD process the mount-table snapshot in descending mount-point
   path-depth order.
3. A mount point that is already gone or no longer mounted is a successful
   no-op. peinit MUST NOT treat this as a shutdown failure.
4. If an unmount fails, peinit MUST attempt to remount that mount point
   read-only when the kernel and filesystem permit it. If the read-only
   remount also fails, peinit MUST retain or log the cleanup failure
   evidence, but MUST NOT abort final shutdown and MUST NOT enter Recovery
   mode.
5. The root filesystem (`/`) is not unmounted. After all non-root unmount
   attempts have completed, peinit MUST remount the root filesystem
   read-only. If the root read-only remount fails, peinit MUST retain or
   log the failure evidence, but MUST continue to Step 8.

### Step 8: Sync and final action

Step 8 is irreversible finalization. Cleanup failures retained from
Steps 6 and 7 affect logging and diagnostics only; they MUST NOT block the
final kernel action.

1. `sync()` -- flush all pending writes. peinit MUST call `sync()` for
   graceful shutdown, forced shutdown, and Critical-service immediate
   reboot paths.
2. Call `reboot(2)` with the appropriate command:
   - `RB_POWER_OFF` for poweroff.
   - `RB_AUTOBOOT` for reboot.
   - `RB_HALT_SYSTEM` for halt.
3. If `reboot(2)` returns, the final action failed. peinit MUST enter a
   minimal failed-shutdown state, keep PID 1 alive, retain or log the
   failure evidence, and retry the same final action no more frequently
   than once per second. It MUST NOT restart normal services and MUST NOT
   enter Recovery mode after finalization has begun.

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
| SIGPWR | Poweroff request. Compatibility path for power-button/power-failure policy. |
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
