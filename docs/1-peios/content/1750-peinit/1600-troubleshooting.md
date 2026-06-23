---
title: Troubleshooting peinit
type: how-to
description: "A symptom-first guide to peinit problems: a service that won't start, one that keeps restarting, a config change that didn't take, an access denial, a dependent that never came up, and a machine stuck rebooting or sitting in Safe or Recovery mode. Each works backward from what you see to the cause and the fix."
related:
  - peios/peinit/the-service-lifecycle
  - peios/peinit/supervision
  - peios/peinit/controlling-services
  - peios/peinit/boot-and-boot-modes
  - peios/access-decisions/debugging-a-denial
---

Almost every peinit problem is diagnosed the same way: **read the state and the cause.** A `status` query gives you both, and the [cause taxonomy](~peios/peinit/the-service-lifecycle) tells you what the cause means. This page works backward from common symptoms to the cause and the fix.

```
$ peiosctl status <service>      # state + cause + health + warnings
$ peiosctl list                  # everything you can see, at a glance
```

For history beyond what peinit holds in memory — past jobs, prior failures, the exact log line a service died on — query [eventd](~peios/auditing/overview); peinit emits every [job and operation](~peios/peinit/jobs-and-operations) transition there.

## A service won't start

`status` shows it `Failed` or `Skipped`. The **cause** says why:

| Cause | What happened | What to do |
|---|---|---|
| `ValidationError` | The definition is malformed — a bad field, an unresolvable conflict, an illegal health-check timing. | Check the logs for the specific field. Fix the definition; the message names what is wrong. |
| `DependencyFailure` | A `Requires`/`BindsTo` target failed or does not exist. | Fix the *target* first — `status` it. The dependent recovers once the target can start. |
| `ConditionSkipped` (→ Skipped) | A start-time [condition](~peios/peinit/execution-environment) was not met. **Not a failure** — the service decided it does not apply here. | If it *should* run, the condition's premise is false (a missing path/file/key). This is often correct behaviour. |
| `AssertionError` | A start-time [assert](~peios/peinit/execution-environment) failed — a required precondition is missing. | Create the missing precondition (path, file, directory, registry key), then start again. |
| `PreHookFailure` | An `ExecStartPre` hook exited non-zero. | Run the hook command by hand as the [hook identity](~peios/peinit/identity-and-privileges) to see why. |
| `ParentSetupFailure` | peinit could not even fork — fd/PID exhaustion, a cgroup error. No process was created. | A system-resource problem, not the service's fault. Check for fd/PID limits and cgroup health. |
| `PreExecFailure` | Setup after fork failed — token install, rlimits, environment. | Usually identity: check `Identity`, that authd is up, and that `RequiredPrivileges` names real privileges. |
| `ReadinessTimeout` | The process started but never became [ready](~peios/peinit/service-types) within `StartTimeout`. | Either the service is genuinely slow (raise `StartTimeout`, or have it send `EXTEND_TIMEOUT_USEC`) or it never sends `READY=1` (wrong `Readiness`, or a bug). |

> [!TIP]
> A startup failure (`ReadinessTimeout`, `PreHookFailure`, `PreExecFailure`, `ParentSetupFailure`) is **restart-eligible** — peinit will have retried it through [Backoff](~peios/peinit/supervision) before landing in Failed. So by the time you see `Failed`, it has already failed repeatedly. The logs show each attempt.

## A service keeps restarting

The service flaps — up, down, up, down. This is [restart policy](~peios/peinit/supervision) doing its job, but it points at an unstable service.

- **It eventually settles in `Failed` with `RestartBudgetExhausted`.** It crashed `RestartMaxRetries` times faster than it could stay healthy for `RestartWindow`. The fix is the *service*, not the policy — read its logs for the crash. Raising the budget only delays the inevitable.
- **It flaps forever and never exhausts the budget.** It is briefly reaching Active each cycle and resetting the counter. Either genuinely stabilise it, or — if a [health check](~peios/peinit/supervision) is failing it after it starts — check the health command; a flaky check restarts a perfectly good service.
- **It restarts on a clean exit you did not expect.** `RestartPolicy=Always` restarts even successful exits (cause `CleanExitRestart`). If the service is *meant* to exit, use `OnFailure` instead.

## The machine keeps rebooting

A reboot loop almost always means a **Critical service is failing**. A [`ErrorControl=Critical`](~peios/peinit/supervision) service that exhausts its budget makes peinit sync and reboot; if it fails the same way every boot, you loop.

