---
title: Auto-Claim
description: Installing an eligible provider claims every unheld role it provides, and what happens when one transaction brings two providers.
---

Installing a package that is an eligible provider of one or more roles
claims, by default, every one of those roles that is currently
**unheld**. The new provider becomes the holder, and the role's claim
paths are materialised against its targets.

Auto-claim applies only to unheld roles. Installing a provider of a role
another package already holds does not change the holder: the new
provider is installed and eligible, and the incumbent keeps the role
unless the operator directs otherwise.

> [!NOTE]
> The two halves are deliberate. Auto-claiming an unheld role means a
> freshly installed sole provider just works — install the registry
> daemon and its binary appears, with no second command. Leaving held
> roles alone means installing an alternative provider never silently
> steals a live system name out from under the incumbent.

## Two providers in one transaction

When a transaction installs two eligible providers of the same unheld
role, the role goes to the one whose package name sorts lexicographically
first.

The rule exists so that the outcome is a consequence of the inputs
rather than of the order the resolver happened to place them in, which
would make an install non-deterministic.
