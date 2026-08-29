---
title: Identity
description: Two identities per submission — the submitter's, captured from the kernel, and the job's, which is either the submitter's own primary or a token the kernel verified it could convey. Never a name.
---

Every submission involves two identities, and the protocol keeps them
apart.

The **submitter** is who asked. The **job identity** is who the job
runs as. They are the same principal in the simplest case and
different ones in the case the channel exists for — a broker running a
program as the client it is serving.

## The submitter

The manager MUST establish the submitter's identity from the kernel,
as §4.6 requires of the control channel: the peer's token, captured
when the connection was accepted, used for every message on the
connection. A submitter MUST NOT be able to assert who it is, and a
change of identity mid-connection has no effect on it.

The submitter's identity is what the manager records on the job as
its submitter, what it counts quotas against, and what it names as the
owner of the job's descriptor (§7.8). It MUST be the identity the peer
thread was acting under when it connected — so a submitter that
connects while impersonating is recorded as the principal it was
impersonating. A submitter that intends to *own* the jobs it submits,
as itself, connects as itself and conveys any other identity per
message.

## The job identity

The job identity is established in exactly one of two ways, and the
manager MUST NOT provide a third.

**No token attached — the submitter's own primary.** The manager MUST
open the primary token of the connecting *process* — identified by
the kernel through the peer's process handle (`SO_PEERPIDFD`), never
by a PID the submitter names — duplicate it, and install the duplicate
on the job.

The job then has the identity a child of the submitter would have
had: its primary token, with no impersonation inherited (the Peios
Kernel TRM §3.2). A submitter that was impersonating when it
connected therefore produces a job running as its *own* identity, not
the impersonated one, while being recorded as a submitter under the
impersonated one. The two differ deliberately, and a submitter that
wants the impersonated identity on the job attaches it.

**A token attached — the identity conveyed with the message.** The
manager MUST use the token the kernel delivered with the `submit`
message, duplicate it to a primary token, and install the duplicate on
the job.

The kernel gated the attach: it ran the impersonation gates with the
submitter as installer and recorded on the token the lower of the
socket's level and the source's own (the Peios Kernel TRM §3.5). The
attached token is therefore a kernel-verified statement that *the
submitter could have acted as this identity, at this level, when it
sent this message*. The manager MUST rely on that statement and MUST
NOT re-derive it.

## What the manager checks

The manager MUST refuse, with `BAD_TOKEN`:

- more than one attached token on a message;
- an attached token whose impersonation level is below Impersonation.
  An Identification-level token cannot pass an access check and an
  Anonymous one is not an identity to run a process as; neither can
  become a primary (the Peios Kernel TRM §3.2.4);
- an attached token the manager cannot duplicate.

The manager MUST NOT refuse a token because of *who* it names. Whether
the submitter may run a job as that identity was decided by the kernel
when the token was conveyed, and a second decision inside the manager
would be a second copy of the same policy, able only to disagree with
the first.

## The level carries through

The duplicated primary carries the attached token's impersonation
level, and everything the job does inherits it (the Peios Kernel TRM
§3.5.1). A submitter that needs the job to convey Delegation — to a
session that will authenticate to remote services on its user's
behalf — MUST set its own jobs connection to Delegation before
attaching, because the default level on a socket is Impersonation and
the attach is clamped to it. A job started at Impersonation cannot be
raised afterwards, by anyone.

## What the manager never does

The manager MUST NOT accept a *primary* token passed as a plain
descriptor (`SCM_RIGHTS`) as a job identity. A descriptor passed that
way is not gated by the kernel: whoever holds an fd can pass it, and
the recipient learns nothing about whether the sender could act as the
identity it names. Every job identity on this channel is one the
kernel verified the submitter could act as, and a path that skips the
verification would be the only one worth attacking.

The manager MUST NOT install on a job any token it obtained by a route
other than the two above. In particular it MUST NOT open a token
through a submitter-supplied PID or descriptor, and MUST NOT let a
`submit` field name an identity. There is no identity field, and a
manager MUST NOT add one (§7.11).

> [!NOTE]
> The consequence for a service that runs programs as its clients is
> that it needs `SeImpersonatePrivilege` — to be allowed to convey a
> client's identity at all — and nothing more. It never holds a
> primary token for the client, never needs
> `SeAssignPrimaryTokenPrivilege`, and never installs anything. The
> one process that installs primary tokens on other people's behalf is
> the one that supervises the result.
