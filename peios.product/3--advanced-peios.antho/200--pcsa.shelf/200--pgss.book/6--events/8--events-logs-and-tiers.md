---
title: Events, Logs and Tiers
description: The two tests that decide whether something is an event, a log line or a metric, and the four tiers an event type declares — essential, standard, verbose and debug — with what makes an event essential.
---

## Event, log or metric

An **event** is a discrete occurrence that someone may search for, alert
on, or attribute to a principal, one record at a time. It carries an
identity the kernel stamped (PSPK §2).

A **log line** is narrative for the people who maintain a component. Its
value is in reading the sequence, not in querying single records.

A **metric** is a sampled quantity, where the trend matters and no single
sample does.

An emitter MUST decide between them by two tests, in order:

1. **Does an operator care?** Events and metrics are for operators; logs
   are for developers. If an operator would not act on it, it is a log
   line, and the second test does not apply.
2. **Does one instance matter on its own?** If it does, it is an event,
   however frequent it is. If only the trend matters, it is a metric.

An emitter MUST NOT carry log text in an event. A message a person reads
belongs in `outcome.detail` (§6.6) where it explains the outcome, and in
the log otherwise.

> [!NOTE]
> An operator should not need to read logs in all but the rarest cases.
> If they do, something that should have been an event was written as a
> log line.

## Tiers

Every event type declares one tier in its fragment (§6.10). The tiers are
a closed set.

| Tier | Meaning | On unless the policy says otherwise |
|---|---|---|
| `essential` | Extremely important and relatively rare, or governed by its own configuration | Always; cannot be switched off |
| `standard` | What an administrator reviews: lifecycle, configuration, failures | Yes |
| `verbose` | Detail for an active investigation | No |
| `debug` | For the component's developers | No |

A tier sets only the default. The emission policy switches a type on or
off whatever its tier, except an essential type, which it never switches
off (§6.9). A shipped default policy MUST NOT switch a `debug` type on.

## Essential

An event type is essential for one of two reasons:

- **It is extremely important and relatively rare.** A logon session
  ending, or a configuration value rejected.
- **Its emission is already governed by its own configuration.** The
  kernel's access audit is the example: a SACL, or a token's audit
  policy, decides which occurrences are recorded.

The second reason follows a principle that holds across Peios: **one
switch per thing.** Something already governed by its own configuration
does not also need an emission-policy switch before it works. Making an
administrator turn on the same thing in two places is what this rules
out.

An emitter MUST NOT declare an event type essential for any other
reason.

> [!NOTE]
> Nothing in a running system stops a third party declaring an event
> essential, and nothing tries to. Whether an essential event meets one
> of the two reasons is one of the checks made when a package is
> submitted to the Peios package repository.
