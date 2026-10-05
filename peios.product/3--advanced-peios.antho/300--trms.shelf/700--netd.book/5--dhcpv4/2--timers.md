---
title: Timers
description: The DHCPv4 client's retransmission schedule in each state, when "nobody answered" is reported, and the lease boundaries T1, T2 and expiry.
---

Every timer is on netd's monotonic clock.

## Retransmission while acquiring [*dhcp4-timers.backoff]

In Selecting, Requesting and Rebooting each transmission schedules the
next one after the current backoff plus a jitter drawn uniformly from −1 s
to +1 s, then doubles the backoff, up to 64 s. The backoff starts at 4 s
on entering each of the three states. So transmissions follow at roughly
4, 8, 16, 32, 64, 64, … seconds.

| State | Transmissions before it gives up | Then |
|---|---|---|
| Selecting | never gives up | — |
| Requesting | four REQUESTs (about 0, 4, 12 and 28 s) | at the next timer, about 60 s, Selecting with a new DISCOVER |
| Rebooting | two REQUESTs (about 0 and 4 s) | at the next timer, about 12 s, Selecting with a new DISCOVER and no option 50 |

[*dhcp4-timers.give-up-schedule]

## "Nobody answered" [*dhcp4-timers.no-offer-once-per-client]

On the third retransmission of a DISCOVER — the fourth DISCOVER, about
28 s after the first — the client reports that no offer came. netd then
records the interface warning `asked for an address; nobody answered` and,
when the profile wants it, falls back to a link-local address (§5.5). The
client keeps discovering.

The report is made at most once in a client's life: the flag is reset only
when a client is started. A client that reported it, then got a lease,
then lost it, does not report it again, so it does not fall back to a
link-local address a second time.

## Lease boundaries [*dhcp4-timers.lease-boundaries]

A lease's T1, T2 and length are measured from the moment its ACK
arrived, and are fixed when the lease is read (§5.3).

- At **T1** a Bound client enters Renewing and sends a unicast REQUEST.
- At **T2** a Renewing client enters Rebinding and sends a broadcast
  REQUEST.
- At the **lease's end** a Rebinding client loses the lease (§5.4) and
  enters Selecting.

A boundary is acted on before any retransmission due at the same
moment.

## Retransmission while renewing and rebinding [*dhcp4-timers.renewal-retransmit]

Each REQUEST in Renewing or Rebinding schedules the next for half the time
remaining to the state's next boundary (T2 while renewing, the lease's
end while rebinding), but never sooner than 60 s from now. With a short
lease the 60 s floor means a state's boundary usually arrives before its
second REQUEST: a 20 s lease renews once at 10 s and rebinds once at
17 s, then lapses at 20 s.

An ACK in either state starts the lease's clock again from that moment.
