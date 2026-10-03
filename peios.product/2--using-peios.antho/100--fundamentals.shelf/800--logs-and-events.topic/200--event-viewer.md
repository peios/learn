---
title: Event Viewer
type: how-to
description: Read a machine's logs and events from the desktop — newest first and live, narrowed by source, text, type and time, with every field of a record and a word on anything you may not see.
related:
  - peios/logs-and-events/overview
  - peios/services-and-jobs/controlling-services
  - peios/evctl/using-evctl
---

**Event Viewer** shows what eventd has recorded on the machine: the logs
of its services and the events of its kernel and programs. It shows the
newest first, adds new ones at the top as they are recorded, and shows any
record in full.

It asks eventd as you, so it shows exactly what you may read, and it says
when something is kept from you.

## Opening it

- From the launcher: start **Event Viewer**.
- From Services Manager: select a service and choose **Logs…**, in the
  details pane or on the row's right-click menu. Event Viewer opens on
  that service's logs, including its hooks' and health checks'.
- From a program: `gxwi-event-viewer --logs NAME` opens on what `NAME`
  logged, and `gxwi-event-viewer --events` opens on the events.

A window opened on one service or one type of event says so in its title,
such as **Event Viewer: sshd**, so several windows can be told apart.

## Logs

Select **Logs** at the top left. Each row is one line, with when it was
written, where it came from and what it says. Lines written to standard
error are shown in red.

To narrow them:

- **From** takes a service's name, and shows its lines and those of its
  hooks and health checks. It suggests the names that have logged.
- **Containing** shows only lines with that text in them, in any case.
- **Errors only** shows only lines written to standard error. Many
  programs write everything to standard error, so this narrows less than
  its name suggests.

## Events

Select **Events**. Each row is one event, with when it happened, its
type, its source, and its own fields in one line.

To narrow them:

- **Type** takes an event type, such as `access.denied`. A `*` stands
  for any part of a type, so `job.*` is every job event and `*.denied`
  every refusal. It suggests the types that have been recorded.
- **Source** shows only events from programs, the kernel, security
  (KACS) or the registry (LCS).

## The time range and applying a filter

Both tabs look back over the **last 24 hours** at first. The list beside
the filters changes that, to 15 minutes, an hour, 7 days or any time.
Searching for text and the suggestions cover the whole range, so a
shorter range is quicker on a busy machine.

Typed filters apply when you press **Enter** or select **Apply**. **Errors
only**, **Source** and the time range apply as soon as you change them.

## Following new records

While the **Pause** button shows a dot, new records appear at the top as eventd
stores them, usually within a second. Select **Pause** to keep the list
still while you read, and **Resume** to show the newest again and carry
on following.

If following stops, because eventd restarted or the window fell too far
behind a burst of records, Event Viewer says so above the list. Select
**Show the newest** to start again.

## Older records

The list starts with the newest 200 records. **Show older**, at the
bottom of the list, adds the 200 before them. When there are no more in
the time range, it says so.

A window holds at most 1,000 records. Past that, the newest are let go to
make room and the window stops following. It says so at the top, with
**Show the newest** to go back. **Show older** carries on as before.

## A record in full

Select a row to see all of it in the pane on the right: for a log line,
its whole text, its stream, its job and its boot; for an event, every
field, the standard ones first under plain names, with the field's own
name beneath. Times are shown to the nanosecond, on this machine's clock.

- **Show only…** narrows the list to that record's source or type. A
  row's right-click menu does the same.
- **Copy** copies every field, one per line.

The **Up** and **Down** arrow keys move through the list, and **F5**
reads it again from the newest.

## What you may not see

eventd leaves out what you may not read without saying so. Event Viewer
reads eventd's read policy as you and says what it keeps from you, at the
bottom right of the window:

| It says | Which means |
|---|---|
| Nothing | You may read everything of that kind |
| Hidden from you: logs from sshd\*, … | The policy keeps those names from you; the rest are shown |
| Only some events are yours to read | Only names the policy lists for you are shown |
| You can't read events on this machine | Nothing of that kind is yours to read |
| Some logs may be hidden from you | The policy itself could not be read, so Event Viewer cannot tell |

If eventd does not let you ask it anything at all, the list says so
instead of showing nothing.

## In a terminal

`evctl` asks eventd the same questions in its query language. The window's
filters are its `LOGS FROM`, `CONTAINING`, `ERROR ONLY`, `EVENTS <type>`
and `SINCE` clauses, so anything the window shows, `evctl` can print. See
[Using evctl](~peios/evctl/using-evctl).
