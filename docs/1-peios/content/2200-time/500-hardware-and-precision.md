---
title: Hardware Clocks, NTP, and PTP
type: reference
description: Hardware clock sources, the kernel NTP discipline state machine, the RTC device, leap-second handling, and Precision Time Protocol support.
related:
  - peios/time/clocks
  - peios/time/setting-time
  - peios/privileges/understanding-privileges
---

This page covers the lower-level pieces of the timekeeping stack: which hardware clocks the kernel uses, how the NTP discipline state machine works, the Real-Time Clock device, leap-second handling, and Precision Time Protocol.

## Hardware clocksources

The kernel's notion of time is ultimately driven by reading some piece of hardware. Different hardware exists on different systems, and the kernel selects from what's available at boot. Common clocksources:

| Clocksource | Notes |
|---|---|
| **TSC** (Time Stamp Counter) | Per-CPU counter incrementing at the CPU frequency. Fastest to read. Historically had reliability issues across cores, sockets, and suspend/resume; modern hardware is largely fixed but the kernel maintains a blocklist for known-bad chipsets. |
| **HPET** (High Precision Event Timer) | Motherboard-level timer, several MHz tick rate. Reliable, somewhat slower than TSC. Intel removed HPET from some recent chipsets. |
| **ACPI PM Timer** | Old, slow, always present. Last-resort fallback. |
| **KVM-clock / Xen-clock** | Paravirtualised clocksources for VMs. Used inside hypervised guests; the host sees TSC/HPET. |
| **Architecture-specific** | ARM has `arm-arch-counter`; other architectures have their equivalents. |

The kernel selects a default at boot based on hardware detection and the built-in blocklist, then exposes the choice as `/sys/devices/system/clocksource/clocksource0/current_clocksource`. On Peios this surface is registry-driven via `ksyncd` — operators can override the kernel's choice when they have specific knowledge (e.g., a VM where KVM-clock is glitchy on a particular hypervisor version).

Available choices are listed in `available_clocksource`. Switching at runtime is supported but the kernel typically picks the right thing by default; operator overrides are diagnostic-grade rare.

There is no security implication to clocksource selection. A wrong clocksource just makes time wrong, which is bounded by the same threat model that any clock-corruption attack covers (covered under [setting time](setting-time)). The privilege gate on writing the clocksource registry knob is the registry-key SD, not a separate clock-related privilege.

## High-resolution timers (hrtimer)

Inside the kernel, timer management uses the `hrtimer` framework — a red-black tree of pending timers with nanosecond-resolution expiry times. Whenever a timer's deadline approaches, the kernel programs the hardware clockevent device (a per-CPU programmable interrupt timer) to fire at exactly the right moment. The result is that `clock_nanosleep`, `timer_settime`, `timerfd_settime`, and `select`/`poll`/`epoll_wait` timeouts all resolve to nanosecond accuracy on hardware that supports it.

`hrtimer` is universally enabled on Peios. There is no build-time or runtime switch.

## Tickless kernel

The Linux kernel periodically interrupts each CPU with a "tick" interrupt — historically a fixed rate, used for scheduling decisions, accounting, and timer expiry. Modern kernels are increasingly **tickless**: the tick is omitted when not needed.

| Mode | Behaviour |
|---|---|
| `CONFIG_NO_HZ_IDLE` | Tick is suppressed on idle CPUs. The CPU sleeps until either a hardware interrupt or a scheduled timer wakes it. Universal power saving with no downside. |
| `CONFIG_NO_HZ_FULL` | Tick is also suppressed on busy CPUs running a single task. The user-space code runs without periodic interruption — important for real-time workloads, HPC compute kernels, and packet processing fast paths. Activated per-CPU via the `nohz_full=` kernel boot parameter. |

Peios kernel builds enable both. `NO_HZ_IDLE` is always-on. `NO_HZ_FULL` is compiled in but not active by default — operators of latency-sensitive or high-performance workloads opt in by setting `nohz_full=<cpu-list>` on the kernel command line, which isolates the listed CPUs from periodic ticks.

The base tick rate (`CONFIG_HZ`) on Peios server kernels is **250 Hz** — the standard server-tier choice, balancing scheduler granularity against per-tick overhead. Workloads needing finer scheduling decisions either rely on `hrtimer` (which gives nanosecond timer resolution regardless of `HZ`) or migrate to `nohz_full` CPUs where ticks are suppressed entirely.