The [boot-attempt counter](~peios/peinit/boot-and-boot-modes) is designed to break this: after N attempts (default 3) peinit stops and drops you into [Recovery mode](#booted-into-recovery-mode). From the Recovery shell, find the failing Critical service (its logs are in [eventd](~peios/auditing/overview), which persists across reboots), fix or disable it, and reboot. If you need to intervene before the counter trips, boot with `peios.recovery=1` on the kernel command line.

## A service is Abandoned

`Abandoned` means peinit SIGKILLed the process but it survived — stuck in uninterruptible kernel sleep (**D-state**), the signature of hung I/O (a dead NFS mount, a failing disk). Nothing in userspace can kill a D-state process.

- The underlying **I/O fault is the real problem** — investigate the storage or mount, not peinit.
- The service's cgroup is **leaked** and shows in `warnings`. A later start uses a fresh [generational cgroup](~peios/peinit/execution-environment), so the new instance is unaffected.
- `peiosctl reset <service>` clears the Abandoned state and re-checks the cgroup: if the stuck process finally died, peinit cleans up; if not, it stays leaked and warns you. Leaked cgroups clear fully only on reboot.

## I changed the config and nothing happened

peinit works from an [in-memory snapshot](~peios/peinit/defining-a-service), and each field has a **mutability class** that decides when a change applies:

- **Immutable at runtime** (`ImagePath`, `Type`, `Identity`, `RequiredPrivileges`, `ErrorControl`) → takes effect only on `restart`.
- **Apply on next start** (dependencies, conditions, `OnFailure`) → next start or graph reload.
- **Reloadable at runtime** (timeouts, restart policy, health checks, environment, hooks…) → next time peinit acts on the service.
- **Hot-reloaded** (`ServiceSecurity`) → next control request.

If a change is not landing, check its class first. For a wholesale re-read of every definition, run `peiosctl reload-config` — it rebuilds and validates the whole graph atomically and swaps it in only if validation passes (running services are untouched). And remember peinit *pulls* changes from [registry notifications](~peios/the-registry/watches) rather than having them pushed, so there can be a brief lag.

## ACCESS_DENIED

A control command returns `ACCESS_DENIED`. peinit ran [AccessCheck](~peios/access-decisions/overview) on your token against the target's descriptor and the right was not granted:

- A *service* command needs the matching right in the service's [ServiceSecurity descriptor](~peios/peinit/who-can-manage-a-service) (`start` needs `SERVICE_START`, `restart` needs both stop and start, …).
- `shutdown` and `reload-config` need `SYSTEM_SHUTDOWN` / `SYSTEM_RELOAD_CONFIG` in peinit's control descriptor.
- The check uses your **effective** identity at connect time — if you are [impersonating](~peios/impersonation/overview), that is what is checked.

Every denial is logged with the caller SID, target, and requested right. Walk it through [Debugging a denial](~peios/access-decisions/debugging-a-denial).

> [!NOTE]
> If `list` shows fewer services than you expect, that is not a bug — `list` **omits** services you lack `SERVICE_QUERY_STATUS` on rather than denying them. You are seeing exactly what your token can see.

## A dependent never started

You started (or booted) a service, but something that depends on it never came up:

- A **`Requires`/`BindsTo` dependent stays blocked** until its target reaches a [satisfying state](~peios/peinit/the-service-lifecycle) (Active, Completed, or Skipped). If the target is stuck in Starting or Failed, so is the dependent — fix the target.
- A dependent that connected to its target on boot and got *connection refused* usually means the target uses **`Readiness=Alive`** — peinit only waited for the process to exist, not to be serving. Switch the target to `Readiness=Notify` so it signals `READY=1` when actually ready. (peinit logs this as a validation warning at boot.)
- A **`Wants` dependent starts regardless** of its target — if you needed it to wait, `Wants` was the wrong relationship; use `Requires`.

## Booted into Safe mode

[Safe mode](~peios/peinit/boot-and-boot-modes) starts only Critical and `SafeMode=1` services. You land here when graph validation finds a **cycle or unresolvable conflict involving a Critical service**, or when `peios.safemode=1` is on the kernel command line. The TCB is healthy; the *configuration* is broken.

Fix the graph: the logs name the cycle path (`A → B → C → A`) or the conflicting pair. Once the cycle is broken or the conflict resolved, a normal boot returns. You can start any service by hand from Safe mode in the meantime — it is only auto-start that is restricted.

## Booted into Recovery mode

[Recovery mode](~peios/peinit/boot-and-boot-modes) gives you a SYSTEM shell on the console and starts nothing else. You reach it when the boot counter hits N, when `peios.recovery=1` is set, or when **registryd failed in Phase 1** (entered immediately, no counter).

If the registry itself is the problem, use the offline tools that bypass it — they talk to the [loregd implementation](~peios/peinit/boot-and-boot-modes) directly:

```
$ loregd --inspector               # read the storage directly to diagnose
$ loregd --recover-from-backup     # restore the backup taken each registryd start
$ loregd --dangerously-clear-database   # last resort — wipe; roles re-supply config
```

Recovery has **no TCB protections** — it is a SYSTEM shell, full stop. Treat it accordingly, and remember it needs console access (physical, IPMI, or serial); there is no remote recovery yet.

## Where to start

To read states and causes fluently, keep [The service lifecycle](~peios/peinit/the-service-lifecycle) handy.

For restart, backoff, and Critical-reboot behaviour, see [Keeping services running](~peios/peinit/supervision).

For the commands and their outputs, see [Controlling services](~peios/peinit/controlling-services).
