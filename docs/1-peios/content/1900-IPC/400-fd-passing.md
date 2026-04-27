---
title: FD Passing
type: concept
description: Passing file descriptors between processes on Peios via SCM_RIGHTS — the fd-bearer-authority model and its security implications.
related:
  - peios/IPC/unix-domain-sockets
  - peios/IPC/peer-credentials
  - peios/identity/primary-vs-impersonation-tokens
---

A Unix domain socket can carry **file descriptors** as ancillary data. The kernel takes an fd from the sender's fd table, packages a reference to the same underlying kernel object, and on the receiving side allocates a fresh fd in the receiver's fd table referring to that same object.

This is **the** mechanism for cross-process fd handoff on Peios. The receiver ends up with an independent fd that grants the same access the sender had — without going through any fresh `open()` and the access checks that would entail. fd passing makes a number of architectural patterns possible: privilege separation, sandboxing, init-time fd handoff, container management, daemon-to-helper composition.

## The mechanism

The sender constructs a `msghdr` with an `SCM_RIGHTS` ancillary message containing one or more fds, then calls `sendmsg`. The receiver receives via `recvmsg`, including handling of the ancillary data, and finds the new fds in its own fd table.

A minimal illustration on the sender side:

```c
int payload_fd = open("/etc/secret", O_RDONLY);

struct msghdr msg = {0};
char ctlbuf[CMSG_SPACE(sizeof(int))];
msg.msg_control = ctlbuf;
msg.msg_controllen = sizeof(ctlbuf);

struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type = SCM_RIGHTS;
cmsg->cmsg_len = CMSG_LEN(sizeof(int));
*(int *)CMSG_DATA(cmsg) = payload_fd;

sendmsg(sock, &msg, 0);
```

On the receiving side:

```c
char ctlbuf[CMSG_SPACE(sizeof(int))];
struct msghdr msg = {0};
msg.msg_control = ctlbuf;
msg.msg_controllen = sizeof(ctlbuf);

recvmsg(sock, &msg, 0);

struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
int received_fd = *(int *)CMSG_DATA(cmsg);

/* received_fd is now an fd in our table referencing the same file
   the sender opened. We can read from it directly. */
```

Multiple fds can be sent in a single message — `SCM_RIGHTS` carries an array. Both sender and receiver hold valid references after the handoff; the sender's fd is unchanged. To "transfer" an fd in the strict sense (sender no longer holds it), the sender closes its end after the send completes.

## fd-bearer authority

The receiver's authority to use the fd is **possession**. There is no re-authentication when the fd arrives — the kernel does not check whether the receiver could have opened the underlying file directly. The receiver simply has a new fd backed by the same kernel object.

This model is intentional and load-bearing for several patterns:

**Privilege separation.** A privileged parent process opens a sensitive file (e.g. a private key), then forks an unprivileged child for protocol handling and passes the fd. The child has access to the file content via the fd despite not having the privilege required to open it directly. If the child is compromised, the attacker can use the passed fd but cannot open *other* sensitive files.

**Init-time fd handoff.** Socket-activation patterns: peinit (or another supervisor) binds a privileged port (Linux ports below 1024 historically required privilege) and passes the listening socket fd to an unprivileged service. The service handles connections without needing port-binding privilege.

**Sandbox containment.** A sandbox supervisor opens a small set of allowed resources, passes their fds to a child, then drops capabilities and seccomp-filters the child. The child can use the passed fds but cannot open new resources.

**Cross-process protocol composition.** Daemons like the X server, Wayland compositors, and PipeWire pass fds between clients to share GPU buffers, audio buffers, and other resources without each client needing its own copy.

## Security implications

The model is "if you have the fd, you have the access." This has consequences worth understanding:

**fds outlive credential changes.** If a process opens a file with broad permissions, then drops privilege (closes its primary token, or has its DACL tightened), the fd retains its original granted access. This is intentional — POSIX semantics require that an open fd remains valid even if the file is deleted or its permissions change. On Peios, the access mask granted at open time is preserved on the fd, regardless of subsequent SD changes on the underlying object.

**Passed fds bypass receiver-side access checks.** A receiver that wouldn't be able to open the file directly can still use a received fd. This is the entire point — privilege separation depends on it — but it means servers must be careful about which fds they pass to which clients. Sending the wrong fd to a client is a substantive privilege grant.

**fd revocation is hard.** Once an fd has been passed, the only way to "take it back" is for every holder to close it. There is no kernel mechanism to invalidate a specific fd from the outside. Software that needs revocable access typically uses a more elaborate protocol (e.g. periodic re-authentication) rather than relying on fd passing alone.

**fds carry no identity.** A passed fd does not record who originally opened it. The receiver cannot distinguish "this fd was opened by the sender process" from "this fd was passed through five intermediaries before it arrived." For provenance, the receiver must rely on out-of-band attestation (the connection itself, peer credentials, etc.).

## Limits and quotas

The kernel imposes limits on how many fds a single process can hold (`RLIMIT_NOFILE`) and how many can be in flight simultaneously through `SCM_RIGHTS` messages awaiting receive (controlled by per-user accounting). The Peios per-user accounting model is documented in the **Resource Control** category.

A receiver that is at its `RLIMIT_NOFILE` limit causes `recvmsg` to fail with the ancillary data dropped — the message body is delivered, but the fds are not allocated. This is a footgun for protocols that assume fd delivery is reliable; recipient software must handle the partial-delivery case.

## Cross-namespace fd passing

fd passing across network namespaces, mount namespaces, and PID namespaces works for fds that reference objects valid in both namespaces. A pipe fd is namespace-agnostic; a socket fd referring to an abstract socket may not be valid across network namespaces (the abstract namespace is per-netns). Files and devices generally pass through any namespace boundary.

The kernel does not perform namespace-translation on passed fds — the fd refers to the same kernel object on both sides, and whether that object makes sense in the receiver's namespace context is the caller's problem.

## Comparison with `pidfd_getfd`

`pidfd_getfd(pidfd, targetfd, flags)` is the **inverse** primitive: instead of the holder *sending* an fd, a third party *takes* an fd from the holder. See [Event-bearing File Descriptors](event-fds) for `pidfd_getfd` itself. The two primitives differ in who initiates and how authorisation works:

- **`SCM_RIGHTS`:** sender chooses to share. Receiver gets the fd because the sender said so. No external access check.
- **`pidfd_getfd`:** taker initiates. Authorisation is `PROCESS_DUP_HANDLE` on the target's process SD plus PIP dominance. Target may or may not even be aware.

`SCM_RIGHTS` is the cooperative pattern (sender consents); `pidfd_getfd` is the imposed pattern (taker has authority, target has no say). Most production fd-handoff is `SCM_RIGHTS`; `pidfd_getfd` is reserved for diagnostic and supervisory tooling.

## See also

- [Unix domain sockets](unix-domain-sockets) — the carrier for `SCM_RIGHTS`.
- [Peer credentials](peer-credentials) — for verifying who the sender is before trusting passed fds.
- [Event-bearing file descriptors](event-fds) — `pidfd_getfd`, the imposed inverse of `SCM_RIGHTS`.
