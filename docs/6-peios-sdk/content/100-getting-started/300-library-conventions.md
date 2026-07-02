---
title: Library conventions
type: concept
description: The rules every libpeios function follows — how success and failure are reported, how the two-call buffer protocol works, how builders and views manage memory, and how file descriptors and constants are handled. Learn these once and they hold across the whole SDK.
related:
  - peios-sdk/getting-started/installing-and-linking
  - peios-sdk/getting-started/your-first-program
  - peios-sdk/reference/security
---

libpeios has a small number of conventions that hold across *every* function in *every* module. They are deliberately uniform: once you know how one function reports an error or returns a variable-length buffer, you know how all of them do. This page is the one to read slowly. Everything else in this documentation assumes it.

The conventions come in four groups: **how results are returned**, **the two-call buffer protocol**, **memory ownership** (builders and views), and **the small stuff** (file descriptors and constants).

## How results are returned

Every entry point reports success or failure through its return type. There are three return shapes, and the shape tells you how to read the result.

### `int` — a file descriptor, or zero

A function returning `int` returns either:

- a **file descriptor** (a non-negative `int`), when its job is to open something — a token, a registry key, an event stream; or
- **`0`** on success, when it performs an action with no handle to hand back; and
- **`-1` on failure**, with the reason in `errno`.

```c
int fd = peios_token_open_self(/* … */);
if (fd < 0) {
    /* errno is set — perror(), strerror(errno), etc. */
}
```

### `ssize_t` — a byte length

A function returning `ssize_t` produces a **variable-length result** — a SID, a serialised security descriptor, a formatted string, a registry value. It returns:

- the **length in bytes** of the result on success (`>= 0`); or
- **`-1` on failure**, with the reason in `errno`.