## Real-Time Clock (RTC)

The RTC is a small battery-backed clock chip on the motherboard that keeps time when the system is powered off. At boot, the kernel reads the RTC to seed `CLOCK_REALTIME`; during shutdown, it may write `CLOCK_REALTIME` back to the RTC to preserve drift corrections.

The userspace interface is `/dev/rtc0` (and `/dev/rtc1`, etc., on systems with multiple RTC devices), with an ioctl-based command set:

| ioctl | Purpose | Authority |
|---|---|---|
| `RTC_RD_TIME` | Read current RTC time. | Unprivileged (subject to file SD). |
| `RTC_SET_TIME` | Set RTC time. | `SeSystemtimePrivilege`. |
| `RTC_ALM_SET` / `RTC_ALM_READ` | Set / read in-OS alarm — fires while system is running. | `SeSystemtimePrivilege` for set, unprivileged for read. |
| `RTC_UIE_ON` / `RTC_UIE_OFF` | Enable / disable update interrupts (1Hz tick). | Unprivileged. |
| `RTC_PIE_ON` / `RTC_PIE_OFF` / `RTC_IRQP_SET` | Enable / configure periodic interrupt. | Unprivileged for enable; periodic-rate set bounded by kernel limits. |
| `RTC_WKALM_SET` | Set wake-from-suspend alarm — hardware wakes the system at the scheduled time. | **`SeShutdownPrivilege`** (not the time-setting privilege). |
| `RTC_WKALM_RD` | Read currently-scheduled wake alarm. | Unprivileged. |

The asymmetry on `RTC_WKALM_SET` is deliberate. Setting a wake alarm causes the *hardware* to power the system on or wake it from suspend at the appointed time — a power-state-shaped operation, not a time-shaped one. Bundling it with `SeSystemtimePrivilege` would let any process authorised to discipline the clock also schedule unattended boots, which doesn't follow. `SeShutdownPrivilege` is the natural Windows-precedented gate for power-state authority, and is the one Peios uses.

`hwclock`-equivalent userspace tools (operator commands for inspecting and adjusting the hardware clock) run as privileged operator commands, holding `SeSystemtimePrivilege` for their lifetime.

`CONFIG_RTC_SYSTOHC` controls whether the kernel automatically writes `CLOCK_REALTIME` back to the RTC during shutdown. Peios enables this — without it, drift corrections accumulated during runtime are lost across reboot.

## NTP kernel discipline

The kernel provides a built-in NTP-style PLL/FLL (Phase-Locked Loop / Frequency-Locked Loop) state machine accessible through `adjtimex` / `clock_adjtime`. A timesync daemon (chronyd-equivalent on Peios) measures the offset between local time and a reference clock, then feeds adjustments to the kernel's PLL via `adjtimex(ADJ_FREQUENCY | ADJ_OFFSET, ...)`. The kernel applies smooth corrections — slowing or speeding the clock by a small fraction — to converge on the reference without ever stepping (unless asked to via `ADJ_SETOFFSET`).

State exposed through `adjtimex`:

| Field | Meaning |
|---|---|
| `offset` | Current offset estimate from reference time. |
| `freq` | Current frequency adjustment (parts per million). |
| `maxerror` / `esterror` | Current bounds on the clock's accuracy. |
| `status` | Status bits: `STA_PLL` (PLL active), `STA_PPSSIGNAL` (PPS reference present), `STA_UNSYNC` (currently unsynchronised), `STA_INS` / `STA_DEL` (leap-second pending), and others. |
| `constant` | PLL time constant — controls how aggressively the kernel chases offsets. |
| `precision` | Estimated clock precision. |
| `tolerance` | Maximum frequency deviation the PLL will use. |
| `tai` | Current TAI-UTC offset. |

A pure read (`adjtimex` with `mode == 0`) returns this state without modifying anything. Reads are unprivileged — the same information is broadcast by the timesync daemon to every NTP peer it speaks with, and is observable through ambient channels. Mutation (any non-zero mode value) requires `SeSystemtimePrivilege`.

The PLL-vs-FLL distinction is mostly internal. PLL mode tracks an offset while keeping frequency stable; FLL mode is more aggressive on frequency adjustment. Most timesync daemons use PLL by default and switch to FLL only when the offset is large.

## Leap seconds

