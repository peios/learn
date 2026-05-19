---
title: uptime
type: reference
description: Show how long the system has been running.
related:
  - peios/system-and-processes/date
  - peios/system-and-processes/overview
---

`uptime` shows how long the system has been running, along with a few related figures.

```
uptime [options]
```

```
$ uptime
 14:32:08  up 6 days,  3:21,  2 users,  load average: 0.18, 0.24, 0.21
```

The default line packs in four things:

- the **current time**;
- how long the system has been **up**;
- how many **users** are currently logged in;
- the **load average** — a rough measure of how busy the system has been over the last 1, 5, and 15 minutes.

## Options

| Option | Effect |
|---|---|
| `-p`, `--pretty` | Show just the uptime, in a readable phrase — `up 6 days, 3 hours, 21 minutes`. |
| `-s`, `--since` | Show the date and time the system started, rather than how long ago that was. |

## Exit status

`uptime` returns `0`, or non-zero if the boot time could not be read.
