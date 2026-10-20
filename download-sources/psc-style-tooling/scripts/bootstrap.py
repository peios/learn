"""Install locked development tools locally; never modify project source."""

import hashlib
import io
import json
import platform
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(arguments: list[str]) -> str:
    """Run a required command and return its standard output."""
    return subprocess.check_output(arguments, cwd=ROOT, text=True).strip()


def verify_runtimes() -> dict[str, str]:
    """Reject runtime drift instead of silently qualifying different versions."""
    expected = json.loads((ROOT / "runtimes.lock.json").read_text())
    actual = {
        "platform": sys.platform,
        "machine": platform.machine(),
        "python": platform.python_version(),
        "node": run(["node", "--version"]),
        "npm": run(["npm", "--version"]),
        "go": run(["go", "version"]),
        "rustc": run(["rustc", "+" + expected["rust_toolchain"], "--version"]),
        "rustfmt": run(["rustfmt", "+" + expected["rust_toolchain"], "--version"]),
        "kernel_rustfmt": run(["rustfmt", "+" + expected["kernel_rust_toolchain"], "--version"]),
    }
    for name, value in actual.items():
        if value != expected[name]:
            raise RuntimeError(f"{name}: expected {expected[name]!r}; found {value!r}")
    return expected


def verify_tools() -> dict[str, str]:
    """Check installed package versions and downloaded executable hashes."""
    python_pins = {}
    for line in (ROOT / "requirements.lock").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split()[0].split("==")
        python_pins[name] = version
    actual = json.loads(
        run(
            [
                str(ROOT / ".venv/bin/python"),
                "-c",
                "import importlib.metadata,json,sys; print(json.dumps({n: importlib.metadata.version(n) for n in sys.argv[1:]}))",
                *python_pins,
            ]
        )
    )
    if actual != python_pins:
        raise RuntimeError("Installed Python packages differ from requirements.lock")
    node_pins = json.loads((ROOT / "package.json").read_text())["devDependencies"]
    for name, version in node_pins.items():
        installed = json.loads((ROOT / "node_modules" / name / "package.json").read_text())
        if installed["version"] != version:
            raise RuntimeError(f"Installed {name} differs from package.json")
    binaries = json.loads((ROOT / "binary-tools.lock.json").read_text())
    for name, entry in binaries.items():
        if (
            hashlib.sha256((ROOT / ".bin" / name).read_bytes()).hexdigest()
            != entry["binary_sha256"]
        ):
            raise RuntimeError(f"Installed {name} executable differs from its lock")
    return {
        **python_pins,
        **node_pins,
        **{name: item["version"] for name, item in binaries.items()},
    }


def main() -> None:
    """Install hash-locked packages and release binaries inside this bundle."""
    verify_runtimes()
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--require-hashes",
            "--only-binary=:all:",
            "--cache-dir",
            str(cache / "pip"),
            "-r",
            str(ROOT / "requirements.lock"),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--cache", str(cache / "npm")],
        cwd=ROOT,
        check=True,
    )
    destination = ROOT / ".bin"
    destination.mkdir(exist_ok=True)
    for name, entry in json.loads((ROOT / "binary-tools.lock.json").read_text()).items():
        target = destination / name
        if (
            target.exists()
            and hashlib.sha256(target.read_bytes()).hexdigest() == entry["binary_sha256"]
        ):
            continue
        request = urllib.request.Request(
            entry["url"], headers={"User-Agent": "Peios-style-tooling"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            artifact = response.read()
        if hashlib.sha256(artifact).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Artifact hash mismatch for {name}")
        if entry["member"]:
            with tarfile.open(fileobj=io.BytesIO(artifact), mode="r:gz") as archive:
                member = archive.extractfile(entry["member"])
                if member is None:
                    raise RuntimeError(f"Missing executable in {name} archive")
                binary = member.read()
        else:
            binary = artifact
        if hashlib.sha256(binary).hexdigest() != entry["binary_sha256"]:
            raise RuntimeError(f"Executable hash mismatch for {name}")
        temporary = target.with_suffix(".download")
        temporary.write_bytes(binary)
        temporary.chmod(0o755)
        temporary.replace(target)
    verify_tools()
    print("Locked tooling installed. Run: python3 scripts/qualify.py")


if __name__ == "__main__":
    main()
