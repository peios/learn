"""Qualify style configurations in temporary files, with optional read-only samples."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from bootstrap import ROOT, verify_runtimes, verify_tools

CONFIG = ROOT / "configs"
VENV = ROOT / ".venv/bin"
BIN = ROOT / ".bin"
NODE = ROOT / "node_modules/.bin"


def execute(
    arguments: list[str], code: str | None = None, cwd: Path = ROOT
) -> subprocess.CompletedProcess[str]:
    """Run a bounded check with caches confined to the tooling directory."""
    environment = os.environ.copy()
    environment.update(
        {
            "GOTOOLCHAIN": "local",
            "GOCACHE": str(ROOT / ".cache/go-build"),
            "CARGO_TARGET_DIR": str(ROOT / ".cache/cargo-target"),
            "RUFF_CACHE_DIR": str(ROOT / ".cache/ruff"),
            "MYPY_CACHE_DIR": str(ROOT / ".cache/mypy"),
        }
    )
    return subprocess.run(
        arguments, input=code, cwd=cwd, env=environment, text=True, capture_output=True, timeout=60
    )


def format_code(language: str, code: str) -> str:
    """Format standard input using exactly the selected configuration."""
    commands = {
        "kernel-rust": [
            "rustfmt",
            "+1.83.0",
            "--config-path",
            str(CONFIG / "kernel-rustfmt.toml"),
            "--emit",
            "stdout",
        ],
        "c": [str(VENV / "clang-format"), "-style=file:" + str(CONFIG / "clang-format.yaml")],
        "kernel-c": [
            str(VENV / "clang-format"),
            "-style=file:" + str(CONFIG / "kernel-clang-format.yaml"),
        ],
        "rust": [
            "rustfmt",
            "+1.98.1",
            "--config-path",
            str(CONFIG / "rustfmt.toml"),
            "--emit",
            "stdout",
        ],
        "go": ["gofmt"],
        "python": [
            str(VENV / "ruff"),
            "format",
            "--config",
            str(CONFIG / "ruff.toml"),
            "--stdin-filename",
            "sample.py",
            "-",
        ],
        "typescript": [
            str(NODE / "prettier"),
            "--config",
            str(CONFIG / "prettier.json"),
            "--parser",
            "typescript",
        ],
        "shell": [str(BIN / "shfmt"), "-i", "4"],
        "starlark": [str(BIN / "buildifier"), "-type=bzl"],
    }
    result = execute(commands[language], code)
    if result.returncode:
        raise RuntimeError(f"{language} formatter failed: {result.stderr}")
    return result.stdout


def main() -> None:
    """Exercise policy examples and write a machine-readable qualification result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kernel", type=Path, help="Read-only kernel checkout for representative wrappers"
    )
    args = parser.parse_args()
    versions = verify_runtimes()
    tools = verify_tools()
    results: list[dict[str, object]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        results.append({"name": name, "passed": passed, "detail": detail})

    def checked(
        name: str,
        command: list[str],
        should_pass: bool = True,
        diagnostic: str = "",
        cwd: Path = ROOT,
    ) -> str:
        result = execute(command, cwd=cwd)
        output = result.stdout + result.stderr
        passed = (result.returncode == 0) == should_pass
        if diagnostic:
            passed = passed and diagnostic in output
        record(name, passed, output[-3000:] if not passed else "")
        return output

    cases = {
        "kernel-rust": "sample.rs",
        "c": "sample.c",
        "kernel-c": "sample.c",
        "rust": "sample.rs",
        "go": "sample.go",
        "python": "sample.py",
        "typescript": "sample.ts",
        "shell": "sample.sh",
        "starlark": "sample.bzl",
    }
    formatted: dict[str, str] = {}
    for language, name in cases.items():
        first = format_code(language, (ROOT / "fixtures" / name).read_text())
        formatted[language] = first
        record(language + " formatter idempotent", format_code(language, first) == first)
    record("C one-line guard retained", "if (value < 0) return 0;" in formatted["c"])
    record(
        "kernel C uses tabs and next-line function braces",
        "int normalize(int value)\n{" in formatted["kernel-c"] and "\tif" in formatted["kernel-c"],
    )
    record(
        "long C diagnostic remains intact",
        'return "A deliberately intact' in formatted["c"]
        and 'meaning of the message."' in formatted["c"],
    )
    record("Go uses tabs", "\tif" in formatted["go"])
    record("Rust uses four spaces", "    if" in formatted["rust"])
    record("TS keeps serialized name", '"legacy_name"' in formatted["typescript"])
    record("TS keeps multiline trailing comma", '"final_name",' in formatted["typescript"])

    javascript = execute(["node", str(ROOT / "scripts/check-javascript.mjs")])
    if javascript.returncode == 0:
        results.extend(json.loads(javascript.stdout))
    else:
        record("JavaScript policy cases", False, javascript.stdout + javascript.stderr)

    with tempfile.TemporaryDirectory(prefix="peios-style-") as temporary:
        work = Path(temporary)
        for language, name in cases.items():
            if language not in {"kernel-c", "kernel-rust"}:
                (work / name).write_text(formatted[language])
        ruff = [str(VENV / "ruff"), "check", "--config", str(CONFIG / "ruff.toml")]
        mypy = [str(VENV / "mypy"), "--config-file", str(CONFIG / "mypy.ini")]
        checked("Python valid fixture", ruff + [str(work / "sample.py")])
        checked("Python typed fixture", mypy + [str(work / "sample.py")])
        untyped = work / "untyped.py"
        untyped.write_text("def echo(value):\n    return value\n")
        checked("Python missing annotations rejected", ruff + [str(untyped)], False, "ANN001")
        checked("Python missing types rejected", mypy + [str(untyped)], False, "no-untyped-def")
        ignored = work / "ignored.py"
        ignored.write_text(
            "def echo(value):  # noqa: ANN001, ANN201 - fixture for a dynamic adapter\n    return value\n"
        )
        checked("Python narrow annotation exception", ruff + [str(ignored)])
        wildcard = work / "wildcard.py"
        wildcard.write_text(
            "from math import *  # deliberate wildcard fixture; preference is not a ban\n"
        )
        checked("Python wildcard preference not hard failure", ruff + [str(wildcard)])
        for directory in ["vendor", "generated"]:
            path = work / directory / "bad.py"
            path.parent.mkdir()
            path.write_text("not valid python (((\n")
            checked("Python " + directory + " excluded even explicitly", ruff + [str(path)])
        side_effects = work / "side_effects.py"
        side_effects.write_text(
            "# isort: off\n# Registration order is intentional in this fixture.\nimport z_registration  # noqa: F401 - registration side effect\nimport a_registration  # noqa: F401 - registration side effect\n# isort: on\n"
        )
        checked("Python side-effect import order exception", ruff + [str(side_effects)])

        tsconfig = json.loads((CONFIG / "tsconfig.json").read_text())
        tsconfig["files"] = ["sample.ts"]
        (work / "tsconfig.json").write_text(json.dumps(tsconfig))
        checked(
            "TypeScript strict valid fixture",
            [str(NODE / "tsc"), "-p", str(work / "tsconfig.json")],
        )
        (work / "sample.ts").write_text(
            "export function missing(value: string | null): string { return value; }\n"
        )
        checked(
            "TypeScript nullable error rejected",
            [str(NODE / "tsc"), "-p", str(work / "tsconfig.json")],
            False,
            "TS2322",
        )

        tidy = [
            str(VENV / "clang-tidy"),
            "--config-file=" + str(CONFIG / "clang-tidy.yaml"),
            "--warnings-as-errors=*",
        ]
        checked("C valid fixture", tidy + [str(work / "sample.c"), "--", "-std=c11"])
        c_bad = work / "bad.c"
        c_bad.write_text("int f(int x) { if (x)\nreturn 1; return 0; }\n")
        checked(
            "C next-line unbraced body rejected",
            tidy + [str(c_bad), "--", "-std=c11"],
            False,
            "readability-braces-around-statements",
        )
        # These passing commands confirm a documented gap, not policy compliance.
        for name, code in {
            "C multiline condition remains manual": "int f(int x) { if (\nx\n) return 1; return 0; }",
            "C mixed chain remains manual": "int f(int x) { if (x) { x++; return x; } else return 0; }",
        }.items():
            c_bad.write_text(code + "\n")
            checked(name, tidy + [str(c_bad), "--", "-std=c11"])

        checked(
            "Shell quoted arguments",
            [str(BIN / "shellcheck"), "--external-sources", str(work / "sample.sh")],
        )
        (work / "sample.sh").write_text('#!/bin/sh\nprintf "%s\\n" $1\n')
        checked(
            "Shell unquoted expansion rejected",
            [str(BIN / "shellcheck"), str(work / "sample.sh")],
            False,
            "SC2086",
        )
        buildifier = [
            str(BIN / "buildifier"),
            "-mode=check",
            "-type=bzl",
            "-lint=warn",
            "-warnings=load,unused-variable,function-docstring",
        ]
        checked(
            "Bazel syntax, format and selected warnings", buildifier + [str(work / "sample.bzl")]
        )
        (work / "sample.bzl").write_text('load("//:defs.bzl", "unused")\n')
        checked(
            "Bazel unused import rejected",
            buildifier + [str(work / "sample.bzl")],
            False,
            "unused",
        )
        (work / "sample.bzl").write_text("not valid (((\n")
        checked(
            "Bazel syntax error rejected",
            [str(BIN / "buildifier"), "-mode=check", "-type=bzl", str(work / "sample.bzl")],
            False,
        )

        go_work = work / "go"
        go_work.mkdir()
        (go_work / "go.mod").write_text("module example.test/stylefixture\n\ngo 1.26.0\n")
        (go_work / "sample.go").write_text(formatted["go"])
        checked("Go vet", ["go", "vet", "./..."], cwd=go_work)
        (go_work / "sample.go").write_text(
            'package sample\nimport "fmt"\nfunc Report() { fmt.Printf("%d", "wrong") }\n'
        )
        checked(
            "Go vet catches format mismatch",
            ["go", "vet", "./..."],
            False,
            "wrong type",
            cwd=go_work,
        )
        (work / "Cargo.toml").write_text(
            '[package]\nname = "style_fixture"\nversion = "0.0.0"\nedition = "2021"\n[lib]\npath = "sample.rs"\n'
        )
        checked(
            "Rust selected Clippy checks",
            [
                "cargo",
                "+1.98.1",
                "clippy",
                "--offline",
                "--",
                "-A",
                "clippy::all",
                "-D",
                "clippy::correctness",
            ],
            cwd=work,
        )
        (work / "sample.rs").write_text(
            "pub fn equal_to_itself(value: i32) -> bool { value == value }\n"
        )
        checked(
            "Rust correctness lint rejects self comparison",
            [
                "cargo",
                "+1.98.1",
                "clippy",
                "--offline",
                "--",
                "-A",
                "clippy::all",
                "-D",
                "clippy::correctness",
            ],
            False,
            "eq_op",
            cwd=work,
        )

    samples = []
    if args.kernel:
        provenance = json.loads((ROOT / "kernel-provenance.json").read_text())
        for relative, digest in provenance["files"].items():
            record(
                relative + " matches qualified kernel profile",
                hashlib.sha256((args.kernel / relative).read_bytes()).hexdigest() == digest,
            )
        for relative, language in [
            ("peios/runner.py", "python"),
            ("peios/generate-keys.py", "python"),
            ("peios/build.sh", "shell"),
            ("peios/verify-config.sh", "shell"),
            ("peios/kernel.bzl", "starlark"),
            ("peios/BUILD.bazel", "starlark"),
        ]:
            source = args.kernel / relative
            before = source.read_bytes()
            output = format_code(language, before.decode())
            record(relative + " formatter idempotent", format_code(language, output) == output)
            record(relative + " source untouched", source.read_bytes() == before)
            samples.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(before).hexdigest(),
                    "formatting_would_change": output.encode() != before,
                }
            )

    report = {
        "runtimes": versions,
        "tools": tools,
        "checks": results,
        "samples": samples,
        "manual_checks": [
            "C multiline conditions, 100-column brace eligibility and full-chain brace consistency",
            "Soft function-size/nesting thresholds and meaningful naming",
            "Side-effect-sensitive import ordering and contract preservation",
        ],
        "passed": all(result["passed"] for result in results),
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/qualification.json").write_text(json.dumps(report, indent=4) + "\n")
    failed = [result for result in results if not result["passed"]]
    for result in failed:
        print(result["name"], result["detail"])
    print(
        f"{len(results) - len(failed)}/{len(results)} checks passed; {len(samples)} source samples untouched."
    )
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
