---
title: Event Viewer
type: how-to
description: Read a machine's events, metrics and logs from the desktop — records newest first and live, metrics charted on dashboards of your own, and a word on anything you may not see.
related:
  - peios/logs-and-events/overview
  - peios/services-and-jobs/controlling-services
  - peios/evctl/using-evctl
---

**Event Viewer** shows what eventd has recorded on the machine: the events
of its kernel and programs, the metrics programs publish, and the logs of
its services. It shows events and logs newest first, adds new ones at the
top as they are recorded, and shows any record in full. It charts metrics
on dashboards you arrange.

It asks eventd as you, so it shows exactly what you may read, and it says
when something is kept from you.

## Opening it

- From the launcher: start **Event Viewer**. It opens on the events.
- From Services Manager: select a service and choose **Logs…**, in the
  details pane or on the row's right-click menu. Event Viewer opens on
  that service's logs, including its hooks' and health checks'.
- From a program: `gxwi-event-viewer` opens on the events,
  `gxwi-event-viewer --metrics` on your dashboards,
  `gxwi-event-viewer --settings` on eventd's settings, and
  `gxwi-event-viewer --logs NAME` on what `NAME` logged.

A window opened on one service or one type of event says so in its title,
such as **Event Viewer: sshd**, and on the Metrics tab the title names
the dashboard, so several windows can be told apart.

## Events

**Events** is the first tab. Each row is one event, with when it happened,
its type and its source. Select one to see its fields.

To narrow them:

- **Type** takes an event type, such as `kacs.audit.access.checked`. A
  `*` stands for any part of a type, so `peinit.job.*` is every job event
  and `*.rejected` every refusal of that kind. It suggests the types that
  have been recorded.
- **Source** shows only events from programs, the kernel, security
  (KACS) or the registry (LCS).

## Metrics

Select **Metrics**, between **Events** and **Logs**. On the left is every
metric you may read, with its type and latest value, or how many series it
has. A *series* is one of a metric's sets of labels: `eventd.store.bytes`
has a series for each store, for example. Hold the pointer over a metric
to see each series' latest value. **Find a metric** narrows the list as
you type.

On the right is a **dashboard**: a page of charts over one time range.
Until you make your own, it is **eventd's health**, which charts how
eventd itself is doing: what it stores, whether it is losing events, how
full its stores are, and whether queries are being refused.

### Charts

Select a metric on the left to add a chart of it to the dashboard. A
chart has a line for each series, a legend naming them, and the values
up its left side. Hold the pointer over a chart to see every line's value
at that moment.

A chart divides its range into windows, such as a minute each over the
last hour, and shows one value in each. Select **⋯** on a chart to change
what it shows:

- **Show** is what each value is. A counter, which only goes up, is shown
  as its **rate per second** at first, or as its **change in each
  window**, or **as recorded**. A gauge, which goes up and down, is shown
  as recorded. A histogram, a spread of measurements such as how long
  requests took, is shown as a percentile: the **median**, the **95th**
  or the **99th**.
- **In each window, the** picks the **average**, **least**, **greatest** or
  **total** of the values that fall in each window.
- **Lines** gives **one for each series**, or **one for all of them**
  together.
- **Move earlier** and **Move later** reorder the charts, and **Remove**
  takes one away.

A chart's right-click menu has the same choices.

### Dashboards

The list at the top left picks a dashboard. Beside it:

- Type in the name box and press **Enter** to rename the dashboard.
- The time range is 15 minutes, an hour, 6 hours, 24 hours or 7 days.
- **New dashboard** starts an empty one.
- **Delete…** deletes the dashboard shown, after asking.

Charts are read again every few seconds, more often over a shorter
range. **Refresh**, or **F5**, reads everything again now.

Your dashboards are yours: they are kept in your part of the registry,
at `CurrentUser\Software\gxwi-event-viewer`, and other people have their
own. Delete your last one and eventd's health takes its place again.

## Logs

Select **Logs**, after **Metrics**. Each row is one line, with when it
was written, where it came from and what it says. Lines written to
standard error are shown in red.

To narrow them:

- **From** takes a service's name, and shows its lines and those of its
  hooks and health checks. It suggests the names that have logged.
- **Containing** shows only lines with that text in them, whatever the
  case of the letters.
- **Errors only** shows only lines written to standard error. Many
  programs write everything to standard error, so this narrows less than
  its name suggests.

## The time range and applying a filter

The Events and Logs tabs look back over the **last 24 hours** at first. The list beside
the filters changes that, to 15 minutes, an hour, 7 days or any time.
Searching for text and the suggestions cover the whole range, so a
shorter range is quicker on a busy machine.

Typed filters apply when you press **Enter** or select **Apply**. **Errors
only**, **Source** and the time range apply as soon as you change them,
and so does anything typed and not yet applied.

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

Drag the pane's left edge to make it wider or narrower. The width is
kept while the window is open. On a narrow screen the pane is put away.

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

The Metrics tab says the same of metrics. By default everyone signed in
may read every metric.

If eventd does not let you ask it anything at all, the list says so
instead of showing nothing.

## Settings

Select **Settings**, the last tab, to see how eventd is set up and who
may read what. Anyone may look. Only those allowed to change eventd's
settings may change them, by default administrators; everyone else sees
them read-only, with a line saying why.

### eventd's settings

The settings are in groups: **Keeping records** first, then taking in
events, logs and metrics, answering queries, and storage. Each one says
what it is, what it is set to or that it has its default, the values it
may take, and whether a change applies at once or when eventd next
starts. These descriptions are eventd's own, from its regman page, which
`regman` shows in a terminal.

- Type a value and press **Enter** or **Save** to change one. A value
  outside its range is refused, with the range given, and nothing is
  changed.
- **Use the default** takes a setting back to its default.

eventd notices a change by itself and records it as an
`eventd.config.changed` event, which the Events tab shows. The paths
of its stores and sockets are shown but not changed here: eventd needs
them to point at places made ready for it.

### Who may read what

eventd's **read policy** says who may read which events, logs and
metrics. It is a list of **patterns**, each a name with the permissions
for it:

- `*` covers everything of its kind that no other pattern covers.
- A name, such as `sshd` for logs or `kacs` for events, covers that name
  and every name under it, such as `kacs.audit.access.checked`.

The most specific pattern that matches decides. Each pattern says, in
words, who may read it, who may only read some of its fields, and who may
not. For metrics it also says who may publish them.

- **Change…** opens the pattern in the permissions editor. Changes apply
  from the next question anyone asks eventd.
- **Add a pattern** starts a new pattern for a name, with the permissions
  that apply to that name now, and opens it to be changed. Nothing changes
  until you change it there.
- **Remove…** takes a pattern away after asking. The broader pattern
  above it then decides. The `*` patterns cannot be removed, since eventd
  would let nobody read what they cover.

**Changing eventd's indexes**, at the end, says who may ask eventd to
index a field.

For example, to keep sshd's logs from everyone but administrators, add a
pattern `sshd` under Logs and, in the editor, take **Read** away from
Authenticated Users. Anyone else then sees "Hidden from you: logs from
sshd\*" on the Logs tab.

## In a terminal

`evctl` asks eventd the same questions in its query language. The window's
filters are its `LOGS FROM`, `CONTAINING`, `ERROR ONLY`, `EVENTS <type>`
and `SINCE` clauses, and a chart is a `METRIC` query such as
`METRIC eventd.store.bytes[] SINCE 1h ago MAX_OVER 1m`, so anything the
window shows, `evctl` can print. See
[Using evctl](~peios/evctl/using-evctl).
