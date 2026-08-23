---
title: Install Flags
description: The three flags that modify what an install claims, the contradictions between them, and naming a role the package does not provide.
---

Three flags modify what an install claims. Let the *provided roles* of a
package be the roles it is an eligible provider of.

| Flag | Effect |
|---|---|
| `--no-claim` | Claim nothing, including unheld roles |
| `--claim <roles>` | Claim each named role, even if another package holds it |
| `--claim-all` | Claim every provided role, including held ones |

The claim set applied is the union of two sets:

- the **auto set** — the provided roles currently unheld — which is
  empty under `--no-claim`; and
- the **force set** — the roles named by `--claim`, or every provided
  role under `--claim-all`.

Roles in the force set are claimed even when held. Roles in the auto set
are claimed only because they are unheld.

> [!NOTE]
> The flags compose. `--no-claim --claim registryd` empties the auto set
> and forces exactly one role: it claims that role and nothing else, not
> even a second unheld role the package provides. This is the idiom for
> "claim only this".

## Contradictions

Two combinations are rejected as self-contradictory: `--claim-all` with
`--claim`, and `--claim-all` with `--no-claim`.

`--no-claim` with `--claim` is not contradictory — it is the idiom
above.

## Naming a role the package does not provide

A role named by `--claim` that nothing in the transaction provides is
rejected: a package cannot hold a role it is not an eligible provider
of.

The check is against every package in flight, not only the one the
operator named. So `peipkg install foo --claim bar` succeeds when a
package pulled in as a dependency of `foo` provides `bar`, and claims it
for that package.
