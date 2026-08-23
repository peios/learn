---
title: Withdrawal
description: What happens to a role when its holder is uninstalled, why nothing is promoted automatically, and how it is ordered within the uninstall.
---

When the package holding a role is uninstalled, the role's claim is
**withdrawn**: peipkg removes the role's links within the uninstall
transaction and the role becomes unheld.

peipkg does not automatically promote another eligible provider.

If other eligible providers remain installed, the withdrawal is surfaced
to the operator, naming them and the command to assign a new holder:

```
Claim 'registryd' withdrawn — packages 'altregd', 'thirdregd'
also provide it. Run 'peipkg claim registryd grant altregd'
to assign a new holder.
```

> [!NOTE]
> Withdrawal leaves the role unheld rather than auto-promoting because
> the replacement is the operator's choice: the remaining providers are
> alternatives that were deliberately not chosen while the incumbent
> held the role. Auto-promoting one would silently repoint a contended
> system name at a provider nobody selected. Surfacing the alternatives
> with a ready-to-run command makes reassignment one step without making
> it implicit.

## Revocation is not withdrawal

Revoking a role is the operator taking a grant away. Withdrawal is the
same end state reached automatically when the holder is removed — a
package withdrawing its own claim rather than an operator revoking a
grant.

A revoke does not surface the remaining providers the way a withdrawal
does, even though the resulting state is identical.

## Whether withdrawal is safe

It depends on the role's consumers. If every installed consumer reaches
the role through an optional dependency, withdrawal breaks no required
dependency and is informational.

If a required dependency is left with no holder for a name it hard-codes,
the operator is removing something the running system needs. That is the
scenario a system-critical guard would catch, and peipkg has no such
guard (§4.6).

## Ordering within an uninstall

Because claim operations ride the last staged package operation, an
uninstall of the holder deletes the target file before it deletes the
link. There is a transient window within the transaction in which the
link dangles — invisible to anything that only sees committed state, but
visible to a concurrent reader.
