---
title: Thread operations reference
type: reference
description: The per-thread operations a program uses directly — reading a thread's ID, the exit-notification mechanism behind thread joins, and thread-local storage.
related:
  - peios/threads-and-processes/the-process-and-thread-model
  - peios/threads-and-processes/process-creation-reference
---

This is the thread-level companion to
[the process and thread model](~peios/threads-and-processes/the-process-and-thread-model)
— the operations that act on an individual thread rather than on the process as a
whole.

## Thread IDs

Every thread has its own **thread ID** (TID), returned by `gettid`. Within a
multi-threaded process all threads share one PID — the value `getpid` returns,
which is really the **thread-group ID** (TGID) — but each thread's TID is unique.
In a single-threaded process the TID, PID, and TGID are all the same number.

The TID is how the system targets one specific thread rather than the whole
process: sending a signal to a single thread, setting one thread's CPU affinity, or
addressing it under `/proc`. It names a thread the way a PID names a process — and,
like a PID, it is a reference, not an identity. What a thread is acting as is its
token, never its TID.

The TID is also distinct from the opaque handle a threading library returns when it
creates a thread; that is a library-level identifier, not the kernel's TID.

## Thread-exit notification

A thread can have the kernel notify waiters when it exits — the mechanism threading
libraries build thread join on. `set_tid_address` sets a **clear-tid address** for
the calling thread (and returns its TID). When that thread later terminates, if it
shares memory with other threads, the kernel writes 0 to the integer at that address
and wakes one thread waiting on it (a single futex wake).

A thread waiting for another to finish blocks on that address; the kernel clears it
and wakes the waiter at the exact moment the other thread ends. This is the same
machinery as the `CLONE_CHILD_CLEARTID` flag in
[process creation](~peios/threads-and-processes/process-creation-reference) — that
flag arranges the clear-tid address at thread creation, where `set_tid_address` sets
it afterwards.

## Thread-local storage

**Thread-local storage** (TLS) gives each thread its own private copy of a variable
— a value that is per-thread rather than shared across the process, even though the
threads share the same memory. The per-thread data lives in an ordinary block of
memory; what makes it per-thread is a register pointing at this thread's block, so
the same code reaches a different copy depending on which thread is running.

The kernel's part is maintaining that per-thread pointer. It is set when the thread
is created (the `CLONE_SETTLS` flag carries the address) and, on x86-64, a running
thread can change it through `arch_prctl` with `ARCH_SET_FS` (the older
`set_thread_area` serves the same purpose on 32-bit). Everything above that — how
thread-local variables are laid out and reached in code — is handled by the compiler
and the threading library.

## See also

- [The process and thread model](~peios/threads-and-processes/the-process-and-thread-model) — the conceptual counterpart to this page.
- [Process creation reference](~peios/threads-and-processes/process-creation-reference) — the clone flags that create threads and arrange TLS and clear-tid addresses.
