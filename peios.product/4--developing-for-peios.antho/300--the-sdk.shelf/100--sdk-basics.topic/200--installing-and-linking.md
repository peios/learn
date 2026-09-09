---
title: Installing and linking
type: how-to
description: The packages that make up libpeios, the headers you include, and how to compile and link against the library — with pkg-config, by hand, statically, and from non-C languages.
related:
  - peios/sdk-basics/what-is-the-peios-sdk
  - peios/sdk-basics/your-first-program
  - peios/sdk-conventions/library-conventions
---

libpeios ships as a small set of packages, split the same way a C library conventionally is: a lean runtime package that programs depend on, and a development package that carries the headers and the linker symlink. You install the runtime everywhere the library is used and the development package only where you compile.

## The packages

| Package | Contents | When you need it |
|---|---|---|
| `dev.peios.libpeios` | The versioned shared object `libpeios.so.0` (the runtime soname). | At **runtime**, on every machine that runs a program linked against the library. Pulled in automatically as a dependency of anything built against it. |
| `dev.peios.libpeios-devel` | The public headers (`peios.h` + `peios/*.h`), the unversioned `libpeios.so` linker symlink, and the `peios.pc` pkg-config descriptor. Depends on a matching `dev.peios.libpeios` and the Peios kernel UAPI headers. | At **build time**, on machines where you compile. |
| `dev.peios.libpeios-static` | The static archive `libpeios.a`. | Only if you link the library **statically** instead of against the shared object. |
| `dev.peios.libpeios-debuginfo` | Split DWARF debug info, build-id indexed. | Debugging or profiling through the library. |
| `dev.peios.libpeios-debugsource` | The referenced Rust sources for the debug info. | Stepping into the library's own source in a debugger. |

Installing `dev.peios.libpeios-devel` pulls in the matching `dev.peios.libpeios` runtime and `kernel-headers` automatically — the development package pins the exact runtime version whose ABI its headers describe, so the headers you compile against and the shared object you load cannot disagree.

## Obtaining the SDK

On a Peios system, the development package comes from the package repository the system is configured with:

```sh
peipkg install dev.peios.libpeios-devel
```

The packages are built, signed and published into the Peios repository, but that repository is not yet hosted at a public address. Until it is, the source is the route for anyone outside the project. All of it is public:

| Repository | What it is |
|---|---|
| <https://github.com/peios/libpeios> | The library. `cargo build --release` produces `libpeios.so` and `libpeios.a`; the headers are in `include/`. |
| <https://github.com/peios/librsi> | The registry-source library, built the same way. |
| <https://github.com/peios/peios-rs> | The Rust `peios` and `peios-sys` crates. |
| <https://github.com/peios/peios-cabi> | The shared C-ABI substrate both libraries are built on. |

The library builds themselves need nothing beyond a Rust toolchain: they pin the kernel ABI through their Cargo dependencies. Compiling a C program against the resulting headers needs the `<pkm/*.h>` kernel UAPI headers described below.

## The headers

Everything lives under `<peios/…>`, with one umbrella:

```c
#include <peios.h>          /* the whole API */
```

or, for a tighter compile surface, just the concept headers you use:

```c
#include <peios/security.h> /* SIDs, security descriptors, ACLs */
#include <peios/token.h>    /* tokens */
#include <peios/access.h>   /* access checks */
#include <peios/file.h>     /* file security */
#include <peios/process.h>  /* process security */
#include <peios/registry.h> /* the LCS registry */
#include <peios/msgpack.h>  /* msgpack framing */
#include <peios/event.h>    /* the KMES event stream */
```

The headers are hand-written and are the real API — they carry the prose docs and the layout notes that a generated header can't. (Internally they are checked against the library's Rust surface by a cbindgen-based verifier, so they cannot silently drift from what the shared object actually exports. You do not interact with that machinery; it just means the header you read is the contract you get.)

### The `<pkm/*.h>` dependency

The Peios headers do not re-invent the kernel's wire constants — they use them directly. So `<peios/security.h>` includes `<pkm/sid.h>` and `<pkm/sd.h>`, and the other headers pull in their matching `<pkm/*.h>` UAPI headers for the `KACS_*`, `LCS_*`, and `KMES_*` constants and the `#[repr(C)]` argument structs. Those PKM kernel UAPI headers must be on your include path when you compile. They ship with the Peios kernel headers; on a normal Peios development install they are already where the toolchain looks. If a build fails with `fatal error: pkm/sid.h: No such file or directory`, that is what is missing — add the kernel UAPI include directory to your compiler's search path.

