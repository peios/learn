---
title: Bootstrap and First Admin
---

A freshly installed system has an empty principal store and no users.
This section defines how the first administrator comes to exist without
an existing administrator to authorize it.

## The bootstrap authority

The apparent paradox — account creation requires an administrator —
dissolves because the **SYSTEM bootstrap token** exists before any user
(it is kernel-constructed and inherited through peinit; PSD-004,
PSD-007). First-admin seeding therefore runs in the SYSTEM-everywhere
window, before authd is even serving, with full authority. No
circular dependency exists.

## Generalised images

A shipped image MUST NOT contain a machine SID or any
`machine_sid`-relative principal (§3.1). Identity is personalised per
installed instance on first boot. This prevents SID collisions across
clones of one image.

## First-boot setup

On first boot, in setup mode, on the SYSTEM token:

1. lpsd opens its database; finding it uninitialised **and** setup mode
   in effect, lpsd initialises the template:
   - generate the `machine_sid` (`S-1-5-21-X-Y-Z`);
   - initialise `rid_counter` and the password/lockout policy;
   - seed the built-ins: Administrator (RID 500, **disabled**), Guest
     (RID 501, disabled), and the `S-1-5-32` BUILTIN alias groups;
   - create the database file with the tight SD of §3.5.
2. authd starts, connects to lpsd, and signals readiness (§7.1 below).
   CAAP population is deferred (§8); authd applies the default policy of
   §5.2 in the meantime.
3. Because no usable administrator exists yet, the system enters an
   out-of-box (OOBE) setup rather than normal login. A SYSTEM setup
   agent uses lpsd's administration interface (§7.2) to create the first
   administrator as a **new user (RID ≥ 1000)** added to
   `Administrators`, and sets its password. The agent obtains the
   first-admin details interactively, or non-interactively from an
   unattended answer file — one agent, two input modes.
4. Setup mode ends; login frontends are enabled; normal multi-user login
   begins.

lpsd MUST generate the machine SID **only** in setup mode. An
uninitialised or missing database on a *normal* boot MUST be a hard
error that triggers recovery (§7.3), never a silent re-generation of the
machine SID — silent regeneration would orphan every existing principal
if the real database were later restored.

## Setup mode and "usable administrator"

**Setup mode** is signalled to lpsd by peinit via a **kernel-attested
capability** — peinit's `SeTcbPrivilege`-bearing token, which lpsd
verifies by checking the signaller's peer token (§6.2) is peinit — never a
forgeable flag/file/env, and never inferred from the database being absent
or empty. lpsd MUST generate the machine SID and seed the template only
when this attested signal is present, and only once. On a normal boot (no setup signal), an uninitialised or
missing database is a hard error that routes to recovery (§7.3).

A **usable administrator** is at least one *enabled* principal that is a
member of `Administrators` (`S-1-5-32-544`) and holds a `password`
credential factor. The system enters OOBE (step 3 above) iff no usable
administrator exists; otherwise it proceeds to normal login. The built-in
Administrator (RID 500), shipped disabled, does not by itself satisfy this
predicate.

## Startup ordering and readiness

peinit launches lpsd, then authd, early in boot (PSD-007). authd's
startup obligations are: verify its own state (PIP-protected, expected
token), connect to its sources, and signal readiness to peinit, which
blocks until then before launching dependent services. (In a version
with CAAP, authd populates the policy cache before signalling readiness;
that step is deferred here — §8.)
