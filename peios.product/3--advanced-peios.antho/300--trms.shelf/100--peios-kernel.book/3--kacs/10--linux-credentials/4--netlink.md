---
title: Netlink
description: Netlink requests are authorised through the capability switchboard — both the socket opener's token and the sender's — synchronously, in the sender's own context.
---

Netlink is the kernel's message interface: a process sends a request
to a kernel subsystem (routing, firewalling, audit, generic netlink
families) and the subsystem answers, or pushes notifications to
multicast groups. The kernel authorises those requests with capability
checks, and on Peios every one of them is a KACS privilege check.

## Where the checks run

A request to the kernel is handled synchronously: `netlink_unicast`
delivers the message to the family's receive function inside the
sending task's own `sendmsg`, under the family's mutex. There is no
later context in which a message is processed, so the sender at every
check is the current thread, and audit attribution needs no capture.
Only messages between two user sockets are queued.

The netlink permission helpers — `netlink_capable`,
`netlink_ns_capable` and `netlink_net_capable`, and through them the
generic-netlink `GENL_ADMIN_PERM` and `GENL_UNS_ADMIN_PERM` operation
flags — test two subjects and require both to pass: the credential
that **opened** the netlink socket, held on the socket's file, and the
**sender**, the current thread. `netlink_allowed`, which gates binding
to a family's multicast groups and sending to another port, tests the
current thread. This is Linux's own two-point rule, introduced after
CVE-2014-0181 so that a privileged program could not be turned into a
deputy by inheriting an unprivileged process's netlink socket as its
standard output.

## What decides

Every one of those tests reaches `security_capable()` with a specific
credential, and the capability switchboard (§3.10.2) evaluates **that
credential's token**: `pkm_kacs_capable_in_cred_ns` looks up the token
on the credential and asks whether it holds a privilege the capability
maps to. The opener's file credential carries the opener's token; the
current thread's credential carries the sender's effective token,
impersonation included. So a netlink request is authorised against two
KACS tokens, with the same privilege catalogue and the same fail-closed
behaviour as any other capability check — not against uid bits, and
not against a projection of the token.

The catalogue maps `CAP_NET_ADMIN`, `CAP_NET_RAW` and `CAP_SYS_ADMIN`
to `SeTcbPrivilege`. Configuring the network — adding a route, setting
an interface up, editing a firewall — is therefore a TCB operation on
Peios; an administrator's session cannot do it, and a `RTM_NEWLINK`
from an administrator is answered with `EPERM`. Audit control
(`CAP_AUDIT_CONTROL`, `CAP_AUDIT_READ`) maps to `SeSecurityPrivilege`
and audit writes (`CAP_AUDIT_WRITE`) to `SeAuditPrivilege`. Requests
that need no capability — dumps of the routing table or the link list
— are answered for any caller.

## What netlink carries about the sender

A netlink message's metadata (`NETLINK_CB`) records the sender's
projected UID and GID, in the same form `SO_PEERCRED` uses, and
delivers them to a receiving user socket that asked for
`SCM_CREDENTIALS` with `SO_PASSCRED`. As everywhere on Peios, those
values are a projection for compatibility and display, not an
authorisation input (§3.10.1). Netlink between two user sockets is not
a supported identity-carrying transport: it carries the projection and
nothing more, and a program that needs the peer's token uses an
`AF_UNIX` socket (§3.5).
