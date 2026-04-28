---
title: Seccomp on Peios
type: concept
description: Voluntary syscall filtering — how seccomp works, how it complements KACS, the Peios-specific PR_SET_NO_NEW_PRIVS semantics, and audit knobs for filter operations.
related:
  - peios/signals/signals-on-peios
  - peios/process-security/process-security-descriptors
  - peios/identity/impersonation
---

**Seccomp** (secure computing mode) is a kernel mechanism that lets a process voluntarily restrict its own syscall surface. After installing a seccomp filter, the process can no longer make syscalls the filter denies — and crucially, the restriction survives `exec()` and `fork()`, so a launcher can sandbox a child process before handing it control.

Seccomp solves a different problem than KACS. KACS authorises *who* is calling — does this principal have the right to do this operation? Seccomp constrains *what code* may legitimately call — does this code path have any business making this syscall? The two are complementary. A renderer process is fully authorised to call `openat()` (it runs as a normal user); but a renderer that has finished loading the page should never need to open files again, so its sandbox seccomp filter denies further `openat()` calls. Even if a JavaScript engine bug compromises the renderer, the attacker cannot escape into the filesystem — the syscall is gone, regardless of authorisation.

This page covers the seccomp mechanism, how it sits alongside KACS, the Peios-specific behaviour for `PR_SET_NO_NEW_PRIVS`, and audit configuration. It also sketches the **seccomp-bridge** pattern that lets unmodified Linux applications gain Peios identity semantics through a userspace mediator — a foundational compatibility primitive.

## The mechanism

There are two seccomp modes:

- **Strict mode** (`SECCOMP_SET_MODE_STRICT`): legacy. After enabling, the process can call only `read`, `write`, `_exit`, and `sigreturn`. Anything else terminates the process with SIGKILL. Almost never used in modern code.
- **Filter mode** (`SECCOMP_SET_MODE_FILTER`): the modern path. The process loads a small BPF program — the **filter** — that runs on every syscall entry. The filter inspects the syscall number and arguments and returns a **verdict** that determines what happens.

Filter verdicts:

| Verdict | Effect |
|---|---|
| `SECCOMP_RET_ALLOW` | Pass through. The syscall executes normally. |
| `SECCOMP_RET_ERRNO` | Stop. Return a chosen errno without executing the syscall. |
| `SECCOMP_RET_KILL_THREAD` | Stop. Kill the calling thread with SIGSYS. |
| `SECCOMP_RET_KILL_PROCESS` | Stop. Kill the entire process with SIGSYS. |
| `SECCOMP_RET_TRAP` | Stop. Deliver SIGSYS to the process — the handler can inspect what was blocked and recover. |
| `SECCOMP_RET_LOG` | Pass through, but log via the kernel audit subsystem. |
| `SECCOMP_RET_USER_NOTIF` | Suspend the calling process and notify a userspace handler over a notification fd. The handler decides what return value the suspended syscall should report. |
| `SECCOMP_RET_TRACE` | Hand control to a ptrace tracer. |

The filter cannot modify syscall arguments or rewrite paths. It is purely a gate. Argument-rewriting would require dereferencing user pointers from inside the filter, which has historically been a rich source of TOCTOU (time-of-check vs time-of-use) bugs. Behaviour-modification, when needed, happens through `SECCOMP_RET_USER_NOTIF` — a userspace handler can synthesise a return value or perform an equivalent operation in its own context.

## Properties that matter

Three properties make seccomp useful as a sandboxing primitive:

1. **Self-restriction only.** A process applies seccomp to itself. There is no syscall to apply seccomp to another process. This is fundamentally different from KACS authorisation, and it's why seccomp doesn't need a privilege gate — restricting yourself can never harm anyone else.

2. **Tighten-only.** Once a filter is installed, the process can install additional, more-restrictive filters but cannot remove or weaken the existing one. Filter sets compose: every filter must allow a syscall for it to pass through. This makes the restriction permanent and auditable.

3. **Inheritable.** Filters survive `fork` and `exec`. A privileged launcher can install a filter and then `exec` an untrusted binary, which then runs with the filter in force and has no way to clear it. This is the foundation of every browser-renderer sandbox.

## How seccomp and KACS interact

Seccomp runs at syscall entry, **before** any LSM hook fires. So if a seccomp filter denies a syscall, KACS never sees it — there's no opportunity for KACS to decide differently. This is the intended layering:

