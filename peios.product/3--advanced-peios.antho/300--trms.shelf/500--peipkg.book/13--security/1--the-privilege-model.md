---
title: The Privilege Model
description: peipkg holds no principal and no rights of its own — it runs as the calling operator, and every file operation is checked against their token.
---

peipkg holds no principal, no identity, and no access rights of its own.

It runs **as the calling operator**. Every file operation it performs —
creating, replacing, or deleting — is checked by the kernel against the
*caller's* token and the target's security descriptor. If the caller is
authorised the operation succeeds; if not, it fails. peipkg contributes
no authority.

This is verifiable in the shape of the program. There is no daemon, no
broker, and no socket. Nothing in it changes identity: no user or group
is assumed or dropped, no capability is manipulated, no ownership is
changed on any file it writes. No privilege is requested anywhere. The
only privilege its operation touches is the one audit emission consumes
passively (§13.3).

## What follows

The authority to install a package is exactly the authority to write the
directories the package installs into — an ordinary matter of security
descriptors on the permitted destinations. A deployment grants
installation authority by granting those write rights to whichever
principals it intends to be able to install software.

A package's declared security descriptor overrides can only assign
descriptors the calling operator already has the authority to assign.
Where applying a given descriptor requires a particular right —
`WRITE_DAC` for a discretionary access list, `WRITE_OWNER` and
`SeRestorePrivilege` for an owner assignment — that right is held by the
*operator*, not by peipkg. A package cannot, through
peipkg, obtain authority the operator running it does not hold.

That consequence is currently theoretical rather than load-bearing,
because overrides are parsed and then never applied (§5.4).

> [!NOTE]
> An earlier design ran the package manager as a dedicated service
> principal holding broad system rights — a posture comparable to a root
> process. Peios instead makes it an ordinary unprivileged program:
> there is no standing principal to compromise, no privilege to confine,
> and the blast radius of a malicious package is bounded by the
> authority of whoever ran it.
>
> The cost is that scoped, curated installation — letting a
> low-authority operator install one approved package without granting
> general write access — is not something peipkg can provide. That is
> the job of the higher-level roles and features layer, which can act as
> a privileged broker.
