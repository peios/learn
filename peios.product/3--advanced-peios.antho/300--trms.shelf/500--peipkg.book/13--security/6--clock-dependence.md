---
title: Clock Dependence
description: The checks that depend on the local system clock, and what a wrong clock does to each of them.
---

Several checks depend on the local system clock: a signing key's
validity window, the maximum trusted age, index staleness, and build
provenance timestamps.

An attacker able to manipulate the local clock can extend a
transitioning key's validity, evade a staleness check, or hide a
compromise-detection window.

peipkg does not gate on clock sanity, and does not pretend to. There is
no build-timestamp comparison, no time-synchronisation state query, and
no override flag for a clock peipkg thinks is wrong. The
clock-dependent checks assume a sane clock.

> [!NOTE]
> The intended end state refuses operations when the clock is plausibly
> wrong — when the current time precedes peipkg's own recorded build
> timestamp, or when no reliable time source has reported a successful
> synchronisation since boot. A *reliable* source means a
> cryptographically authenticated time protocol, or agreement among
> several independent unauthenticated ones; plain unauthenticated time
> synchronisation, being trivially substitutable by an attacker in a
> network position, does not on its own qualify.
>
> Operators in environments where clock manipulation is a concern will
> want an authenticated time source in use.
