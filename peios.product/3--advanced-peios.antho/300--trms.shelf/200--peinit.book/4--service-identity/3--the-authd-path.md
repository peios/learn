---
title: The authd Path
description: Every non-SYSTEM token comes from authd — peinit resolves no identities itself, and the interface belongs to authd.
---

For any identity other than `SYSTEM`, the token comes from authd. peinit
does not resolve identities, does not know whether a principal is local
or from a domain, and does not want to: routing is authd's whole
purpose.

What peinit requires of authd is:

1. peinit sends the `Identity` value verbatim.
2. authd routes it to an identity source — a built-in for the
   well-known principals, lpsd for local accounts, a connector for
   domain accounts.
3. The source returns the principal's user SID and group SIDs.
4. authd mints a KACS token, creates a logon session, adds the
   per-service SID to the group list, and returns the token descriptor
   to peinit.

Every non-SYSTEM service start depends on this, and every one of them
fails if authd is unavailable when the token is needed. Platform
services are unaffected, because they never take this route.

## The interface is authd's

The steps above describe what peinit needs, not how it asks. authd owns
the request and response schema, the socket path, and the descriptor
passing mechanism. No authd specification exists yet — authd's design
was deliberately deferred until KACS and the registry had settled — so
this path is not implementable from this manual alone.

## The current implementation

peinit's authd client is a placeholder. It ignores the requested
identity and returns a freshly minted SYSTEM token, taking the §4.2 path
for every service.

The consequence is that every service currently runs with user SID
`S-1-5-18` and peinit's full privilege set, whatever its definition
says. `RequiredPrivileges` still applies, and is currently the only
thing that reduces what a service can do. A service that does not set it
runs fully privileged.

Two things follow that are worth stating plainly, because both are
easy to reason wrongly about:

- **Status output reports the declared identity, not the effective
  one.** The job's resolved identity string is what appears in a status
  query and in a `job.created` event, and it says `LocalService` for a
  service running on a SYSTEM token.
- **The per-service SID is still correct.** peinit computes it from the
  service name and adds it to the minted token (§4.4), so per-service
  ACLs behave as designed even while the user SID does not.

The placeholder also interacts with socket protection in a way worth
knowing about. peinit's sockets are reachable only by SYSTEM (§13.3),
so a service on a correctly resolved non-SYSTEM token could not reach
the notification socket to report readiness. Today every service holds
a SYSTEM token, so the question does not arise — which means the two
have to be resolved together rather than one at a time.