- Seccomp runs first. Denial here is final.
- LSM hooks (including KACS's hooks) run next, and only on syscalls seccomp allowed.
- The actual kernel work runs last.

The pre-LSM ordering means seccomp can only deny — it can never allow past KACS. A seccomp filter that returns `SECCOMP_RET_ALLOW` for every syscall is observationally identical to having no filter at all; KACS still gets to make its own decisions.

This pre-LSM positioning is also why seccomp is fast. The filter is a small BPF program executed without much kernel context, and a denial avoids the full syscall entry path that would otherwise run.

## Privilege gating: there isn't any

Anyone can install a seccomp filter on themselves. No privilege required. This is how unprivileged sandboxes work — Chrome's renderer is itself unprivileged but installs a filter to drop most of its syscalls. Adding a privilege gate would break every existing sandbox and provide no security benefit (the worst a process can do is restrict itself).

The verdict `SECCOMP_RET_USER_NOTIF` does require an extra step: receiving the notification fd. The fd is returned to the process that installed the filter; that process can then send the fd to a privileged supervisor over a Unix socket. The supervisor handles the notifications and decides what to do — see the [seccomp-bridge pattern](#the-seccomp-bridge-pattern) below.

## PR_SET_NO_NEW_PRIVS — the Peios twist

`PR_SET_NO_NEW_PRIVS` (NNP) is a process flag that, when set, prevents the process and its descendants from acquiring any new privileges across `exec()`. On Linux, this primarily means setuid/setgid bits and file capabilities are ignored — a process with NNP set that execs a setuid-root binary does not gain root.

NNP is required before installing a seccomp filter under Linux's modern semantics, because the combination of "drop syscalls then exec setuid binary" used to produce strange interactions. Requiring NNP first makes the flow clean: if you're sandboxing yourself, you also forfeit the ability to elevate.

On Peios, setuid bits don't grant elevation in the Linux sense — privilege flows through KACS tokens, not through file mode bits. So Linux's NNP semantics (block setuid escalation) are mostly inert here. Peios extends NNP to give it a meaningful guarantee on the token model:

> **NNP on Peios additionally blocks `kacs_assume_token` for the calling process and all its descendants. Once NNP is set, no thread in this process tree can ever acquire an alternate token, even if authd would have authorised the operation.**

This makes NNP a hard floor on identity. A sandboxed process with NNP set cannot escape its current token state, regardless of bugs or compromise. Combined with seccomp, this gives a launcher a powerful pattern:

```c
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
// install seccomp filter that intercepts identity-related syscalls
seccomp(SECCOMP_SET_MODE_FILTER, 0, &fprog);
execve("/path/to/sandboxed/binary", argv, envp);
```

After this point the sandboxed binary:

- Cannot acquire a new token (NNP-extended semantics).
- Cannot make syscalls the filter denies (seccomp).
- Cannot remove the seccomp filter or the NNP flag (both are tighten-only).

Existing Linux software that calls `prctl(PR_SET_NO_NEW_PRIVS, 1)` before installing seccomp gets the stronger guarantee for free, without any code changes.

## The seccomp-bridge pattern

Beyond simple syscall denial, `SECCOMP_RET_USER_NOTIF` enables a powerful compatibility primitive: an unmodified Linux application can run on Peios with full Peios identity semantics, with a userspace daemon translating Linux-shaped operations into Peios-shaped ones.

The mechanism, in outline:

1. A Peios launcher prepares a Linux process. Before `exec`, it sets `PR_SET_NO_NEW_PRIVS` (Peios-flavour: also blocks `kacs_assume_token`) and installs a seccomp filter that returns `SECCOMP_RET_USER_NOTIF` on identity-related syscalls (`setuid`, `setresuid`, `setgid`, `setresgid`, `setgroups`, `capset`) and on any Linux-specific syscalls without a direct Peios equivalent. The filter sends the notification fd to a privileged daemon (`compatd`) before `exec`.

2. The Linux binary runs and eventually calls a Linux-shaped operation, e.g. `setuid(1000)`.

3. The kernel suspends the calling thread and posts a notification to `compatd`'s fd.

4. `compatd` examines the request, resolves the Linux UID to a Peios token via the credential projection, decides whether to authorise the operation by Linux-style policy, applies the resulting token change to the suspended process, and returns a synthetic result code.

5. The kernel resumes the thread with the synthetic result. From the Linux binary's perspective, `setuid()` returned 0 — it has no awareness that anything Peios-specific happened.

This pattern lets the *decision* about what a Linux-shaped operation means on Peios live in one place (compatd), keeps the Linux binary unmodified, and gives the result of every such operation real KACS state. Because NNP-extended blocks the binary from calling `kacs_assume_token` directly, compatd is the only path to identity changes — the bridge is sealed.

The pattern works well for identity syscalls and other rare administrative operations. It is not suitable for hot-path syscalls like `read`/`write`/`futex` — the user-notif round-trip would dominate latency. The full seccomp-bridge architecture, including the missing `kacs_apply_token_to_process` primitive that makes step 4 possible, is a separate design topic; see (TODO: link to compatd architecture page when it lands).

## Audit knobs

Seccomp filter operations can be audited at three different surfaces, each with very different volume and value characteristics. Peios exposes a registry knob for each so operators can tune to deployment context.

| Registry path | Default | What it audits |
|---|---|---|
| `\System\Audit\Seccomp\InstallEvents` | enabled | Filter installation events: which process installed which filter (filter hash, length, attached pids). Low volume — once per process startup. High diagnostic value: answers "is this process actually sandboxed and with what?" |
| `\System\Audit\Seccomp\DenialEvents` | disabled | Filter denial events: a `RET_KILL`/`RET_TRAP`/`RET_ERRNO` fired. Variable volume — can be very high under attack or buggy software. High diagnostic value during incident response; noisy in steady state. |
| `\System\Audit\Seccomp\NotifyEvents` | disabled | `RET_USER_NOTIF` firings. Mostly compat-shim traffic; high volume on bridged Linux apps. Useful for compatd debugging, not for security audit. |

The defaults reflect typical operator preference: low-volume install events on by default (the diagnostic value is high enough to be worth always paying for); the noisy denial and notify channels off by default but available when needed (forensic environments, fortress images, debugging compat shims).

`RET_ALLOW` events are not audited separately — when a syscall passes seccomp, it proceeds to whatever LSM and audit subsystems would otherwise observe it, and gets logged through those normal channels. Auditing the seccomp-allow event would just duplicate the record.

The registry-key access controls on the audit knobs are themselves the security boundary: writing these keys requires operator authority. Per Peios's general registry model, "what if an attacker flips the audit knob" is not an additional attack surface — anyone who can write the knob already has authority equivalent to disabling the audit subsystem entirely.

## Verdict-by-verdict notes

### RET_ALLOW

The default outcome. Syscall executes; LSM hooks (including KACS) still apply.

### RET_ERRNO

The most common denial verdict. The filter chooses an errno value, the kernel returns it without executing the syscall, and the calling code sees a normal-shaped failure. Sandbox writers prefer `EPERM` (permission denied) for "this would work but we forbid it" and `ENOSYS` (function not implemented) for "as far as you should know, this kernel doesn't support that."

### RET_KILL_THREAD, RET_KILL_PROCESS

Hard kill with SIGSYS. `RET_KILL_PROCESS` is preferred for sandboxes — killing a single thread in a multi-threaded program leaves the process in a partially-functional state that can mask security failures. `RET_KILL_THREAD` exists mainly for compatibility with older sandboxes.

### RET_TRAP

Deliver SIGSYS but allow the handler to recover. The handler reads `si_call_addr`, `si_syscall`, and `si_arch` from siginfo to identify the offending call. Used by sandboxes that want to trap suspicious syscalls without immediately dying — for example, a debugger-style sandbox that logs and continues, or a JIT runtime that catches and emulates certain syscalls.

### RET_LOG

Allow but log. The syscall executes normally and a record goes to the kernel audit log. Useful for "what is this code actually doing?" investigation without changing behaviour.

### RET_USER_NOTIF

The behavior-modification verdict, foundational to the seccomp-bridge pattern. The kernel suspends the calling thread, posts a notification on the notification fd, and waits for the userspace handler to send a verdict back. The handler can:

- Approve the call, optionally substituting a synthetic return value.
- Deny the call with a chosen errno.
- Continue without intervening, letting the syscall proceed normally.

Container runtimes use this to virtualise specific syscalls inside an unprivileged container. compatd uses it for the bridge pattern. Any process can install a `RET_USER_NOTIF` filter on itself, but the notification fd has to be passed to a privileged supervisor for the pattern to be useful.

### RET_TRACE

Hands control to an attached ptrace tracer. Largely supplanted by `RET_USER_NOTIF`, which doesn't require a ptrace attach.

## SIGSYS

When seccomp delivers SIGSYS via `RET_KILL_*` or `RET_TRAP`, the siginfo carries seccomp-specific fields:

- `si_code` is `SYS_SECCOMP`.
- `si_call_addr` is the program counter at the offending instruction.
- `si_syscall` is the syscall number that was denied.
- `si_arch` identifies the architecture (`AUDIT_ARCH_X86_64` etc.).

Handlers can use these to decide whether to recover or terminate. See [Signal Information](../signals/siginfo) for the full siginfo discussion.

## Mandatory profiles?

A natural question: should certain Peios trust tiers come with mandatory seccomp profiles applied by the launcher? For example, "all Protected-tier services automatically have a baseline seccomp profile applied at exec by `peinit`."

This is deliberately *not* baked in. Service definitions can opt into seccomp profiles per-service, and that's where the choice belongs — operators want per-workload control, and bundling it into the launcher would be an unhelpful one-size-fits-all decision. The pattern that already works (service definitions specifying syscall filters) does the right thing.

## See also

- [Signals on Peios](../signals/signals-on-peios) — the security model for signal sending, including SIGSYS.
- [Signal information](../signals/siginfo) — the seccomp-specific siginfo fields.
- [Process security descriptors](../process-security/process-security-descriptors) — KACS's process-level access masks, which seccomp complements.
- [Impersonation](../impersonation/understanding-impersonation) — the `kacs_assume_token` operation that NNP-extended blocks.
