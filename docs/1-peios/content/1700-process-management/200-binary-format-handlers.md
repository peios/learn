---
title: Binary Format Handlers
type: concept
description: How Peios extends the set of executable file formats — registry-defined handlers that match files by magic bytes or extension and route them to a chosen interpreter.
related:
  - peios/process-management/understanding-process-creation
---

The kernel directly recognises ELF binaries and `#!`-prefixed scripts. Anything else — Java jars, foreign-architecture binaries, Windows executables under an emulator — needs a **binary format handler** that matches the file by its content or extension and tells the kernel which interpreter to run.

On Peios, handlers are **defined in the registry** and applied to the kernel by a system service (`ksyncd`). The registry is the source of truth: adding a handler means writing a registry key, removing one means deleting it, and the live kernel state is kept in sync automatically. There is no manual registration step.

## What a handler does

A handler is a rule of the form *"if a file matches this pattern, run this interpreter against it."* When a process calls `exec()` on a file, the kernel checks the file against its built-in formats first (ELF, then `#!`). If neither matches, the kernel walks the registered handler list. The first matching handler causes the kernel to exec the handler's **interpreter** instead, with the original file's path supplied as an argument.

The interpreter does the real work — loading the jar, emulating the foreign instruction set, translating Windows syscalls. From the kernel's point of view, the process that runs is the interpreter; the matched file is just data.

## How handlers are defined

Each handler is a single key under `\System\BinaryFormats\`. The key name identifies the handler; its values describe what the handler matches and what to do when it matches.

| Value | Type | Meaning |
|---|---|---|
| `Type` | `REG_DWORD` | `0` = match by magic bytes, `1` = match by filename extension |
| `Magic` | `REG_BINARY` or `REG_SZ` | Bytes to match (when `Type=0`) or extension string (when `Type=1`). |
| `Mask` | `REG_BINARY` | Bit mask the same length as `Magic`, applied before comparison. Magic-only. |
| `Offset` | `REG_DWORD` | Byte offset into the file where the magic begins. Magic-only. |
| `Interpreter` | `REG_SZ` | Absolute path to the interpreter binary. |
| `Flags` | `REG_DWORD` | Bitfield. `P` preserves the matched file's name as `argv[0]`. `O` opens the file in the kernel and passes a file descriptor (useful for foreign-architecture interpreters that cannot open the file themselves). `F` fixes the interpreter binary in memory at registration so subsequent mount-namespace changes do not break the handler. |
| `Enabled` | `REG_DWORD` | `0` disables the handler without deleting it. `1` makes it eligible. |
| `Priority` | `REG_DWORD` | Lower values match first. Used to resolve overlap between handlers. |
| `Description` | `REG_SZ` | Human-readable description for tooling. Has no behavioural effect. |

There is intentionally no `C` (calculate-credentials-from-interpreter) flag. Peios has no `setuid` bit, and exec never changes a process's identity, so there is nothing for the flag to do.

## Conflict resolution

Two handlers can match the same file — for example, two magic patterns that overlap, or a handler whose mask is a subset of another's. The kernel resolves overlap deterministically:

1. **Lower `Priority` wins.** A handler with `Priority = 10` is consulted before one with `Priority = 50`.
2. **If priorities are equal, alphabetical key name wins.** A handler at `\System\BinaryFormats\java\` is consulted before `\System\BinaryFormats\qemu-arm\` if both have the same priority.

The alphabetical fallback exists because priority is editable and a malformed registry can produce ties. It guarantees that the matching order is always well-defined no matter what the registry contains.

## How the registry becomes live state

`ksyncd` is the system service responsible for projecting the registry into the kernel's binfmt table. At boot, it enumerates `\System\BinaryFormats\`, builds the handler set, and registers each enabled handler via `/proc/sys/fs/binfmt_misc/register`. After boot, it watches the key for changes and re-applies on any add, modify, or delete.

`ksyncd` applies handlers on a **best-effort** basis. If a single handler fails to register — the interpreter binary doesn't exist, the magic field is malformed, the kernel rejects the registration — the handler is skipped and the rest of the set is applied normally. A failure on update leaves the previously-registered version in place rather than removing it. This avoids a single bad edit taking down all binary-format support on the machine.

To make drift visible, `ksyncd` writes a status subkey for each handler under `\System\BinaryFormats\<name>\Status`:

| Value | Meaning |
|---|---|
| `LastApplied` | Timestamp of the last successful registration, or 0 if never. |
| `LastError` | The most recent error string, or empty if the handler is currently live. |
| `Live` | `1` if the kernel currently has this handler registered, `0` otherwise. |

Administrators inspecting the registry can see at a glance which handlers are active and which are misconfigured, without needing to cross-reference `/proc`.

## Identity and mitigations at exec

When a handler fires, the kernel execs the interpreter. From the security model's point of view this is an ordinary exec:

- The **interpreter inherits the calling thread's primary token**, exactly as it would for a `#!` script. The matched file's identity, ownership, and permissions are not consulted for this purpose.
- The **interpreter's mitigations apply**, not the matched file's. `WXP`, signature requirements, and the rest are evaluated against the binary the kernel is actually loading.
- **`NEW_PROCESS_MIN` still applies.** If the calling token has the integrity floor policy and the interpreter file is at a lower integrity level, the child's token is replaced at the file's level — the same rule as any other exec.

