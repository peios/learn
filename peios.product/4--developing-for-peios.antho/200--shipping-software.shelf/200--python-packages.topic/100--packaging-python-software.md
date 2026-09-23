---
title: Packaging Python software
type: how-to
description: How Python libraries and applications are packaged for Peios without pip — where the files go, how a wheel is built and installed in a recipe, bytecode, launchers, and the interpreter pin.
related:
  - peios/package-management/overview
  - peios/install-destinations
  - pekit/recipes/anatomy
  - peios/producing-packages/package-files
---

Peios ships no pip. A Python project becomes a package the same way a C project does: a pekit recipe builds it, the files land under `/usr`, and peipkg installs and verifies them like any other payload. This page is what that recipe does and why, so that a package you write fits the ones already in the pool.

## Where the files go

The interpreter has one directory for installed Python code — its site-packages, inside the triplet directory:

```text
/usr/lib/x86_64-linux-peios/python3.14/site-packages/
```

There is no separate pure-Python location and no `dist-packages`. Ask the interpreter for the path rather than writing it out; `sysconfig.get_path("platlib")` and `sysconfig.get_path("purelib")` both return it on Peios.

Two things follow from the path. It is **versioned**, so a package built for Python 3.14 is not visible to 3.15, and every Python package declares that in its dependencies (see [The interpreter pin](#the-interpreter-pin)). And it sits inside the triplet directory, so a Python package is `architecture = "x86_64"` even when it contains no compiled code.

The system interpreter is the `org.python.python3` package. Its standard
library and shared runtime are in `org.python.python3-libs`; headers and
embedding metadata are in `org.python.python3-devel`; and the static embedding
library is in `org.python.python3-static`. Applications that only run Python do
not need the development or static packages.

## Libraries and applications

Everything in site-packages is importable by every Python program on the system, which makes installing there an interface decision, not a filing one. Peios draws the line by what the software is for:

| The package is… | Modules go to | Package name |
|---|---|---|
| a **library** — other packages import it (`docutils`, `flit_core`) | site-packages | the project's reverse-DNS package name |
| an **application** — people run it (`meson`) | `/usr/lib/x86_64-linux-peios/<name>/` | the project's reverse-DNS package name |

An application's modules are private: nothing else can `import mesonbuild`, so its internals never become an accidental API, and two applications cannot disagree about which version of a dependency site-packages may hold. The application's launcher is the one program that knows the address — it prepends the private directory to `sys.path` before importing. Site-packages stays on the path, so a private application uses shared libraries normally; privacy governs only whether its own modules are offered outward.

Some projects are both — docutils is a library that also ships `rst2man`. Classify by what other packages need from it: if anything imports it, it is a library, and its tools ride along in the same package.

## Building without pip

A recipe replaces pip with three steps that pip would otherwise do behind the scenes.

**Build the wheel** by calling the project's PEP 517 backend directly. The backend is named in the project's `pyproject.toml`; the pool packages Flit Core and Setuptools, and each is a build dependency of the recipe, not of the resulting package:

```sh
python3 -c 'import sys, flit_core.buildapi as b; b.build_wheel(sys.argv[1])' "$PEKIT_OUT/wheel"
```

Run it from the project's source tree. Some backends write into that tree (setuptools leaves `build/` and `*.egg-info` behind); build from a copy when they do, so the fetched source stays pristine. Set `PYTHONDONTWRITEBYTECODE=1` for the same reason.

**Install the wheel** by extracting it — a wheel is a zip archive of exactly the files that belong in site-packages:

```sh
python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' \
  "$PEKIT_OUT"/wheel/*.whl "$PEKIT_OUT$SITE"
```

Keep the `.dist-info` directory: `importlib.metadata` reads it at run time, and its `entry_points.txt` is the input to the next step.

**Generate the launchers.** A project declares its commands under `[project.scripts]`; the wheel records them in `entry_points.txt` under `[console_scripts]`, one `name = module:function` per line. Each becomes a five-line script in `/usr/bin`:

```python
#!/bin/python3
import sys
from docutils.core import rst2man
if __name__ == '__main__':
    sys.exit(rst2man())
```

The interpreter is `/bin/python3`, not `/usr/bin/python3`: `/bin` is the runtime view every program is reached through, and a payload never names `/usr` directly. A private application's launcher carries one more line before the import — `sys.path.insert(0, '/lib/x86_64-linux-peios/meson')` — again through the view.

## Bytecode

The recipe compiles bytecode and ships it in the package:

```sh
python3 -m compileall -q --invalidation-mode checked-hash -s "$PEKIT_OUT" -p / "$PEKIT_OUT$SITE"
```

Python's default is to write `__pycache__` at first import, and Debian's is to write it at install time. Neither is acceptable on Peios: `/usr` is verified against the package manifest and is never written after install, so a `.pyc` that is not in the manifest is either a verification failure or a file that can never be written. Shipping the bytecode also removes the cost — every start-up would otherwise recompile.

`checked-hash` matters. A timestamp-validated `.pyc` embeds the source file's modification time and goes stale silently; a checked-hash one embeds a hash of the source and is re-validated against it on import. That makes the file reproducible, and it means an operator who shadows a `.py` through `/lcl` gets the shadowed source rather than the package's stale bytecode. `-s` and `-p` rewrite the path recorded in each `.pyc` from the staging directory to the installed one, so tracebacks name `/usr/lib/...`.

## The interpreter pin

Every Python package depends on the interpreter's feature version:

```toml
[dependencies]
python3 = ">= 3.14, < 3.15"
```

Bytecode carries a per-version magic number, extension modules carry the interpreter's ABI tag in their file names, and site-packages itself is a versioned path — so nothing in the package survives a minor-version bump. The pin makes that a resolver fact: peipkg will not move the interpreter until rebuilt packages exist. An interpreter bump on Peios is a rebuild of every Python package, which is one pekit sweep.

The Python recipe follows upstream maintenance releases automatically within
the current feature line. Its soft floor is Python 3.14 and its upper bound is
3.15: a 3.14 bug-fix release can be locked and rebuilt unattended, while 3.15
deliberately waits for the coordinated package sweep required by the ABI and
path change.

The interpreter ships PEP 668's `EXTERNALLY-MANAGED` marker in its standard library. Nothing on the system reads it — there is no pip — but a pip an operator installs for their own use will find it and refuse to write into `/usr`, pointing at a virtual environment or `/lcl` instead. The interpreter also omits `ensurepip` and its bundled wheel. Create an environment with `python3 -m venv --without-pip`; install packaged Python software through peipkg.

## A recipe, end to end

The Docutils recipe in the pool is the reference for a library with console scripts: it builds through flit_core, runs the upstream test suite against a copy of the tree, extracts the wheel, generates eleven launchers from `entry_points.txt`, and compiles the bytecode. Meson is the reference for a private application, and Flit Core for the smallest possible case — a backend that builds itself.

## See also

- [Install destinations](~peios/install-destinations) — the permitted top-level paths, including why `/usr/lib/python3.X` is not one of them.
- [Package files](~peios/producing-packages/package-files) — the manifest keys a recipe's package definition may carry.
- [Recipe anatomy](~pekit/recipes/anatomy) — the pekit recipe this page's steps live in.

## Qualifying Python build backends

Flit Core and Setuptools bootstrap themselves with the system interpreter and
`install-wheel`. Their `build.main` targets remain independent of the Python
test ecosystem; their package gates add a separate `build.vendor` target and
offline tests.

The catalogue installer and staged-module checks share the distribution path
`/usr/lib/x86_64-linux-peios/python<major>.<minor>/site-packages`, using the
executing interpreter's major/minor version. The interpreter must also report
that exact path through `sysconfig`.

Test-only Python tools are resolved during the explicit acquisition stage, in a
native root. Pip runs from its own current wheel, which the acquisition step
downloads and checks against the digest PyPI publishes for it, so the root
needs only the Peios Python. The selected backend version constrains the
candidate tool wheel automatically; other requirements follow the upstream test
requirements and current compatible releases. Only portable Python wheels are
accepted. The acquisition output retains every wheel, a requirements file and
`test-tools.json` with their hashes. These inputs enter the corresponding-source
bundle under `acquisition/vendor`. This is a per-job resolved record, not a
manually maintained version list.

The test worker verifies the complete recorded wheel inventory before creating
a private virtualenv. Pip is bootstrapped from its recorded wheel and installs
only recorded local files into that virtualenv. Dependency consistency is
checked there. Pip and the test ecosystem are not added to the build backend's
runtime package or to the system interpreter. Nested virtualenv tests can clear
`PYTHONPATH` and still find their tools. The worker has no external network;
local `file://` package-index fixtures and recorded wheel files remain usable.

The gates run all Flit Core tests and Setuptools's offline functional suite. Setuptools tests explicitly marked `uses_network` are excluded: these
include its live-PyPI project integration matrix. Release-upload tooling and
performance instrumentation are outside this functional package gate. Upstream
platform/version skips and expected failures remain visible in JUnit results;
a dependency import failure or failed assertion fails qualification.

One recorded adjustment applies only to disposable Setuptools test inputs: the
unused coverage-plugin warning category is removed from the copied pytest
configuration when coverage instrumentation is not enabled. Other warning
errors remain enforced.

Peios's runtime Python deliberately omits CPython's regression tests. Setuptools
therefore declares the Python source package as a native test dependency. When
`test.support` is absent, the gate copies its helpers into the private virtualenv
from the source matching the interpreter's exact major, minor and micro version.
Older source-package archives are checked against their source-lock hash before
extraction; prepared source trees are also supported. A version mismatch fails
the gate. No test modules are added to the runtime package.

Each backend's installed-payload checks import from the staging directory and
exercise wheel, metadata and source-archive hooks. The
smoke wheel's complete RECORD is checked against its files, then the wheel is
installed into a fresh directory and its module is imported in a separate
interpreter with an explicit staged search path. Metadata, vendored code,
licenses and checked-hash bytecode are also checked.

For a selected release candidate, run `pekit test --version VERSION` from its
recipe directory, then package and lint it. Only `build:vendor` has network
access; compilation and tests remain offline. Normal release discovery
continues to follow upstream automatically.
