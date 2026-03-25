---
title: Setting the Impersonation Level on a Connection
type: how-to
order: 110
---

The impersonation level is set by the **client** when establishing a connection to a service. It controls how far the service can go with the client's identity.

## Setting the level on a connection

When connecting to a service, specify the impersonation level:

```
$ pbus connect registry --impersonation-level impersonation
```

The level applies to the connection. The service receiving the connection can impersonate the client up to the specified level but no higher.

## Available levels

| Level | Flag |
|---|---|
| Anonymous | `--impersonation-level anonymous` |
| Identification | `--impersonation-level identification` |
| Impersonation | `--impersonation-level impersonation` |
| Delegation | `--impersonation-level delegation` |

## The default

If no level is specified, the default is **Impersonation** — the service can act as the client for local operations. This is appropriate for most local service connections.

## Programmatic usage

Applications set the impersonation level when creating a connection. The exact API depends on the IPC mechanism, but the principle is the same — the client specifies the level, and the kernel enforces it on the server side.

The level is recorded on the connection and cannot be changed after the connection is established. To use a different level, the client must create a new connection.

## Choosing the right level

Set the minimum level the service needs to do its job:

- Use **Anonymous** to test public accessibility without revealing your identity
- Use **Identification** when the service only needs to know who you are (logging, custom authorization)
- Use **Impersonation** when the service needs to access local resources on your behalf
- Use **Delegation** only when the service needs to forward your identity to other machines

A lower level limits the damage if the service is compromised. A service impersonating at Identification level cannot access resources as the client — even if it tries.
