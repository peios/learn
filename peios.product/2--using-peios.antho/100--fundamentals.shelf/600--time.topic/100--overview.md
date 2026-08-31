---
title: Keeping the time
type: concept
description: How a Peios machine knows what time it is — timed, authenticated network sources, and why the default is three independent operators rather than one.
related:
  - peios/time/configuring-sources
  - peios/time/the-clock-command
  - peios/trust/overview
---

The machine's clock is kept by **timed**, and timed is the only process on
the machine permitted to set it.

That is not a figure of speech. Setting the clock needs
`SeSystemtimePrivilege`, which is granted to timed's service identity and
to nothing else, so "what on this machine can change the time" has a
one-line answer that an administrator can check.

## Why this is worth caring about

A wrong clock does not look like a wrong clock. It looks like:

- certificates that are expired, or not yet valid, and TLS that fails for
  reasons that make no sense;
- Kerberos tickets refused across a domain, because Kerberos treats a
  clock skew as evidence of a replay;
- logs from two machines that cannot be put in order, which is exactly
  when you most need them to be.

So time is not a convenience. It is something several other things quietly
depend on, and an attacker who can move it has more than a wrong clock.

## Sources are not trusted individually

timed polls several servers and does **not** believe any of them. Each one
reports not a time but an *interval* it promises the true time lies
within, and timed looks for the largest set of intervals that overlap. A
server outside that overlap is a **falseticker** and is discarded, however
confident it sounded.

The consequence is worth stating, because it is what makes the scheme
work: a server that claims great accuracy and is wrong excludes *itself*.
Its interval is narrow, so it cannot reach the agreement. Overclaiming is
the one lie the arrangement punishes automatically.

With three independent sources this survives one liar. With two that
disagree there is no way to tell which is right, and timed reports itself
unsynchronised rather than guessing — which is why the shipped default is
three operators and why you should configure at least three of your own.

## Every source is authenticated

By default timed will not use a source that cannot prove who it is. That
is **NTS** (RFC 8915): a TLS handshake on port 4460 establishes a pair of
keys, and every NTP packet afterwards carries a tag computed with them.
Forging a reply requires the key.

The certificate is validated against [the machine's trust
store](~peios/trust/overview), over trustd's socket — so a certificate
authority you distrust is distrusted here too, immediately, without timed
needing to be restarted.

On a network that blocks port 4460 the honest outcome is a machine that
says it is unsynchronised. `AllowUnauthenticated` exists for networks
where that is not acceptable; see [configuring
sources](~peios/time/configuring-sources) for what you give up.

## The default sources

A machine that has been told nothing uses four names in our own zone:

```
0.time.peios.org    →  time.cloudflare.com
1.time.peios.org    →  nts.netnod.se
2.time.peios.org    →  ptbtime1.ptb.de
3.time.peios.org    →  ptbtime2.ptb.de
```

Three independent operators in three jurisdictions — a commercial network,
a Swedish national infrastructure operator, and Germany's national
metrology institute. Independence is what makes the votes worth counting:
three servers run by one operator would agree with each other about
anything.

The indirection through `time.peios.org` is deliberate. If an operator
withdraws its service, that is a DNS change rather than a new image for
every machine.

## Two circles, and how they are broken

Both are worth knowing about, because both look like bugs when you meet
them.

**NTS needs TLS; TLS needs a clock.** A machine whose battery has died
boots reading 1970, and every certificate it holds is "not yet valid", so
it cannot complete the handshake that would tell it the real time. timed
breaks this by refusing to let the clock sit below **its own build
timestamp** — every certificate in the shipped trust store was valid at
that moment, by construction. The clock is wrong, but it is wrong in a way
that TLS tolerates, and the first poll fixes it. `clock status` reports
the floor so that "my clock is being clamped" is visible rather than
mysterious.

**A fresh handshake needs a clock too.** So the cookies from the last one
are kept under `/var/state/timed`, and a reboot usually needs no handshake
at all.

## Steering, not jumping

Once the time is known, timed **slews** the clock: it changes the rate
slightly so the error is absorbed over the next few minutes. A great deal
of software quietly assumes the clock only goes forwards, and stepping it
backwards breaks timers, file timestamps and anything measuring a
duration.

The clock is stepped in exactly two situations:

- **at startup**, once, however large the correction — this is what lets a
  machine with a dead battery start correctly;
- **after fifteen minutes of consistent disagreement**, when the offset is
  too large to slew away. Fifteen minutes because a congested network or a
  server having a moment looks exactly like a genuine step until time
  passes, and stepping the clock on a transient is worse than being slow
  to correct a real one.

An offset larger than a thousand seconds appearing *after* the machine was
synchronised is refused outright and logged loudly. A machine that far out
has a problem a time client should not paper over.

## Learning the crystal

The clock is a crystal running at the wrong rate — consistently wrong, by
some tens of parts per million. timed learns that rate and writes it to
`/var/state/timed/drift`, so the next boot starts already correcting for
it and is within milliseconds after one poll rather than after twenty.

It is also what holds the clock right when the network goes away: a
machine that knows its crystal is 12 ppm fast stays within a second for
about a day on its own.

## What timed does not do

**It is not a time server.** It listens on no network port and initiates
every conversation it takes part in. Serving time to other machines will
be a separate, unprivileged package — the client holds the dangerous
privilege, and a server is exposed to the whole network and needs no
privilege at all. Keeping them apart is the point.

**It does not touch the hardware clock directly.** Once timed reports the
clock as synchronised, the kernel writes it back to the RTC every eleven
minutes on its own.
