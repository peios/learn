---
title: Identity and Service Adapters
type: concept
description: Locate the Peios services behind familiar POSIX identity, name-resolution, and trust interfaces.
---

A familiar library interface does not imply the same configuration source as
another Linux distribution. Peios connects account lookup, hostname lookup,
and certificate trust to their owning services.

## Account lookup and authentication

The authd [NSS adapter](~peios/authentication/libc-identity) translates
POSIX account queries into the authority's identity protocol. Peios' libc
package fixes the account providers; it does not use an `/etc/passwd`
fallback or an independently configured source order. Shadow queries do not
expose credential verifiers.

UID 0 is the numeric projection of SYSTEM, not an account named `root` that
must be looked up before boot can proceed. Native authorization uses tokens
and security identifiers. A numeric name-service record is a compatibility
view rather than the complete security state.

Authentication uses [authd
conversations](~peios/authentication-client/conversations). Applications
integrate with that interface instead of configuring a PAM stack. Account
lookup and credential verification remain separate operations.

## Hostname lookup

The network name-service provider sends hostname queries to
[resolvd](~peios/network-configuration/name-resolution). Static names and resolver policy
belong to that service's configuration. Editing a separate `/etc/hosts` file
or a `files dns` provider chain does not configure Peios' fixed host lookup
path.

This does not make every libc database fixed. Consult the libc package for
databases outside the account and hostname integration before assuming the
same behavior.

## Certificate trust

[trustd](~peios/certificate-trust/overview) combines supplied certificate roots with
machine trust decisions and produces the [compatibility
files](~peios/certificate-trust/the-compat-files) consumed by TLS libraries. Those files
are generated output, even where their paths match another distribution.

Use the trust service's supported configuration for an enduring change.
Adding a certificate directly to a generated file can be undone by the next
refresh. Permission to modify trust policy is separate from permission to
read the resulting certificate bundle.
