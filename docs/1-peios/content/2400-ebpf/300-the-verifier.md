---
title: The Verifier
type: concept
description: How the BPF verifier statically proves safety properties of loaded programs, the role of BTF and CO-RE, the JIT compiler, and the safety guarantees provided.
related:
  - peios/ebpf/overview-and-design
  - peios/ebpf/program-types-and-attach-points
  - peios/ebpf/maps-and-helpers
---

The verifier is the BPF subsystem's safety boundary. Every program loaded via `bpf(BPF_PROG_LOAD, ...)` must pass the verifier before it is JIT-compiled and made available for attachment. A program that does not pass the verifier is rejected — the kernel does not run unverified bytecode.

## What the verifier proves

The verifier walks the program's control-flow graph and proves a set of safety properties:

| Property | What it means |
|---|---|
| **Memory safety** | Every load and store accesses memory within bounds determined statically. No raw pointers, no out-of-bounds access. |
| **Bounded execution** | Loops are bounded (the verifier requires a finite iteration count or uses bounded helpers like `bpf_loop`). The program terminates within the verifier's instruction budget. |
| **Type safety** | Pointer types are tracked through the program. A pointer to a packet cannot be used as a pointer to a map value. |
| **Helper/kfunc allowlist** | The program can only call helpers and kfuncs permitted for its program type. |
| **Stack safety** | Stack reads and writes are tracked; reading uninitialized stack is rejected. |
| **Privileged operation gating** | Some operations require additional privilege checks beyond loading the program; the verifier enforces these per program type. |

A program that survives the verifier is guaranteed (modulo verifier bugs) not to crash the kernel by violating these properties. It can still misbehave — emit wrong data, return wrong values, slow the system — but it cannot scribble over kernel memory or access pointers it shouldn't.

## How the verifier works

The verifier runs as part of `BPF_PROG_LOAD`. It builds a control-flow graph from the bytecode and performs symbolic execution along every path, tracking:

- Register types and value ranges
- Memory access bounds
- Helper/kfunc invocations and their type signatures
- Stack contents
- Program complexity (instruction count)

It is a forward-only abstract interpreter. It does not run the program; it analyses every reachable instruction sequence and rejects the program if any path could violate a safety property.

The complexity budget bounds the verifier's own runtime — programs that require too many states to verify are rejected with a complexity error. This is why BPF programs use bounded loops, tail calls, and BPF-to-BPF function calls: they help the verifier scale.

## The JIT compiler

After verification, the program is JIT-compiled to the host architecture's native instructions. The JIT runs once at load time; the resulting native code is what executes when the program is invoked at its attach point. This makes BPF programs comparable in performance to compiled C — orders of magnitude faster than interpreting bytecode.

Each architecture has its own JIT (x86, arm64, riscv, s390, etc.). On a Peios-supported architecture, the JIT is enabled by default. Architectures without a JIT fall back to interpretation, but this is not the standard configuration.

## BPF Type Format (BTF)

BTF is a compact format for describing the types used by a kernel and its BPF programs. It contains:

- Kernel struct definitions
- Function signatures
- Tracepoint argument types
- Map key/value types

BTF is embedded in the kernel image (and exposed at `/sys/kernel/btf/vmlinux`) and in BPF object files. It serves two purposes:

1. **Verifier type-checking.** The verifier uses BTF to ensure programs access struct fields by their actual layout, not by hardcoded offsets.
2. **CO-RE relocations.** See below.

## CO-RE — Compile Once, Run Everywhere

A challenge for BPF programs is portability across kernel versions: a struct's layout might change between kernels, and a program compiled against one kernel's headers won't work on another. CO-RE solves this:

1. The BPF program is compiled with **CO-RE relocations** — annotations that say "load field `X` of struct `Y`" rather than hardcoding offsets.
2. At load time, the BPF loader (libbpf) resolves these relocations against the running kernel's BTF, patching the bytecode with the correct offsets.
3. The verified, relocated program runs on whatever kernel it's loaded on, regardless of which kernel it was compiled against.

CO-RE makes BPF programs distributable as pre-compiled binaries. A single Tetragon binary, for example, can run on any kernel with BTF support — no recompilation per kernel version.

## BPF-to-BPF function calls

BPF programs can call other BPF functions (subprograms within the same object) and tail-call into other programs (transferring control without returning). Both are verified as part of program load:

- **Subprograms** are verified as if their body were inlined; the call site sees the subprogram's effects on registers and stack.
- **Tail calls** transfer control to a program registered in a `BPF_MAP_TYPE_PROG_ARRAY` map. Tail-call depth is bounded (33 by default) to prevent stack overflow.
- **Sleepable tail calls** — as of kernel 7.0, sleepable programs may tail-call other sleepable programs, enabling more flexible composition.

## BPF exceptions

As of kernel 6.7, programs can use `bpf_throw()` to raise an exception that aborts the program early without continuing through normal control flow. Exceptions unwind the BPF stack and return a predefined value to the program's caller. They are useful for early-exit on error conditions, since the verifier's complexity limits often make conventional `if`-chains expensive.

## bpf_fastcall and private stack

Recent additions optimize the verifier's analysis and the runtime cost of BPF programs:

- **`bpf_fastcall`** (kernel 6.13) — an attribute that tells the verifier a kfunc has no side effects and clobbers a known set of registers, allowing the verifier to skip preserving registers across the call.
- **Private stack** (kernel 6.13) — programs can request a private stack rather than sharing the per-CPU BPF stack, useful for programs with large local state.
- **Union arguments in trampoline programs** (kernel 6.18) — fentry/fexit programs can receive arguments declared as unions, matching kernel function signatures more accurately.

## Resilient queued spinlocks

As of kernel 6.15, BPF programs can use **resilient queued spinlocks** for in-kernel synchronization. Unlike traditional spinlocks, they detect deadlock conditions and return an error rather than spinning indefinitely, which is critical because the verifier cannot statically prove freedom from BPF-induced deadlocks across multi-program interactions.

## See also

- [Maps and helpers](maps-and-helpers) — the data structures the verifier tracks across program execution.
- [Peios integration](peios-integration) — Peios-native helpers and kfuncs, all of which go through the same verification pipeline.
- [Privileges and trust](privileges-and-trust) — the privilege gate that complements the verifier as defense.