These are the functions that use the [two-call buffer protocol](#the-two-call-buffer-protocol) below. The returned length is always the *full* length of the result, which is what makes the protocol work.

For functions that format a **string**, the returned length excludes the terminating `NUL` — exactly like `snprintf`. So a return of `41` means "41 characters plus a NUL"; size your buffer as `len + 1`.

### Structured results — out-parameters

When a call produces more than one value, or a value that isn't naturally a length or an fd, it writes through **out-parameters** and returns `int` (`0` / `-1`). The access check is the archetype: it returns `0` when access is granted and `-1` with `errno == EACCES` when it is denied, and it writes the *granted access mask* through an out-parameter either way.

```c
uint32_t granted = 0;
int rc = peios_access_check(/* … */, &granted);
/* rc == 0: granted; rc == -1 && errno == EACCES: denied.
   `granted` is populated in both cases. */
```

A denial is a normal, expected outcome, not a bug — which is why it is reported the same disciplined way as any other errno, rather than through a separate channel.

### errno

Failure is *always* reported through the standard C `errno`. The library sets `errno` on every `-1` return and uses ordinary, portable errno values — there are no libpeios-specific or PKM-specific error numbers to learn. The ones you will see most:

| errno | Meaning in libpeios |
|---|---|
| `EINVAL` | Malformed input — a bad SID, an unparseable SDDL string, an argument out of range. |
| `ERANGE` | Your output buffer was non-zero but too small. Nothing was written. (See the protocol below.) |
| `EACCES` | An access check denied the request. |
| `ENOMEM` | An allocation failed (for the heap-backed builders). |
| `EBADF`, `ESRCH`, `EFAULT` | The usual Linux meanings — a bad fd or pidfd, a vanished process, a bad pointer. |

Because the values are standard, `strerror`, `perror`, and your language's normal errno handling all work unchanged. Check the return value first, *then* read `errno` — like any POSIX call, `errno` is only meaningful after a call that signalled failure.

> Nothing ever unwinds across the boundary. The library is compiled to abort rather than propagate a panic through the C ABI, so a call either returns a value you can inspect or the process dies — it never leaves you with a corrupt half-state to reason about.

## The two-call buffer protocol

Every function that returns variable-length bytes — anything with an `ssize_t` return and an `(out, cap)` pair — follows the same **getxattr-style** protocol. It is the single most important convention in the library, so it is worth internalising.

The rule:

- Call with **`cap == 0`** (or a **`NULL` buffer**) to **probe**: the function writes nothing and returns the number of bytes the result needs.
- Call with a buffer of **at least that size** to **retrieve**: the function fills the buffer and returns the number of bytes it wrote.
- Call with a **non-zero but too-small** buffer and it **fails with `ERANGE` and writes nothing** — never a truncated or partial result.

That last point is the safety property that makes the protocol trustworthy: a too-small buffer is a clean, detectable error, not a silent truncation. You never have to wonder whether you got the whole thing.

The canonical two-call sequence:

```c
/* 1. Probe for the size. */
ssize_t need = peios_sid_format(sid, sid_len, NULL, 0);
if (need < 0) { /* errno set */ }

/* 2. Allocate. For a string, add 1 for the NUL. */
char *buf = malloc(need + 1);

/* 3. Retrieve. */
ssize_t n = peios_sid_format(sid, sid_len, buf, need + 1);
if (n < 0) { /* errno set */ }
/* buf now holds the formatted SID; n is its length (excluding the NUL). */
```

When you already know a comfortable upper bound, you can skip the probe and call once with a big-enough buffer. Some results have a fixed maximum the library gives you a constant for — for example a SID is never larger than `PEIOS_SID_MAX_BYTES`, so a stack buffer of that size always fits and never needs a probe. Those shortcuts are called out where they apply; the two-call protocol is always available as the general fallback.

## Memory ownership

libpeios never hands you an allocation to `free()`. Instead it uses two ownership patterns — **builders** for constructing byte buffers and **views** for reading them — and both keep the memory question simple: you own your buffers, the library borrows or copies, and the two never get confused.

### Builders — constructing buffers

Anything you *assemble* (an ACL, a security descriptor, a token specification) is built with a **builder**: an opaque, heap-backed object you create, feed, take the bytes from, and free.

Builders have three properties worth knowing up front:

1. **They are sticky-error.** The incremental `add`/`set` calls return `void` — they never fail inline. If one hits a problem (a bad input, an allocation failure), the builder **latches** the error and every later call is a no-op. You do not have to check each step. Instead you check *once*, at the end: either call the builder's `_error()` accessor (it returns the latched errno, or `0` if all is well), or notice that taking the bytes fails. This lets you write a long, clean sequence of `add` calls without a conditional after every line.

2. **You free every builder you create.** Each `_new()` is paired with a `_free()`. Builders also have a `_reset()` that drops the accumulated content *and* clears the sticky error, so you can reuse one builder across several objects instead of churning allocations.

3. **Taking the bytes: borrow (and sometimes copy).** Every builder has a **`_bytes()`** that hands back a pointer *into the builder* — zero-copy, no allocation. That pointer is valid only until the next mutating call, `_reset()`, or `_free()` on that builder. Use it when you are going to consume the bytes immediately (for instance, pass them straight into a kernel call). The call comes in two shapes, and not every builder offers a copying counterpart:
   - The **security builders** (`peios_acl_builder_bytes`, `peios_sd_builder_bytes`) *return the pointer* — `NULL` if the sticky error is set — and write the length through an optional `len_out` pointer. Each is paired with a **`_finish()`** that copies the buffer into a caller-supplied buffer using the [two-call protocol](#the-two-call-buffer-protocol) above, for when the bytes must outlive the builder.
   - **`peios_token_builder_bytes` and `peios_mp_writer_bytes`** are shaped the other way round: they *return the length* as an `ssize_t` (`-1` with `errno` on a latched error) and write the borrowed pointer through an out-parameter (which may be `NULL` to get just the length). Neither has a `_finish()` — copy the borrowed bytes yourself if they need to outlive the builder.

A typical builder lifecycle:

```c
peios_acl_builder *b = peios_acl_builder_new();   /* NULL on OOM */
peios_acl_builder_allow(b, sid, sid_len, mask, 0); /* void — no check */
peios_acl_builder_deny(b, other, other_len, mask, 0);

size_t len;
const void *acl = peios_acl_builder_bytes(b, &len); /* NULL if errored */
if (!acl) { int err = peios_acl_builder_error(b); /* handle */ }
/* … use `acl` before the next mutation … */

peios_acl_builder_free(b);
```

### Views — reading buffers

Anything you *parse* (a security descriptor, an ACL, a SID array from a token) is read through a **view**: a small, caller-allocated struct that you point at a buffer you already hold.

Views have their own two rules:

1. **You allocate the view; it is stack-friendly.** A view type such as `peios_sd_view` is an opaque fixed-size struct — you declare one as a local variable and pass its address to the parse call. No heap, no free. The struct's fields are opaque: never read them directly; use the accessor functions.

2. **A view borrows the buffer it parses — zero-copy.** The parse call does not copy the data; the view points *into* your buffer, and every accessor that yields a SID, a nested ACL, or a blob hands back a pointer into that same buffer. So the buffer must **stay alive and unmodified** for as long as the view — and anything you derived from it — is in use. Free or mutate the underlying buffer and every pointer the view gave you dangles.

```c
peios_sd_view sd;                        /* on the stack */
if (peios_sd_parse(buf, buf_len, &sd) != 0) { /* EINVAL */ }

const void *owner; size_t owner_len;
if (peios_sd_view_owner(&sd, &owner, &owner_len) == 0) {
    /* `owner` points INTO `buf` — valid only while `buf` lives. */
}
```

Views compose: parsing a security descriptor gives you a `peios_sd_view`, from which you obtain a `peios_acl_view` for its DACL, from which you obtain each `peios_ace_view`. Every one of them borrows the *same* original buffer, so keeping that one buffer alive keeps the whole tree valid.

The symmetry is the thing to remember: **builders own heap and must be freed; views own nothing and borrow your buffer.** Constructing is builders, reading is views, and neither ever asks you to free something the library allocated.

## File descriptors

Handles that libpeios opens — tokens, registry keys, event streams — are **raw `int` file descriptors**, the same kind `open()` gives you. You close them with `close()`, poll them, and pass them across `exec` (or not) with the usual fd machinery.

They are created **`O_CLOEXEC` by default**: a handle does not leak across an `exec` unless you deliberately clear the flag with `fcntl`. This is the safe default for security-sensitive handles — a token or key fd will not silently end up in a child process you launch.

## Constants

libpeios does **not** invent its own names for the kernel's wire constants. The access-right bits, ACE types, control flags, and mapping structs all come straight from the `<pkm/*.h>` UAPI headers, and you use those published names directly: `KACS_ACCESS_*`, `KACS_ACE_TYPE_*`, `KACS_SD_*`, `struct kacs_generic_mapping`, and so on. There is no parallel `PEIOS_*` aliasing to translate in your head — the name in the PSD, the name in the kernel header, and the name you write in your code are the same name.

The handful of constants that *are* libpeios's own — buffer-size ceilings like `PEIOS_SID_MAX_BYTES`, and enums for convenience selectors like `enum peios_wks` (well-known SIDs) — are prefixed `PEIOS_` and documented with the module that defines them.

## The conventions at a glance

| Convention | The rule |
|---|---|
| `int` return | fd or `0` on success; `-1` + `errno` on failure. |
| `ssize_t` return | byte length on success; `-1` + `errno` on failure. Strings exclude the `NUL`. |
| Two-call protocol | `cap == 0` / `NULL` probes for the size; too-small non-zero buffer → `ERANGE`, nothing written. |
| errno | standard values only; check the return first, then `errno`. |
| Access denial | `-1` + `EACCES`, with the granted mask still written to the out-param. |
| Builders | heap-backed, sticky-error, `void` adders; check `_error()` at the end; `_free()` every one; `_bytes()` borrows, and the security builders add a `_finish()` that copies. |
| Views | caller-allocated (stack), opaque, borrow the parsed buffer; keep that buffer alive and unmodified. |
| File descriptors | raw `int`, `O_CLOEXEC` by default, closed with `close()`. |
| Constants | use the `<pkm/*.h>` `KACS_*` names directly; only libpeios's own additions are `PEIOS_*`. |

With these in hand, the module documentation reads as just "what does this function do?" — the *how* of memory and errors is answered here, once, for all of them. Next: [your first program](~peios-sdk/getting-started/your-first-program), which puts the protocol and the error model to work in something you can compile.
