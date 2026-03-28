---
title: Process Mitigations
type: concept
order: 20
description: The four immutable process mitigations -- WXP, LSV, TLP, and CFI -- that harden processes against exploitation.
---

**Process mitigations** are security hardening flags that restrict what a process can do at the memory and code-loading level. They are set when the binary is executed — determined by the binary's metadata and signing properties — and **cannot be changed at runtime**.

Mitigations target exploitation. Even if an attacker finds a vulnerability in a service, mitigations make it dramatically harder to turn that vulnerability into code execution.

## The four mitigations

### WXP — Write-XOR-Execute Protection

Memory pages cannot be simultaneously writable and executable. A page can be writable (for data) or executable (for code), but never both at the same time.

This blocks **shellcode injection** — the classic technique of writing attacker-controlled code to a writable memory region and then executing it. With WXP, there is no memory region that is both writable and executable.

WXP is safe for all server workloads that do not use JIT compilation. Processes that need to generate code at runtime (JIT compilers, some language runtimes) cannot use WXP.

### LSV — Library Signature Verification

Only **cryptographically signed** shared libraries can be loaded. Any attempt to load an unsigned library into the process is rejected.

This prevents an attacker from loading a malicious library into a protected process. Even if the attacker can write a file to disk, the file cannot be loaded as code unless it carries a valid signature.

LSV requires the same signing infrastructure as PIP. It is used for TCB processes where all loaded code must be verified.

### TLP — Trusted Library Paths

Shared libraries can only be loaded from **approved directories** (for example, `/usr/lib`). An attempt to load a library from any other path is rejected.

TLP is weaker than LSV — it trusts the path, not the binary itself. But it is applicable to processes that load third-party unsigned libraries from known locations. An attacker who can write to `/tmp` but not to `/usr/lib` cannot inject a library.

### CFI — Control Flow Integrity

Hardware control-flow enforcement (Intel CET shadow stack, ARM BTI) is **locked on** and cannot be disabled by the process.

CFI prevents **code-reuse attacks** — techniques like ROP (Return-Oriented Programming) that bypass WXP by chaining together existing code snippets in unintended ways. The hardware validates that function returns and indirect branches go to legitimate targets.

## How mitigations compose

The four mitigations address different attack techniques and are most effective in combination:

| Attack technique | Blocked by |
|---|---|
| Injecting new executable code | WXP |
| Reusing existing code out of order (ROP/JOP) | CFI |
| Loading a malicious shared library | LSV or TLP |

Together, WXP + CFI + LSV means: the attacker cannot inject new code, cannot reuse existing code out of order, and cannot load malicious libraries. Exploitation becomes dramatically harder.

## Set at exec time, immutable

Like PIP, mitigations are determined by the binary's properties at `exec` time. The kernel sets them; the process cannot change them. A process cannot disable WXP to make its memory writable and executable, and it cannot disable CFI to turn off the shadow stack.

This immutability is the point. A compromised process cannot weaken its own mitigations to make further exploitation easier.

## Viewing a process's mitigations

Mitigation flags appear in `idn show`:

```bash
$ idn show 47
User:         S-1-5-18 (SYSTEM)
PIP:          Isolated / Trust 4096 (Peios)
Mitigations:  WXP LSV CFI
...
```

A process with no mitigations shows:

```
Mitigations:  none
```
