---
title: Impersonation Levels
order: 1
---

Impersonation allows a server thread to temporarily assume a client's identity. All access control decisions on that thread evaluate the client's token instead of the server's.

The client controls how far their identity can travel by setting an impersonation level on the connection before it is established. The server MUST NOT escalate beyond the level the client chose.

## Levels

Four levels, from least to most permissive:

**Anonymous.** The server MUST NOT identify the caller. The connection carries no identity information — both token inspection and impersonation return a token containing only the Anonymous SID (`S-1-5-7`). There is no API that bypasses the client's choice.

**Identification.** The server can identify the caller (read SIDs, query groups, inspect privileges) but MUST NOT act as them. An Identification-level token MUST NOT be used for AccessCheck against resources. If a server thread impersonates an Identification-level token and attempts to open a file, the access check fails.

**Impersonation.** The server can act as the caller for all local operations, including operations that cross local IPC boundaries. If service A impersonates client B at Impersonation level and connects to service C (also local), service C sees client B's identity. Identity cascades freely across local services. This is the default level.

**Delegation.** For local operations, identical to Impersonation. The distinction activates at the network boundary: a Delegation-level token carries authorization for the server to forward the client's identity to services on other machines via Kerberos delegation. KACS enforces the level; authd acts on it for network-level credential forwarding.

The level is set by the client via a KACS syscall on the socket before `connect()`. The default is Impersonation.
