---
title: Impersonation Levels
description: The four levels at which a server thread may assume a client's identity, and what each permits.
---

Impersonation lets a server thread temporarily assume a client's
identity, so that access control decisions on that thread evaluate the
client's token instead of the server's.

The client controls how far its identity can travel by setting an
impersonation level on the connection before it is established, and
the server cannot escalate beyond the level the client chose. There is
no API that bypasses that choice.

**Anonymous.** The server cannot identify the caller at all. The
connection carries no identity information: both token inspection and
impersonation yield a token whose user SID is Anonymous (`S-1-5-7`),
which carries Everyone as an enabled group and does not carry
Authenticated Users.

**Identification.** The server can identify the caller — read SIDs,
query groups, inspect privileges — but cannot act as them. An
Identification-level token is barred from AccessCheck against
resources: a server thread impersonating one and attempting to open a
file simply fails the check.

**Impersonation.** The server can act as the caller for all local
operations, including ones that cross local IPC boundaries. If service
A impersonates client B at this level and connects to local service C,
C sees B's identity — identity cascades freely across local services.
This is the default.

**Delegation.** Locally identical to Impersonation. The distinction
activates at the network boundary, where a Delegation-level token
carries authorization for the server to forward the client's identity
to services on other machines through Kerberos. KACS enforces the
level; authd is what acts on it.

The level is set by the client through a KACS syscall on the socket
before `connect()`, and defaults to Impersonation.
