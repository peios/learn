---
title: Terminology
description: The words this chapter uses for the store, its principals and groups, and the names a request may give a group.
---

**Store.** The set of local principals and local groups one store daemon
holds, with their memberships, credentials, claims and SSH keys.

**Principal.** A user or service account the store holds. It has a
**name**, unique in the store and matched without regard to case, and a
**RID** (relative identifier): the last sub-authority of its SID. A RID
is never reissued, so a deleted principal's SID never names anyone else.

**Domain SID.** The SID every principal and local group of the store is
under, `S-1-5-21-A-B-C`. A principal's SID is the domain SID followed by
its RID.

**Local group.** A group the store holds, named and numbered as a
principal is, from the same RID space.

**Well-known group.** A group whose SID is fixed by the system rather
than issued by any store: `Everyone`, `Authenticated Users`, and the
`BUILTIN` groups such as `Administrators`. The store holds none of them as
objects, but it records memberships of the `BUILTIN` groups (§2.19).

**Group name, as written.** Where a request names a group (§10.6), the
store daemon resolves it, never the client: a well-known group by its
name (`Administrators`, with or without `BUILTIN\`), a local group by its
name, or any group by its SID written out (`S-1-5-32-544`). A client
MUST pass what the person wrote, and MUST NOT resolve it itself; a client
with its own table of well-known names would be a second implementation
of the machine's identity scheme, free to disagree with the first.

**Effective Unix ID.** The POSIX identifier a principal or group projects
to: the authority's base for the store's range plus the store's relative
number (§2.20). Replies here carry the effective number, so that what an
administrator is shown is what the principal will appear as. Zero means
the store daemon cannot say.

**Credential policy.** Which credentials a principal may sign in with
(§10.8): a password, an SSH public key, either, none required, or none
accepted.
