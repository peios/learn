---
title: Setting Time
type: concept
description: How wall-clock time, monotonic frequency, leap seconds, and NTP discipline are altered on Peios — the SeSystemtimePrivilege gate, the threat model, and why clock-setting authority is held narrowly.
related:
  - peios/time/clocks
  - peios/time/hardware-and-precision
  - peios/privileges/understanding-privileges
---

Reading clocks is unprivileged; *changing* them is not. The kernel exposes several distinct mechanisms for adjusting the system's notion of time, all of which gate on the same privilege: **`SeSystemtimePrivilege`**.

This page covers what those mechanisms are, why they're authority-laden, and how the gate is enforced.

## The mechanisms

Three syscall paths can change the kernel's clocks:

| Call | Effect |
|---|---|
| `clock_settime(CLOCK_REALTIME, &ts)` | Step the wall clock to the given absolute value. Discontinuous jump — `CLOCK_REALTIME` jumps; `CLOCK_MONOTONIC` is unaffected. |
| `settimeofday(&tv, &tz)` | Legacy form of the same operation. The timezone argument is ignored on modern kernels. |
| `adjtimex(&tx)` / `clock_adjtime(clk, &tx)` | The NTP-discipline interface. Performs frequency adjustment, step adjustment, leap-second insertion, and other corrections. |

Plus the RTC ioctl path, which adjusts the hardware clock chip directly:

| Call | Effect |
|---|---|
| `ioctl(rtc_fd, RTC_SET_TIME, &tm)` | Write a new time to the hardware RTC. Effective on next boot, or immediately if `CONFIG_RTC_SYSTOHC` is firing. |

All four are gated on `SeSystemtimePrivilege`. A caller without the privilege receives `EPERM`.

## adjtimex modes

`adjtimex` is a Swiss-army-knife syscall — the `mode` field of `struct timex` selects which operations to perform:

| Mode flag | Effect |
|---|---|
| `ADJ_OFFSET` | Add the given offset to `CLOCK_REALTIME` (small step adjustment, typically used by NTP daemons). |
| `ADJ_FREQUENCY` | Set the kernel's PLL/FLL frequency adjustment. Slow drift correction. |
| `ADJ_MAXERROR` / `ADJ_ESTERROR` | Update the kernel's error-bound estimates. |
| `ADJ_STATUS` | Set NTP status bits — synchronised flag, leap-second pending flag, etc. |
| `ADJ_TIMECONST` | Set the PLL time constant (controls how aggressively the kernel chases an offset). |
| `ADJ_TAI` | Set the TAI-UTC offset. |
| `ADJ_SETOFFSET` | Step the clock by a given offset (large jump). |
| `ADJ_MICRO` / `ADJ_NANO` | Switch resolution mode for offset values. |

`adjtimex` with `mode == 0` is a pure read — it returns current state without changing anything. Reading is unprivileged. Any non-zero mode that mutates state requires `SeSystemtimePrivilege`.

The leap-second status bits (`STA_INS` for "insert leap second at next 00:00:00 UTC", `STA_DEL` for "delete leap second") are set via `ADJ_STATUS`. The kernel honours these flags at the appropriate moment by inserting or deleting a second from `CLOCK_REALTIME`. Whether to use leap-second handling at all, or run a leap-second-smearing strategy in userspace instead, is a configuration choice for the timesync daemon — see [Hardware and precision](hardware-and-precision).

## Why this is authority-laden

Wall-clock time is load-bearing for far more than the obvious "what time is it?" use cases. Wrong time breaks:

- **Certificate validation.** TLS certificates are valid only between their `notBefore` and `notAfter` timestamps. A clock skewed forward causes valid certificates to be rejected (denial of service); a clock skewed backward causes expired certificates — including known-compromised ones — to be accepted (security failure).
- **Kerberos authentication.** Kerberos tickets carry tight time bounds (typically 5-minute skew tolerance). Outside the tolerance, no Kerberos authentication succeeds. Domain access fails.
- **Audit timestamps.** Forensic analysis depends on log-line timestamps being accurate. A clock skewed during an incident creates a forensic puzzle that may obscure the actual sequence of events.
- **Scheduled operations.** Services configured to run at "00:00 UTC" run at the kernel's notion of that time. A backward-skewed clock could cause repeated execution of a daily job.
- **License timing, software-trial expiry, time-stamp tokens, RFC-3161 signed timestamps, blockchain consensus** — all depend on the clock being within tight tolerance of universal coordinated time.

A process holding clock-setting authority can silently produce any of those failures. It is closer in impact to "compromise the certificate authority" than to "modify a configuration file."

For this reason, `SeSystemtimePrivilege` is **not** part of the default privilege set granted to ordinary administrators. Holders are limited to:

- The system's timesync daemon (chronyd-equivalent, running as a TCB-tier service that legitimately needs `adjtimex` for NTP discipline).
- `peinit` during early boot, to seed `CLOCK_REALTIME` from the RTC before any other service starts.
- Operator-granted exceptional cases for diagnostic or recovery scenarios — granted via explicit privilege assignment in the registry, not picked up automatically.

This is the Windows posture (`SeSystemtimePrivilege` on Windows is similarly held narrowly, not in the default Administrator privilege set in hardened domain configurations) adapted to Peios's privilege model.

## Read-only adjtimex

A subset of the `adjtimex` interface is unprivileged: a call with `mode == 0` returns current NTP state — synchronised flag, current offset, frequency error, error bounds, leap-second pending flag — without modifying anything. This information leaks "the system is/isn't synchronised" but the same information is broadcast by every NTP daemon to every peer it speaks with, and is observable through other ambient channels. Gating reads would inconvenience diagnostic tools without producing real security benefit.

## Cross-references

- **RTC operations** that adjust hardware time gate on `SeSystemtimePrivilege`. RTC operations that schedule **wake events** (hardware-driven power-state transitions) gate on `SeShutdownPrivilege` instead — see [Hardware and precision](hardware-and-precision).
- **PTP hardware clock** time-setting operations gate on `SeSystemtimePrivilege` (via the ioctl), with file-SD on `/dev/ptp*` controlling who can talk to the device at all. See [Hardware and precision](hardware-and-precision).
- **Timer precision policy** is unrelated to time-setting authority — it gates how precise *reads* are for unprivileged code, not what the time *is*. See [Clocks](clocks#timer-precision-policy).

## Failure modes when wrong

A correctly-deployed Peios system has exactly one process actively driving clock state in steady state: the timesync daemon, talking to a quorum of NTP or PTP peers. If that daemon is compromised or misconfigured, the clock can drift; if multiple processes hold `SeSystemtimePrivilege` and disagree, they fight each other and the clock oscillates.

Operational guidance:

- Grant `SeSystemtimePrivilege` to exactly one timesync daemon.
- Monitor `adjtimex(0)` output — large `offset` values, frequent step adjustments, or `STA_UNSYNC` set for extended periods indicate trouble.
- If a process other than the designated daemon is observed calling `adjtimex` with mutating flags, treat it as an unauthorised privilege escalation attempt — even if its current SID happens to hold the privilege.

## See also

- [Clocks](clocks) — what the clocks measure and how to read them.
- [Hardware and precision](hardware-and-precision) — RTC, hardware clocksource selection, NTP discipline state machine, PTP support, leap-second handling.
- [Privileges](../privileges/understanding-privileges) — the `Se*Privilege` model and how privileges are granted.
