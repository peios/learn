---
title: The time zone, and setting the clock by hand
type: how-to
description: Choose the machine's time zone, set the clock yourself where there is no time server, and do both from System Settings or a terminal.
related:
  - peios/time/overview
  - peios/time/configuring-sources
  - peios/time/the-clock-command
---

The clock always runs in UTC. The **time zone** is how the time is shown:
the offset from UTC, and when summer time starts and ends, for one place.
There is one time zone for the whole machine. Before changing it, inspect
`clock status` and `clock sources`: a wrong zone changes the display, while
an unsynchronised clock needs a source or manual-time correction. Verify
the effective zone in status rather than assuming a saved choice took
effect.

## In System Settings

**System Settings**, from the launcher, has the machine's time in its
**Time & Date** section. A choice from a list or a switch applies the
moment it is made; one that can't be is put back, and the line along the
bottom of the window says why.

- At the top is the time here, the zone and how far it is from UTC, and
  whether the clock is synchronised, and with which time server.
- **Time Zone** lists the zones by region. Every program shows the chosen
  zone from the next time it looks, which for the desktop's clock is the
  next minute. **UTC** takes it away.
- **Set Time Automatically** is on until you turn it off. Then a date and
  a time open under it, in the zone chosen, with **Set Clock**. Turning the
  switch on again goes back to the time servers. **It starts them afresh
  and can jump the clock by any size when sources agree.** Plan for the
  effect on timers, file timestamps and log ordering before switching it
  on.
- **Time Servers** are where the time comes from: **Change…** opens the
  list under its row, and **Allow Unauthenticated Servers**, **Use Network
  Time Servers** and the minimum and maximum poll intervals apply as they
  are changed. See [configuring time
  sources](~peios/time/configuring-sources). **Server Status** lists each
  server: whether it is in use, a candidate, or rejected, whether it is
  authenticated (NTS), its offset, and when it was last heard.

Changing the settings needs write access to `Machine\System\Time`, which
as shipped only Administrators have. Anyone else sees all of it, and the
section says once, at the top, why they can't change it. Asking timed to
set the clock or reload separately needs its control right, granted by
default to SYSTEM and Administrators. The [control
descriptor](~peios/time/the-clock-command#when-reload-is-refused) and the
registry key's write permissions are separate checks.

After a change, check the zone and synchronisation shown at the top, and
**Server Status** when using automatic time. A saved setting is not proof
that a source has been accepted or that the clock has synchronised.

## In a terminal

The time zone is `Machine\System\Time TimeZone`, a name from the tz
database such as `Europe/London`, `America/New_York` or `Asia/Kolkata`:

```
$ reg set Machine/System/Time TimeZone sz:Europe/London
$ clock status | head -2
generation   12
time zone    Europe/London
```

timed puts the zone in `/etc/localtime` within a second. A name that isn't
a zone on this machine is refused and logged, and the zone in force stays
as it was; `clock status` shows which one that is, even after timed
restarts. timed tries the name again every ten minutes and whenever the
time settings change, so a zone that a tzdata update adds is taken up
without setting the value again. Deleting the value is UTC.

The names are the files under `/usr/share/zoneinfo`, from the tzdata
package. `zone1970.tab` there lists the ones worth choosing between, one
per region whose clocks have agreed since 1970.

To set the clock yourself, first check the effective zone with `clock
status`. You need registry write access to turn automatic time off and
timed's control right to set the clock. A manual set is a jump: plan for
its effect on timers, file timestamps and log ordering before proceeding.
Then turn off setting it automatically and ask timed:

```
$ reg set Machine/System/Time Automatic dword:0
$ clock set 2026-10-04 14:05
the clock is set
```

`clock set` takes a local time, in the machine's zone. timed refuses while
`Automatic` is 1, since its next poll would put the clock back. Inspect
`clock status` after the set: check the effective zone and the
`Automatic is 0: the clock is set by hand` indication. Manual time is not
network synchronisation.

Setting `Automatic` to 1 again starts the time servers afresh. **Once
usable sources agree, the initial correction can be of any size.** Plan
for that clock jump before re-enabling automatic time. Afterwards, run
`clock status` and `clock sources` and check the selected sources,
authentication, state, accuracy and fresh updates. Re-enabling the setting
does not itself prove synchronisation.

## Why not just set the clock?

Administrators hold `SeSystemtimePrivilege`, so `date -s` would set the
clock. timed would then measure the clock as wrong by that much and put it
back, and if it was more than 1000 seconds after timed had been keeping
the clock, it would refuse to follow its own sources and log it as a
problem. Asking timed is what keeps the two in agreement.

A clock set by hand is written to the hardware clock within eleven
minutes, so it survives a reboot.

Asking timed also leaves a record. Each set is a `timed.clock.stepped`
event with `operation.name` `manual`, the clock's reading just before and
just after, and the SID of whoever asked in `subject.token.sid`. `date -s`
leaves none: the clock moves underneath every record without anything
saying so.
