---
title: Network Manager
type: how-to
description: See and change this machine's interfaces, networks, profiles, name resolution and firewall on the desktop with Network Manager — what each section shows, how a change that could cut you off is checked and kept, and what you may see and change.
related:
  - peios/networking/overview
  - peios/networking/configuring-profiles
  - peios/networking/network-policy
  - peios/networking/network-policy-reference
  - peios/networking/name-resolution
  - peios/networking/the-pnp-viewer
  - peios/network-objects/port-reservations
  - peios/logs-and-events/event-viewer
---

**Network Manager** is the desktop's window on this machine's networking
and its firewall. Open it from the launcher (type `network`). Down the side
are three groups:

- **Network:** Overview, Networks, Profiles, Profile rules and DNS.
- **Firewall:** Exposure, Rules and Activity.
- **System:** Port reservations, Auditing and Advanced.

What it shows comes from netd, resolvd, the kernel and the registry under
`Machine\System\Network`. What it changes it writes to the registry, as
you, the same as you could with `regman`. Nothing else holds the network's
settings: see [Networking](~peios/networking/overview) for how they become
real.

> [!NOTE]
> Some of the firewall's live state is example data today. Which services
> are listening, the connections open now, the firewall's counters and its
> recent audit events can't yet be read by programs: only the kernel can
> read them. Until they can, Network Manager makes up an example from this
> machine (its own addresses, and the desktop connections really open now)
> and judges it by your real rules. Every section that shows it says
> **Example data**, and the status line says **Example**. The rules
> themselves, and everything outside the firewall, are real. On an
> Experimental image, [the PNP viewer](~peios/the-pnp-viewer) shows the
> engine's own verdicts and live flows.

## Overview

Along the top is a summary: whether the machine is **Connected** (it has a
way out), **Local network only**, **Connecting** or **Offline**, and its
IPv4 address, gateway, DNS servers and hostname.

Under that is a map. Each interface is a line from this machine to the
network it is on, with the profile it uses on the wire between them, and
the internet at the end when there is a route out. An interface no rule
assigns a profile to is **Not managed**. Wi-Fi isn't supported yet, so a
wireless interface is always shown that way.

Select an interface to see it in full:

- its state and speed, with **Renew lease** to ask the DHCP server for a
  fresh lease, and **Reapply** to make every interface match its profile
  again;
- its **Addresses**, each with where it came from: DHCP, Static, SLAAC,
  Temporary (an IPv6 privacy address) or Link-local, and **Deprecated** for
  one kept only for connections already using it;
- its gateway and route metric, its DNS servers and search domains, its MTU
  and MAC address;
- its **Traffic**, received and sent, over the last minute;
- its **Configuration:** the profile it uses, the rule that chose it, and
  the network it is on;
- its **Routes**;
- its **DHCP lease**, as a bar from when it was obtained to when it
  expires, marked where the machine starts to renew it and then to rebind.
  Older versions of netd don't report a lease's times, and then the lease
  is shown as three stages instead, **Bound**, **Renewing** and
  **Rebinding**, with the current one lit.

An interface that isn't managed has **Assign a profile**, which starts a
profile rule for it.

If netd isn't answering, the page says so and shows what netd last
recorded. If netd refused the newest profile rules, it says why, and that
the last rules that worked still apply.

## Networks

**Networks** lists every network this machine has connected to: its name,
its trust level, what identifies it (its DHCP server or router), its
subnet, and when it was last connected. A network seen for the first time
is marked **New network** until you give it a name and a trust level.

Select one to change:

- its **Name**;
- its **Trust level:** **Private**, a network you control, or **Public**,
  any other network. A network never given one is offered as Public;
- its **Preferred address**, an IPv4 address the machine asks for first.
  The DHCP server may give another.

Rules can name a network and its trust level, so changing either can change
what is reachable or which profile an interface uses. Before you save,
**What this changes** lists each listening service and interface that
would be treated differently.

## Profiles

A profile says how an interface stands on a network: what it takes from the
network and what it sets for itself. A profile inside another inherits
every setting from it and changes only what it sets. See
[Configuring profiles](~peios/networking/configuring-profiles) for what
each setting means.

