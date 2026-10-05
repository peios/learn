---
title: Startup Sequence
description: What resolvd does between exec and READY=1, in order, which steps are fatal, and the only ways the process exits.
---

## The sequence

1. **The native socket.** The runtime directory and the socket are
   created and given their modes and descriptors (§2.4). A failure to
   create the directory, set a mode, remove a stale socket file, or bind
   is fatal: resolvd logs `native socket: <error>` at error level and
   exits with status 1. [*startup.native-socket-failure-is-fatal] A failure to write a descriptor is not
   fatal (§2.4).
2. **The stub listener.** A UDP socket and then a TCP listener are bound
   to `127.0.0.53:53`. A failure of either is fatal: resolvd logs
   `stub listener on 127.0.0.53:53: <error>` and exits with status 1. [*startup.stub-listener-failure-is-fatal]
3. **The registry.** `Machine\System\Network\Dns` is read whole (§2.3).
   A missing or unreadable key is not an error; every value takes its
   default. [*startup.missing-dns-key-is-not-an-error]
4. **The registry watch.** A subtree watch is armed on
   `Machine\System\Network` (§2.3). If it cannot be armed, resolvd logs
   `registry watch unavailable (<error>); configuration is read once`
   and runs on the configuration it read in step 3 until it restarts. [*startup.watch-failure-reads-configuration-once]
5. **The engine.** The engine's random generator is seeded from eight
   bytes of `/dev/urandom`, or from the wall clock in nanoseconds when
   `/dev/urandom` cannot be read. [*startup.generator-seeded-from-urandom] The engine is given the kernel's
   hostname, the fallback servers and search domains, and the static
   names. A kernel hostname that is empty or `(none)` counts as no
   hostname. [*startup.kernel-hostname-none-is-no-hostname]
6. **The control object** is built from `ControlSecurity` (§5.2).
7. **netd.** The first attempt to subscribe is made immediately (§3.1).
   Its failure is not fatal and is retried with backoff (§3.2). [*startup.first-netd-attempt-immediate-and-not-fatal]
8. resolvd logs
   `listening on /run/resolvd/resolv.sock and 127.0.0.53:53`, [*startup.listening-log-line]
9. sends `READY=1` (§2.1),
10. and enters the loop (§2.5).

Both doors are open before readiness is reported, and neither waits for
netd: a client that connects the moment resolvd is ready gets synthetic
and static answers at once, and `unavailable` for anything that needs a
server until either a snapshot arrives or fallback servers are
configured. [*startup.answers-before-first-snapshot]

## Exiting

resolvd has no shutdown path of its own. It installs no signal handlers,
so it ends when peinit signals it, with the default disposition, and
leaves `/run/resolvd/resolv.sock` behind; the next start removes the
stale socket file before binding (§2.4). [*startup.no-signal-handlers-socket-left-behind]

Apart from the startup failures above, the process exits on its own
only when `poll` fails with anything other than `EINTR`. It logs
`poll: <error>` at error level and exits with status 1. [*startup.poll-failure-exits] Nothing a client
or an upstream server sends causes an exit. [*startup.no-input-causes-exit]
