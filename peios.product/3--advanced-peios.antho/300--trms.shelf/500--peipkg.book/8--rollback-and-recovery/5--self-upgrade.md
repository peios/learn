---
title: Upgrading peipkg Itself
description: Upgrading the package manager is not a special case — the binary is one file among the payload, with one wrinkle.
---

Upgrading the package manager is not a special case.

The peipkg binary is one file among a transaction's payload, staged
beside itself and renamed into place like any other. The swap is a
single atomic rename, so there is no half-written binary to recover
from: recovery reconciles a transaction that crashed between its atomic
steps, not a file caught mid-write.

## The one wrinkle

After a self-upgrade, the binary running the next recovery may be a
different version from the one that started the transaction.

This is handled by versioning the journal format. Each transaction
records the schema version it was written under. A peipkg version that
can read that schema recovers the transaction directly; one that cannot
refuses with an error naming the schema version, leaving the
transaction for a version that can.

No immutable copy of the previous binary is required. If recovery needs
the prior binary, it is already present as that binary's ordinary
backup — until the transaction commits, at which point backups are
discarded (§8.2).

> [!NOTE]
> A package-manager upgrade that commits *successfully* but installs a
> defective binary is not a recovery case: there is no incomplete
> transaction. It is handled by running the prior binary — retained as
> the transaction's backup, if the transaction has not yet committed —
> to perform an ordinary downgrade. Once the transaction has committed
> and the backups are gone, the route is a downgrade using whatever
> peipkg is now installed, or an externally supplied package file.
