---
title: Clocks on Peios
type: concept
description: The clocks Peios exposes to userspace — what each measures, how to read them, and the side-channel-precision policy that gates fine-grained timer access.
related:
  - peios/time/setting-time
  - peios/time/posix-timers
  - peios/time/timerfd-and-intervals
  - peios/time/hardware-and-precision
---

A running Peios system tracks several distinct clocks, each measuring a different notion of time. Reading them is unprivileged and fast — the heavy lifting (atomic sync with NTP, hardware-clock calibration, monotonic accumulation across suspend) happens in the kernel and is exposed through a uniform syscall surface.

This page covers what each clock represents, how to read it, and the **timer-precision policy** that controls how fine-grained those reads can be for unprivileged code.

## The clocks

| Clock ID | What it measures |
|---|---|
| `CLOCK_REALTIME` | Wall-clock time. Settable. Subject to NTP discipline (gradual frequency corrections). May jump backwards if reset. |
| `CLOCK_REALTIME_COARSE` | Same value as `CLOCK_REALTIME` but read from a cached value updated at tick rate. Faster, lower resolution. |
| `CLOCK_MONOTONIC` | Time since some unspecified starting point, never goes backward. Adjusted by NTP frequency discipline but never stepped. **Excludes time spent in suspend.** |
| `CLOCK_MONOTONIC_COARSE` | Cached monotonic, faster and lower resolution. |
| `CLOCK_MONOTONIC_RAW` | Like `CLOCK_MONOTONIC` but not subject to NTP frequency adjustment — the raw hardware tick rate. |
| `CLOCK_BOOTTIME` | Like `CLOCK_MONOTONIC` but **includes time spent in suspend.** Useful for measuring elapsed wall time across a sleep. |
| `CLOCK_TAI` | International Atomic Time — `CLOCK_REALTIME` plus the current leap-second offset. No leap-second discontinuities. |
| `CLOCK_PROCESS_CPUTIME_ID` | Total CPU time consumed by the calling process across all threads. |
| `CLOCK_THREAD_CPUTIME_ID` | CPU time consumed by the calling thread. |
| `CLOCK_REALTIME_ALARM` | Like `CLOCK_REALTIME` but fires wake-from-suspend events. Requires `SeWakeFromSleepPrivilege` to use as a timer source. |
| `CLOCK_BOOTTIME_ALARM` | Same, monotonic flavour. |