There is no path by which a binary format handler can elevate a process. The interpreter runs as whoever called exec, with whatever mitigations the interpreter binary's metadata requires.

## Scope

Registry-defined handlers are **system-global**. `ksyncd` applies the registry-defined set to the root mount namespace, and any process that has not entered its own mount namespace sees those handlers. The registry holds one handler set for the whole machine — there is no per-confinement or per-service handler configuration in the registry.

The kernel's underlying machinery is per-mount-namespace, however. A process holding `SeTcbPrivilege` can enter a fresh mount namespace and register its own handlers directly via `/proc/sys/fs/binfmt_misc/register`, independently of the registry-defined set. This path is intentionally narrow: the ordinary case is the registry-defined global set, and the manual path exists for legitimate use cases — container-style isolation, test harnesses, sandboxed compatibility shims — where the global set is inappropriate. `ksyncd` does not attempt to manage any namespace other than the root and does not overwrite handlers that other code has registered in non-root namespaces.

## What ships by default

Nothing. The base image registers no handlers. Administrators or image builders add the handlers their workloads need — typically `qemu-user-*` for cross-architecture work, a Java handler if a JDK is installed, a Wine handler for Windows binaries, and so on. Each of these is a small set of registry keys that an installer or image-generation tool can lay down.

This default stems from the same principle as the rest of Peios system configuration: nothing is loaded that does not have a stated reason to be there.

## Trust and access control

Three layers gate who can change the binary format handler set:

1. **The registry key SD.** `\System\BinaryFormats\` and its children inherit the standard SYSTEM, Administrators security descriptor. Only principals that satisfy this DACL can create, modify, or delete handler keys. Inheritance means individual handler keys carry the same SD by default; per-handler delegation is possible by setting an explicit SD on a specific key but is not the common case.
2. **The kernel registration interface.** Writing to `/proc/sys/fs/binfmt_misc/register` is gated by the `Tcb` privilege. Even a process that somehow obtains write access to the procfs path cannot register a handler without TCB.
3. **`ksyncd` itself runs as a TCB service.** It is the trusted bridge between the registry and the kernel's binfmt table in the root mount namespace, and the only process expected to write to that table. Other TCB-privileged processes may register handlers in their own mount namespaces — this is a deliberate per-namespace use case, not an unintended bypass.

Together, these layers mean that adding a handler in the global set is a deliberate, audited registry operation by an administrator-equivalent principal, applied by a single trusted service. There is no path by which an unprivileged process can extend what the kernel will execute, in any namespace.