Universal Coordinated Time periodically inserts (or theoretically deletes) a "leap second" to keep wall-clock time in alignment with Earth's rotation. When a leap second is announced, the kernel can be told via `adjtimex(ADJ_STATUS, .status |= STA_INS)` and will, at the next 23:59:59 UTC, hold the clock for an extra second — `CLOCK_REALTIME` shows 23:59:60 between 23:59:59 and 00:00:00.

This is **substrate-as-is** kernel behaviour. The contentious question — whether to step the clock at the leap moment, or smear the second across hours, or ignore the leap entirely — is a configuration choice for the timesync daemon, not a kernel decision:

- **Step (kernel default).** Daemon notifies kernel of pending leap; kernel inserts the second at the appropriate UTC moment. Compatible with broadcast-time receivers; some software breaks on minute=60.
- **Smear.** Daemon never tells the kernel about the leap. Instead, it slowly slows the clock for several hours before and after the leap moment, absorbing the second gradually. Software sees no discontinuity but for several hours "1 second" is slightly less than 1 second.
- **Ignore.** Daemon does nothing about the leap. Clock drifts 1s relative to UTC until manually corrected.

The Peios timesync daemon exposes a registry knob (`\System\Timesync\LeapSecondMode`) with values `step` (default), `slew` (smear-style gradual slewing), and `ignore`. This matches what chronyd and ntpd both expose. Default is `step` — server-tier compat, what most operators expect.

## PTP (Precision Time Protocol)

PTP (IEEE 1588) is a network protocol for sub-microsecond clock synchronisation across a LAN. Where NTP gets you milliseconds, PTP achieves tens of nanoseconds by having the receiving NIC hardware capture timestamps at wire arrival, bypassing all OS jitter.

Use cases include telecom infrastructure (4G/5G base stations need synchronised clocks for cell handoff), high-frequency trading (deterministic ordering of events across machines), industrial control (synchronised PLCs), and distributed databases that order events by physical time.

The kernel exposes each **PTP Hardware Clock** (PHC) as `/dev/ptp0`, `/dev/ptp1`, etc. — independent clock devices on PTP-capable NICs. A PHC can be queried via `clock_gettime` with a clockid derived from the PHC fd (`FD_TO_CLOCKID(fd)`), and configured through an ioctl interface.

Common PTP operations:

| ioctl | Purpose |
|---|---|
| `PTP_CLOCK_GETCAPS` | Query PHC capabilities — pin count, supported features, etc. |
| `PTP_SYS_OFFSET` / `PTP_SYS_OFFSET_PRECISE` / `PTP_SYS_OFFSET_EXTENDED` | Read the offset between system time and PHC time, with progressively higher precision. |
| `PTP_PEROUT_REQUEST` | Configure a periodic-output pin (e.g., emit a 1Hz pulse for downstream distribution). |
| `PTP_EXTTS_REQUEST` | Configure an external-timestamp input pin (e.g., receive PPS from a GPS receiver). |
| `PTP_PIN_SETFUNC` | Configure the function of a hardware pin. |
| `PTP_ENABLE_PPS` | Enable PPS output. |

Authority model:

- **File SD on `/dev/ptp*`** controls who can talk to the device. Default DACL grants access to a `PtpServiceUser` SID (or equivalent for the deployed timesync daemon), administrators, and SYSTEM.
- **`SeSystemtimePrivilege`** gates the ioctls that affect PHC time or pin configuration. The privilege provides a second layer — a process that somehow obtains an open `/dev/ptp0` fd still cannot reconfigure pins without holding the privilege.

PTP-capable hardware is rare in general server fleets, common in specific deployment classes. The narrow user base is why pin configuration uses the existing `SeSystemtimePrivilege` rather than a dedicated `SePtpHardwarePrivilege`. The file-SD layer provides the per-device access control; the privilege provides the operation-class gate.

`PTP_SYS_OFFSET_PRECISE` and the extended variants are read-only and unprivileged at the ioctl layer — they need only an open fd on the PHC device.

## See also

- [Clocks](clocks) — the user-facing clock interface.
- [Setting time](setting-time) — `clock_settime`, `adjtimex` mutation, and the privilege gate.
- [Privileges](../privileges/understanding-privileges) — how `SeSystemtimePrivilege`, `SeShutdownPrivilege`, and the rest are defined and granted.