The two CPU-time clocks (`CLOCK_PROCESS_CPUTIME_ID`, `CLOCK_THREAD_CPUTIME_ID`) can also read *another* process's or thread's CPU time when called with a PID-encoded clockid. That cross-process variant is gated; see [Cross-process CPU time](#cross-process-cpu-time-reads) below.

## Reading clocks

The canonical interface is `clock_gettime`:

```c
struct timespec ts;
clock_gettime(CLOCK_MONOTONIC, &ts);
// ts.tv_sec, ts.tv_nsec
```

The same syscall handles every clock ID. `clock_getres()` returns the clock's nominal resolution (typically 1 ns on modern hardware for the high-precision clocks, several ms for the `_COARSE` variants).

Three legacy interfaces remain in the ABI for compatibility:

- `gettimeofday(&tv, &tz)` — historical, returns `CLOCK_REALTIME` as a `timeval`. Compat-only.
- `time(&t)` — historical, returns `CLOCK_REALTIME` as seconds-since-epoch. Compat-only.
- `times(&buf)` — historical, returns process CPU time as clock ticks. Compat-only.

New code should use `clock_gettime`. The legacy interfaces work on Peios for substrate compatibility but offer nothing the modern API doesn't.

## vDSO acceleration

Reading a clock is one of the most common operations a process performs — every log line that includes a timestamp, every per-request latency measurement, every TLS session that checks certificate validity. Doing those as syscalls would be expensive.

The kernel maps a small read-only page into every process at a known address — the **vDSO** (virtual dynamic shared object). The vDSO contains optimised implementations of `clock_gettime`, `gettimeofday`, and `time` that read directly from kernel-managed timekeeping data without entering kernel mode. A typical `clock_gettime(CLOCK_MONOTONIC)` is ~10 ns of inline code, no syscall, no privilege transition.

The vDSO honours the **timer-precision policy** described below — when an unprivileged process is configured for coarsened timers, the vDSO returns coarsened values. There is no escape route around the policy through the vDSO.

## Timer precision policy

Fine-grained timer precision (sub-microsecond) is useful for legitimate code: profilers, latency measurement, packet timestamping, real-time signal processing. It is also the foundational requirement for an entire class of attacks — Spectre, Meltdown, and the broader transient-execution family all depend on the attacker being able to time cache hits versus misses, which differ by tens to hundreds of nanoseconds. Without nanosecond timer precision, the practical attack collapses.

Peios exposes a registry-driven policy controlling how much precision unprivileged userspace gets:

| Registry value | Behaviour |
|---|---|
| `unrestricted` (default) | Full hardware precision available to all userspace. Matches Linux's default behaviour. |
| `privileged-only` | Unprivileged processes receive timestamps coarsened to ~1 µs. Processes holding `SePrecisionTimerPrivilege` see full precision. |
| `coarsened` | All userspace, including privileged code, receives coarsened timestamps. Reserved for forensic environments where defence-in-depth against side channels takes priority over instrumentation. |

The path: `\System\Timekeeping\TimerPrecisionMode`, registry-driven via `ksyncd`.

Server defaults are conservative-permissive — `unrestricted` matches what installed software expects, and the kernel-side mitigations (KPTI, retpolines, microcode) are the primary line of defence against transient-execution attacks. Operators running multi-tenant or high-assurance workloads flip the knob.

When `privileged-only` is in effect, the kernel applies the equivalent of `prctl(PR_SET_TSC, PR_TSC_SIGSEGV)` to any process not holding `SePrecisionTimerPrivilege`. Direct `rdtsc` from such a process traps; `clock_gettime` and the vDSO return coarsened values. Holders of the privilege get the full hardware view.

`SePrecisionTimerPrivilege` is a dedicated privilege precisely so it can be granted narrowly. A profiling daemon that legitimately needs nanosecond timing receives the privilege; ordinary application processes do not. The privilege grants no other authority — it is not a back door to scheduler priority, system time, or anything else; it controls only the precision of timer reads.

> [!INFORMATIVE]
> Software-only precision attacks remain partially viable even with timer coarsening — a tight loop incrementing a counter, with another thread reading it, builds a rough high-resolution timer from low-resolution primitives. Coarsening raises the bar significantly but is not a complete defence. The mitigation is most useful as part of a layered hardening posture, not as a standalone protection.

## Cross-process CPU time reads

The two CPU-time clocks accept a PID-encoded clockid that reads another process's or thread's accumulated CPU time:

```c
clockid_t cid = MAKE_PROCESS_CPUCLOCK(target_pid, CPUCLOCK_SCHED);
struct timespec ts;
clock_gettime(cid, &ts);
```

This is the same data that `ps` and `top` display. The gate is `PROCESS_QUERY_LIMITED` on the target's process security descriptor — the standard "visible to all users at the basic-info tier" mask — plus the usual PIP dominance check on cross-process queries.

A target whose process SD denies `PROCESS_QUERY_LIMITED` to the caller, or which is PIP-protected and does not let the caller dominate, returns `EPERM`. Self-targeted reads (calling process reading its own CPU time) are unrestricted.

This makes the `clock_gettime` path consistent with `/proc/<pid>/stat` reads — both surface the same data and use the same access tier.

## Adjustments and discontinuities

`CLOCK_REALTIME` can move discontinuously: NTP step adjustments, manual `clock_settime` calls, system suspend, or DST-style timezone changes (though timezone is a userspace concept, not kernel) all produce jumps. Code that wants to measure elapsed wall time across one of these events should use `CLOCK_BOOTTIME` (jumps neither for setting nor for suspend).

`CLOCK_MONOTONIC` is guaranteed not to go backward and not to jump on `clock_settime`, but it does pause across suspend. `CLOCK_MONOTONIC_RAW` similarly pauses but is also unaffected by NTP frequency discipline — useful when you want to measure raw hardware time, but practically rare.

For measuring durations: `CLOCK_BOOTTIME` if you need wall-time elapsed including suspend; `CLOCK_MONOTONIC` if you want elapsed running time excluding suspend; `CLOCK_MONOTONIC_RAW` if you also want to exclude NTP frequency corrections.

For absolute time: `CLOCK_REALTIME` (subject to leap seconds and clock-set events) or `CLOCK_TAI` (smooth across leaps but only useful if your application understands TAI-vs-UTC).

## See also

- [Setting time](setting-time) — how the clocks are *changed*, who's authorised, and the threat model.
- [POSIX timers](posix-timers) — `timer_create` family for periodic and one-shot scheduled events.
- [timerfd and interval timers](timerfd-and-intervals) — fd-shaped and legacy timer interfaces.
- [Hardware and precision](hardware-and-precision) — clocksource selection, NTP discipline, RTC, PTP.