On the left is the tree of profiles, with the interfaces using each. Under
it, **New profile** makes one at the top, **Inside** makes one inside the
selected profile, and **Delete** removes the selected profile and the
profiles inside it. A profile a rule still names can't be deleted.

On the right, the selected profile is summed up in five boxes, Addressing,
Gateway, DNS, Hostname and MTU, each coloured by whether it comes from the
network, is set here, or both. Below them is every setting, with a column
for each profile from the top of the tree down to the selected one. The
selected profile's column can be changed; the others show what it
inherits. **Result** gives the value that applies, and which profile it
comes from, or **built in** when none sets it. Choose **Inherit** (or
**Default** at the top of the tree) to stop setting a value here.

Changes wait in a bar, **1 change not applied**, with **Discard** and
**Apply**. The bar says which interfaces the change will apply to at once,
or why the machine would refuse it.

## Profile rules

**Profile rules** says which profile each interface uses. **Now** lists
each interface, the profile it uses, and the rule that chose it. Under
that are the rules. The most specific rule that matches an interface
applies; priority breaks ties. An interface no rule matches is left
unmanaged.

A profile rule's action is **Use profile** (with the profile), **Unmanaged**
(leave the interface exactly as it is), **Disabled** (keep it switched off)
or **None**. Rules are written and changed as on the firewall's
[Rules](#rules) page. Before you save, **What this changes** lists each
interface that would use a different profile, and a rule that would tie
with another at the same priority is marked.

## DNS

**Look up a name** asks resolvd for an IPv4 (A) or IPv6 (AAAA) address,
and shows the way the question went: the static names, the cache, the
interface it was routed to and why, the server that answered, and the
answer, or **No such name** or **No answer**.

**Where names go** shows which interface's servers each name is sent to:
names ending in an interface's search domain go to that interface, and all
others to the default route. **Since resolvd started** counts the
questions asked, how many the cache answered, and how many went to servers
and failed. **Flush cache** empties the cache.

Under **Settings** are the **Fallback servers**, used only when no
interface has DNS servers, and extra **Search domains**, tried after each
interface's own. **Static names** are answered before DNS is asked. See
[Name resolution](~peios/networking/name-resolution) for how resolvd
decides.

## Exposure

**Exposure** answers one question: which services on this machine can be
reached, and from where. Each listening service is a row, with **Any other
port** at the end for everything else. The columns are **Private
networks**, **Public networks** and **This machine**. Each cell is
**Allowed**, **Limited** (allowed, with exceptions that block some of it),
**Blocked**, or **Not listening** when the service only takes connections
from this machine. Under each is the rule that decided it.

Each cell is judged by your real rules, as a new connection from a network
of that trust level. Which services are listening is example data for now.

Select a cell to see why: the same explanation as **Test a connection**
on [Rules](#rules). Its button changes it in one step, **Allow from public
networks** or **Block from private networks**, for example, by the smallest
change to the rules that does it: narrowing a rule to the other trust
level, turning it off, or adding a rule that allows the port. Where no one
rule decides a cell alone, you are told to change it in Rules.

## Rules

**Rules** holds the firewall's rules, in three tabs:

- **Connections**, judged once per connection. Most rules belong here.
- **Packets**, every packet, after connection tracking.
- **Frames**, before connection tracking. Rarely needed.

Exceptions sit under the rule they narrow. Order has no effect: the highest
priority wins, and a tie goes to the stricter action. Traffic no rule
allows is blocked. Rules that come with Peios or its packages are marked
**Built-in**. [Network policy](~peios/networking/network-policy) explains
how rules decide.

Select a rule, or **New rule**, to write one:

- its **Name**, **Priority** and whether it is **On**;
- what it **Matches**, as conditions on facts such as the source address,
  the port or the network's trust level;
- its **Action:** **Allow**, **Block** (discard without a reply, so the
  sender sees a timeout), **Reject** (refuse, and reply "connection
  refused" or "administratively prohibited") or **None** (decide nothing
  and let the rule it is inside decide);
- **Also:** **Count**, **Tag**, **Audit** and **Prompt**, which run
  alongside the action;
- its **Exceptions**, with **Add exception**.

The rule is checked as you write it. A condition that can never match, a
missing value, and anything the machine would refuse are marked where they
are, and it can't be saved until they are fixed. **What this changes**
lists each service whose reachability would change.

**Test a connection** describes a connection, incoming or outgoing, its
protocol, the other machine's address, the port, the network and the
service, and shows what the firewall would do with it: each layer it
passes, in the order the kernel judges them, which rule decides, and every
rule's part in it. There are ready-made examples, such as **Your session**
and **SSH from a café**. A blocked incoming connection offers **Make an
allow rule…**.

## Activity

**Activity** shows what the firewall has been deciding: a chart of new
connections a minute over the last fifteen minutes, allowed, rejected and
blocked. Under it, **Connections** lists the connections open now, in or
out, with the network, the result and the rule that decided it; a connection
to this desktop is marked **Your session**. Select one to see how it was
decided. **Counters** shows each count a rule with a Count action keeps,
which rules write and read it, and, by source, whether it is over a rule's
limit.

All of it is example data for now, judged by your real rules.

## Port reservations

A port reservation says who may listen on a port. Each port uses its
narrowest reservation, and a port without one uses the default. A bar draws
the reservations across the ports from 1 to 65,535. The table lists each,
with who can listen; **Permissions…** changes that. To add one, write it as
protocols and ports, such as `tcp:8443` or `tcp,udp:5000-5100`. A new
reservation starts with only SYSTEM and Administrators allowed to listen.

**Check a port** says whether a program running as SYSTEM, an
administrator, a standard user or one of Peios's services could listen on a
port, and which reservation decides. Who may connect to the port is the
firewall's to say, on [Exposure](#exposure). See
[Port reservations](~peios/network-objects/port-reservations) for how the
kernel checks them.

## Auditing

A rule with an **Audit** action writes an event each time it decides, at a
level from 1 to 5. **Record events from level** chooses the lowest level
recorded: **1** records everything, **5** only the most severe, and **Off**
nothing. **Rules that audit** lists each such rule, its level, and whether
it is recorded.

Recorded events are in [Event Viewer](~peios/logs-and-events/event-viewer),
as `ntfe.verdict.reported` events. **Recent events** here is example data
for now.

## Advanced

**DHCP identity** shows the DUID this machine gives DHCP servers, and each
interface's **Client ID**, which is derived from the DUID when it is
empty. A client ID is written as bytes in hex, such as
`01:52:54:00:12:34:56`.

**Access** says who may look at and who may change netd's and resolvd's
settings. **Permissions…** beside each opens it in the permissions editor.
The hostname is shown here, and changed in System Settings.

## Making a change

Every change is checked before it is written. If the machine would refuse
it, nothing is written, and the status line says why.

A change that would block a connection to this desktop that is open now,
yours or anyone else's, asks first: **This change would disconnect you**,
with the connections it would cut. **Cancel** is the safe answer. **Apply
anyway** makes it.

Some changes are kept only when you say so. A bar across the top asks
**Keep this change?**, with **Keep** and **Undo**, and undoes the change
by itself after 30 seconds unless you keep it. The countdown runs on the
machine, not in your browser, so if the change did cut you off, you need
do nothing: the previous settings come back when it ends. The bar follows:

- saving or deleting a firewall rule or a profile rule;
- changing a cell on Exposure;
- applying a profile that an interface carrying a desktop connection uses;
- renaming a network, or changing its trust level, while a desktop
  connection is on it;
- any change made with **Apply anyway**.

Making another of these while the bar is up keeps the change before it.
Other changes, such as DNS settings, static names, port reservations, the
audit level and new profiles, are made at once, and there is no **Undo**.

The status line along the bottom says what the last change did, and that
the firewall's policy is in force, with its generation. If the kernel
refused the newest rules, it says so, and that the previous generation
still stands.

## What you may see and change

What you may change is what the registry lets you write, key by key, so
it is asked of the machine, not guessed from your groups. Where you may
not, a section is shown read-only, with the reason said once at the top:
**You can see these settings. Changing them needs an administrator.**
Exposure and Activity are for administrators only, and say so instead.

**Permissions…** opens the permissions editor. It shows the same things
read-only to anyone who may not change them.

Network Manager reads the machine again every two seconds, and its
settings whenever something else changes them in the registry.
