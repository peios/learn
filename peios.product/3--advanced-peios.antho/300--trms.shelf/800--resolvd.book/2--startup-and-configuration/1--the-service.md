---
title: The Service
description: How peinit runs resolvd — the service definition, the identity it runs under, the port reservation that lets it bind port 53, readiness, restart, and where its log lines go.
---

## The service definition

resolvd is started by peinit from `Machine\System\Services\resolvd`. The
package ships the definition as a registry seed,
`/usr/share/regim/resolvd-service.reg`, which is inert until an image
names it in its `[registry] autoapply` list. [*service.definition-seed-inert-until-applied]

| Value | Type | Data | Effect |
|---|---|---|---|
| `ImagePath` | `REG_SZ` | `/usr/sbin/resolvd` | The binary. resolvd reads no command-line arguments. [*service.image-path-no-arguments] |
| `Triggers` | `REG_MULTI_SZ` | `boot` | Started at boot. [*service.triggered-at-boot] |
| `Identity` | `REG_SZ` | `Service` | Runs under its own virtual service account. [*service.identity-is-own-virtual-account] |
| `Readiness` | `REG_DWORD` | `0` | Notify: ready when resolvd says so. [*service.readiness-is-notify] |
| `RuntimeDirectories` | `REG_MULTI_SZ` | `resolvd` | peinit creates `/run/resolvd`. [*service.runtime-directory] |
| `RestartPolicy` | `REG_DWORD` | `2` | Always restarted. [*service.restart-policy-always] |
| `ErrorControl` | `REG_DWORD` | `0` | |
| `DisplayName` | `REG_SZ` | `Stub resolver` | |
| `Description` | `REG_SZ` | (one sentence) | |

## Identity and privilege

resolvd holds no privilege and needs none. Its one claim on the machine
that an ordinary process could not make — binding UDP and TCP port 53 —
is met by a port reservation rather than a capability (PSPU §6.8).

The reservation is a second seed, `/usr/share/regim/resolvd-port.reg`,
also inert until an image applies it. It writes one value: [*service.port-reservation-seed]

| Key | Value | Type |
|---|---|---|
| `Machine\System\Network\TcpIp\PortReservations` | `tcp,udp:53` | `REG_BINARY` |

The data is a security descriptor granting the reservation to SYSTEM and
to resolvd's service SID,
`S-1-5-80-3864064249-1823296737-2008945602-1354971773-2894779966`, so it
follows the service rather than whichever account the service happens to
run as. [*service.reservation-granted-to-system-and-service-sid] The selector `tcp,udp:53` is more specific than the kernel
package's `tcp,udp:1-1023` and so decides port 53 alone. The descriptor
bytes are generated from the SID by a tool in the source tree, not
written by hand.

Without the reservation applied, the stub listener cannot bind and
resolvd exits at startup (§2.2, §9.3).

## Readiness

With `Readiness` 0 peinit waits for a notification. resolvd sends the
datagram `READY=1` to the socket named by the `NOTIFY_SOCKET`
environment variable once the native socket and both stub sockets are
open and the registry has been read. [*service.ready-after-doors-open] It does not wait for netd. [*service.ready-does-not-wait-for-netd] When
`NOTIFY_SOCKET` is unset nothing is sent; a failure to send is logged as
`readiness notify: <error>` and startup continues. [*service.notify-failure-not-fatal]

## Restart

`RestartPolicy` 2 restarts resolvd whenever it exits. Everything resolvd
holds is in memory — the cache, the demoted servers, the counters, the
scopes — and a restart loses all of it. [*service.restart-loses-all-state] The scopes come back with the
first snapshot after netd is reached again; the rest starts empty.

## Log lines

Every line resolvd logs is written to standard error as

```text
resolvd: <level>: <text>
```

where the level is `info`, `warn` or `error`. [*service.log-line-format] peinit forwards a
service's standard error to eventd, which is where the lines are read:

```sh
evctl 'LOGS FROM resolvd SINCE 1h ago TAKE 40'
```

Each line is also offered to `/dev/kmsg` at kernel priority 6, 4 or 3
for info, warn and error. `/dev/kmsg` is writable by SYSTEM only, so for
resolvd the mirror fails to open, and the first log line is preceded by
one line on standard error saying so: [*service.kmsg-mirror-fails-once]

```text
resolvd: warn: /dev/kmsg mirror unavailable (<error>): log lines go to stderr only
```

resolvd's lines therefore never reach the console or `dmesg`.
