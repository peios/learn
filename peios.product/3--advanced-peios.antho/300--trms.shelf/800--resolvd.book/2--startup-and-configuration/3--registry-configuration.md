---
title: Registry Configuration
description: The values resolvd reads from Machine\System\Network\Dns, how each is parsed and what a malformed one does, and how a change reaches the running daemon.
---

The registry holds resolvd's fallbacks and its static names, under
`Machine\System\Network\Dns`; which keys a resolver reads is fixed by
PSPU §6.9. Nothing about the live network is read from the registry;
that arrives from netd (§3).

## The values

The key is opened for query and enumerate-subkey access. When it does
not exist or cannot be opened, every value below takes its default. [*config.absent-key-gives-defaults]

| Value | Type read | Default | Used for |
|---|---|---|---|
| `FallbackServers` | `REG_MULTI_SZ`, or one `REG_SZ` / `REG_EXPAND_SZ` | none | The fallback scope's servers (§4.4) |
| `ExtraSearchDomains` | `REG_MULTI_SZ`, or one `REG_SZ` / `REG_EXPAND_SZ` | none | Search domains after every interface's (§4.3) |
| `ControlSecurity` | `REG_BINARY` | the compiled default | The control object (§5.2) |
| `Hosts\` | a subkey | empty | Static names (§4.2) |

Strings are read as UTF-8 up to the first NUL. A `REG_EXPAND_SZ` is read
as it is stored; nothing in it is expanded. [*config.expand-sz-not-expanded] A value of any other type is
treated as absent. [*config.other-value-types-treated-as-absent]

### `FallbackServers`

Each string is trimmed of surrounding whitespace and parsed as an IPv4
or IPv6 address. Empty strings in a multi-string are skipped. A string
that is not an address is skipped and logged: [*config.fallback-malformed-address-skipped-and-logged]

```text
Dns FallbackServers: ignoring malformed address "<string>"
```

There is no way to give a port; every server is asked on port 53. [*config.fallback-servers-port-53] The
order of the list is the order servers are tried in (§4.6).

### `ExtraSearchDomains`

Each string is parsed as a domain name, with or without a trailing dot.
A string that does not parse, or that is the root, is skipped and
logged as `Dns ExtraSearchDomains: ignoring malformed domain "<string>"`. [*config.extra-search-domain-malformed-skipped-and-logged]

### `ControlSecurity`

A `REG_BINARY` value with at least one byte is taken as a self-relative
security descriptor. An empty value, a value of another type, or an
absent value selects the compiled default. [*config.control-security-empty-or-wrong-type-selects-default] Bytes that do not form a
valid descriptor also select the compiled default, and resolvd logs
`ControlSecurity is not a valid descriptor (<error>); using the default`. [*config.control-security-invalid-selects-default-and-logs]

### `Hosts\`

Every value under `Machine\System\Network\Dns\Hosts` is one static name.
The value's name is the host name and its data is one address
(`REG_SZ` or `REG_EXPAND_SZ`) or several (`REG_MULTI_SZ`): [*config.hosts-value-is-one-static-name]

- a value name that is not UTF-8 is skipped silently; [*config.hosts-non-utf8-name-skipped]
- a value name that does not parse as a domain name is skipped and
  logged as `Dns Hosts: ignoring malformed name "<name>"`; one that
  parses to the root is skipped silently; [*config.hosts-malformed-name-skipped-and-logged]
- each address is parsed as for `FallbackServers`, and a malformed one
  is skipped and logged as `Dns Hosts: ignoring malformed address
  "<string>"`; [*config.hosts-malformed-address-skipped-and-logged]
- a name left with no valid address, including one whose value has any
  other type, is not a static name at all. [*config.hosts-name-without-address-dropped]

Names match case-insensitively, so `Printer` and `printer` are the same
static name. [*config.hosts-names-case-insensitive] Where the same address is listed under several names, the
reverse lookup of that address returns one of them (§4.2).

## Changes at run time

resolvd watches `Machine\System\Network`, recursively and for every kind
of change, rather than the `Dns` key itself: the `Dns` key need not
exist at boot, and a watch on a missing key cannot see it appear. [*config.watches-network-key-recursively] Every
batch of watch events, from anywhere under `Machine\System\Network`,
causes the whole `Dns` key to be read again, as at startup. [*config.any-event-rereads-dns-key] netd's own
writes under that key cause such re-reads too.

The fresh configuration is compared with the one in use. When nothing
differs nothing happens. [*config.unchanged-configuration-is-a-no-op] When anything differs, resolvd:

1. rebuilds the control object from `ControlSecurity`; [*config.change-rebuilds-control-object]
2. replaces the fallback servers and search domains, discarding every
   answer cached through the fallback scope if the server list differs
   in content or in order; [*config.fallback-server-change-flushes-fallback-cache]
3. replaces the static names; [*config.change-replaces-static-names]
4. logs `configuration changed`. [*config.change-logged]

Every change applies to the next question or request; nothing needs a
restart. [*config.changes-apply-live] Static names are never cached, so a new or removed `Hosts\`
value is visible at once. [*config.static-name-change-visible-at-once] Answers already cached through an interface
scope are not discarded by a registry change. [*config.registry-change-keeps-interface-cache]

If reading watch events fails, resolvd logs
`registry watch: <error>; re-arming` and arms a new watch. [*config.watch-error-re-arms] If that also
fails, watching stops without a further message and the configuration
in use stays as it is until resolvd restarts. [*config.failed-re-arm-stops-watching-silently]