## Compiling and linking

### With pkg-config (recommended)

The development package installs a `peios.pc` descriptor, so pkg-config knows the include and library flags:

```sh
cc myprog.c $(pkg-config --cflags --libs peios) -o myprog
```

`pkg-config --cflags peios` expands to the include flags and `--libs peios` to `-lpeios` plus the library directory. This is the form to prefer — it stays correct across install prefixes and multiarch library directories.

### By hand

If you are not using pkg-config, link against `-lpeios` directly:

```sh
cc myprog.c -lpeios -o myprog
```

Add `-I` / `-L` flags if your headers and library live outside the compiler's default search paths.

### Statically

Install `dev.peios.libpeios-static` and point the linker at the archive:

```sh
cc myprog.c -o myprog /usr/lib/x86_64-linux-peios/libpeios.a
```

The static archive is also what the library's own integration tests link against, so it is a fully supported way to build. Static linking folds the library into your binary — you then do not need the `libpeios` runtime package on the target, though you still need whatever C runtime your program uses.

## Linking from other languages

Because libpeios is a C ABI, any language with a C FFI can call it. The shape is always the same: point the FFI at the `libpeios.so.0` shared object (or the static archive), declare the `peios_*` functions with their C signatures, and follow the [library conventions](~peios/sdk-conventions/library-conventions) for buffers and errors exactly as a C caller would.

- **Rust** — use the maintained bindings: the safe **`peios`** crate (or the raw `peios-sys`), covered in [Using the SDK from Rust](~peios/sdk-basics/using-the-sdk-from-rust). You don't need to hand-roll `bindgen`. (The library *is* Rust internally, but the crates still bind it strictly as a C library through the stable ABI — the supported entry point.)
- **Go** — cgo against `<peios.h>` with `#cgo pkg-config: peios`.
- **Python** — `ctypes` or `cffi` against `libpeios.so.0`.
- **C++** — include the headers directly; they are wrapped in `extern "C"` and compile as C++.

The one rule that matters across every language: the errno-based error model and the caller-buffer / two-call buffer protocol are part of the contract, not a C convenience. Read [Library conventions](~peios/sdk-conventions/library-conventions) before you wrap the API in another language's idioms.

## librsi — the registry-source library

Everything above describes **libpeios**. If you are writing a [registry source](~peios/registry-sources/overview), you link the sibling library **librsi** instead (or as well). It is built on the same [`peios-cabi` substrate](~peios/sdk-basics/what-is-the-peios-sdk) and follows the identical [library conventions](~peios/sdk-conventions/library-conventions) — raw fds, the `int`/`ssize_t` error model, the borrow discipline.

### Packaging status

librsi is **not yet packaged**. It will take the same split as libpeios, under the `dev.peios.librsi` name: a runtime package, `-devel` with the headers, the `librsi.so` linker symlink and an `rsi.pc` descriptor, plus `-static`, `-debuginfo` and `-debugsource`. Until that lands, build it from source:

```sh
git clone https://github.com/peios/librsi
cd librsi && cargo build --release
# target/release/librsi.so, target/release/librsi.a, headers in include/
```

The `<rsi/*.h>` headers include `<pkm/lcs.h>`, so the same UAPI-header requirement described above applies.

### Headers and linking

Include the umbrella or the individual concept headers:

```c
#include <rsi.h>            /* the whole librsi API */
/* or: */
#include <rsi/source.h>    /* registration */
#include <rsi/request.h>   /* decoding requests */
#include <rsi/response.h>  /* building responses */
```

and, once the package exists, compile with pkg-config (the descriptor's module name will be `rsi`):

```sh
cc mysource.c $(pkg-config --cflags --libs rsi) -o mysource
```

From a source build, point the compiler at the checkout instead: `-I<checkout>/include -L<checkout>/target/release -lrsi`, or link against `librsi.a` for a static build — the same three forms shown for libpeios above. The two libraries are independent: a program can be a client (libpeios), a source (librsi), or both, linking each as needed.
