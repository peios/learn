---
title: Claim Operations
---

This section defines the operations that grant, revoke, and
withdraw the holder of a role (§4.4). *Grant* and *revoke*
are the operator's explicit verbs; *withdraw* is what happens
automatically when a package that made a claim is removed.
Claims are materialised on the filesystem within the same
transaction model (§7.4) as install, upgrade, and uninstall.

## Auto-claim on install

When a package that is an eligible provider of one or more
roles (§4.4.3) is installed, the package manager by default
claims every such role that is currently *unheld*. The newly
installed provider becomes the holder, and the role's claim
paths are materialised against its targets (§4.4.4).

Auto-claim applies only to unheld roles. Installing a
provider of a role that another installed package already
holds does NOT change the holder by default; the new provider
is installed and eligible, but the incumbent keeps the role
unless the operator directs otherwise (§7.7.2, §7.7.5).

> [!INFORMATIVE]
> Auto-claiming unheld roles means a freshly installed sole
> provider "just works": install `loregd` and
> `/usr/bin/registryd` appears, with no second command.
> Leaving held roles alone means installing an alternative
> provider never silently steals a live system name out from
> under the incumbent.

## Install flags

The install operation (§7.1) accepts three flags that modify
claim behaviour. Let the *provided roles* of a package be the
roles for which it is an eligible provider (§4.4.3).

- `--no-claim`: claim nothing. No role is claimed, including
  unheld ones. The provider is installed and eligible but
  holds nothing.
- `--claim <roles>`: a comma-separated list of role names to
  claim. Each named role is claimed even if another package
  currently holds it (an override, §7.7.5). Roles not named
  remain subject to default auto-claim (§7.7.1).
- `--claim-all`: claim every provided role, including those
  another package currently holds.

The claim set applied at install is computed as the union of:

- the **auto set** — the provided roles currently unheld —
  which is empty when `--no-claim` is given; and
- the **force set** — the roles named by `--claim`, or all
  provided roles under `--claim-all`.

Roles in the force set are claimed even when held; roles in
the auto set are claimed only because they are unheld.

> [!INFORMATIVE]
> The flags compose. `--no-claim --claim registryd` empties
> the auto set and forces exactly `registryd`: it claims that
> one role and nothing else — not even a second, unheld role
> the package provides. This is the idiom for "claim only
> this".

A flag combination MUST be rejected as an error when it is
self-contradictory:

- `--claim-all` together with `--claim <roles>`;
- `--claim-all` together with `--no-claim`.

`--no-claim` together with `--claim <roles>` is NOT
contradictory: it is the "claim only these" idiom above.

A role named by `--claim` that the package does not provide
MUST be rejected with an explicit error: a package cannot
hold a role it is not an eligible provider of (§4.4.3).

## The claim command

The package manager provides a `claim` command for inspecting
and changing holders independently of install:

- `peipkg claim <role>` — report the role's current holder,
  its materialised claim paths, and the other installed
  eligible providers.
- `peipkg claim <role> grant <package>` — make `<package>`
  the holder of `<role>`, repointing the role's claim links
  (§4.4.5). `<package>` MUST be an installed eligible
  provider of `<role>`; otherwise the command MUST fail with
  an explicit error.
- `peipkg claim <role> revoke` — revoke the current grant,
  removing the role's claim links and leaving it unheld.

A role is addressed by name, not by path. Because a role has
a single holder across all its slots and paths (§4.4.5),
granting a role moves every one of its claim paths together.

> [!INFORMATIVE]
> Addressing by role name rather than by claim path keeps
> multi-path and multi-slot roles coherent:
> `peipkg claim registryd grant loregd` moves the whole role,
> however many files it materialises, in one operation. A
> path-addressed form would invite a role being half-moved.

A `grant` or `revoke` executes within a transaction (§7.4)
and is rolled back on failure like any other operation.

## Materialisation within a transaction

Claim materialisation, repointing, and removal are file
operations and occur in the apply phase of the transaction
commit procedure (§7.4.5 step 2), alongside payload file
operations. Claim-holder state is recorded in the package
database as part of the transaction's database commit (§7.4.5
step 3) and becomes visible only on commit (§7.4.8).

Because the holder change is part of one transaction:

- a crash before commit rolls the claim change back with the
  rest of the transaction (§7.4.7); the prior holder's links
  are restored from the backup map (§7.5.1.3);
- a holder swap never exposes a window in which a role's
  claim path is absent (§4.4.5).

The package manager MUST record, for each held role, the
holding package, so that holder state survives across
invocations and is removed when the holder is uninstalled
(§7.7.6). The storage schema is implementation-defined,
subject to the package database's transactional guarantees
(§7.4.8). Holder state is recorded independently of whether
any claim link exists: a role may be held with an empty
materialised set (§4.4.4).

A transaction MUST reconcile (§4.4.4) every role whose inputs
it changes, not only roles whose holder it changes.
Installing a package that declares a consumer-side claim path
for a role that is already held MUST retroactively
materialise that path against the current holder; removing
such a package MUST remove the claim links that only it
declared. After the transaction, the materialised links for
every affected role MUST equal that role's computed claim set
for the resulting state (§4.4.4).

## Granting and overriding

Granting a role to a package that is not its current holder
is an *override*: the role's claim links are repointed from
the incumbent's targets to the new holder's targets (§4.4.5).
The incumbent remains installed and eligible; it simply no
longer holds the role.

An override is requested explicitly — by `--claim` or
`--claim-all` at install (§7.7.2), or by
`peipkg claim … grant` (§7.7.3). The package manager MUST NOT
override a held role as a side effect of any operation the
operator did not direct; in particular, auto-claim (§7.7.1)
never overrides.

*Revoking* a role (`peipkg claim <role> revoke`, §7.7.3) is
the operator-initiated inverse of a grant: the current grant
is taken away, the role's claim links are removed, and the
role becomes unheld. It is distinct from *withdrawal*
(§7.7.6), which is the same end state reached automatically
when the holding package is uninstalled — a package
withdrawing its own claim, rather than an operator revoking a
grant.

## Holder removal and withdrawal

When the package that holds a role is uninstalled (§7.3), the
role's claim is *withdrawn*: the package manager removes the
role's claim links within the uninstall transaction and the
role becomes unheld (§4.4.5). The package manager MUST NOT
automatically promote another eligible provider in the
holder's place.

If other eligible providers of the role remain installed, the
package manager MUST surface the withdrawal to the operator,
naming them and the command to assign a new holder:

```
Claim 'registryd' withdrawn — packages 'altregd', 'thirdregd'
also provide it. Run 'peipkg claim registryd grant altregd'
to assign a new holder.
```

> [!INFORMATIVE]
> Withdrawal leaves the role unheld rather than
> auto-promoting because the choice of replacement holder is
> the operator's: the remaining providers are alternatives
> that were deliberately not chosen while the incumbent held
> the role. Auto-promoting one would silently re-point a
> contended system name to a provider the operator never
> selected. Surfacing the alternatives with a ready-to-run
> grant command makes reassignment one step without making it
> implicit.

Whether withdrawing a role is safe depends on its consumers
(§4.4.7). If every installed consumer reaches the role
through an `optional_dependencies` entry, withdrawal breaks
no required dependency and is informational. If a required
dependency (§4.1) is left with no holder for a name it
hard-codes, the operator is removing a package the running
system needs; this is the system-critical-removal scenario of
§7.3, and the foot-gun guard there (an explicit override
flag) applies.
