---
title: peipkg-manager CLI
type: reference
description: Flags and modes for peipkg-manager, the long-lived build farm coordinator.
related:
  - peios-packages/getting-started/set-up-a-build-farm
  - peios-packages/running-a-farm/configuration
---

`peipkg-manager` is the long-lived build farm daemon. It reads its configuration from a single TOML file and shells out to `peipkg-build` and `peipkg-repo` (which must be on `PATH`) to do the actual format work.

## Invocation

```
peipkg-manager [flags]
```

Two modes, selected via `--once`:

- **Daemon mode** (default): runs forever, polls upstreams on a schedule, listens for webhooks if `[http].addr` is set, exits on SIGTERM/SIGINT.
- **One-shot mode** (`--once`): polls every recipe once in parallel, processes triggers, exits. For cron, CI, or manual rebuilds.

## Flags

| Flag | Default | Description |
|---|---|---|
| `--config PATH` | `/etc/peipkg-manager/config.toml` | Path to `peipkg-config.toml`. |
| `--log-level LEVEL` | `info` | One of `debug`, `info`, `warn`, `error`. |
| `--once` | `false` | Run a single sweep and exit. No webhooks, no scheduler. |

There is no `-h` or `--help` beyond the flag listing standard `flag.PrintDefaults` produces.

## Daemon mode

The default. Loads recipes, initialises the repository if needed, starts per-recipe poll goroutines, optionally starts the HTTP server, and then drains the trigger channel forever.

Operator interactions:

- **`SIGTERM` / `SIGINT`** — clean shutdown. Drains the in-flight build (if any), then exits zero.
- **`SIGHUP`** — reload recipes from `recipes_dir`. The daemon picks up new recipes and dropped ones; in-progress builds finish.
- **`/healthz`** — HTTP endpoint returning `200 ok`. For readiness probes.
- **`/status`** — HTTP endpoint returning JSON status. See [Monitoring](../running-a-farm/monitoring).

## One-shot mode

```
peipkg-manager --once --config /etc/peipkg-manager/config.toml
```

What it does:

1. Initialises the repository if it doesn't exist.
2. Polls every recipe with `[upstream]` configured, in parallel.
3. Drains triggers as they arrive: dedupe against the archive, build, publish.
4. Exits zero when all polls have completed and the trigger channel has drained.

What it doesn't do:

- No HTTP server, no webhook receiver.
- No periodic ticker; one poll per recipe per invocation.
- No background processing — when the function returns, all the work for this invocation is done.

### When to use one-shot mode

| Use case | Notes |
|---|---|
| Cron-driven setups | `*/30 * * * * peipkg-manager --once --config /etc/peipkg-manager/config.toml`. |
| GitHub Actions on the recipes repo | Run on every push to recipes repo's main branch; the action invokes `peipkg-manager --once`. |
| Manual operator-driven rebuilds | `peipkg-manager --once` then watch `/var/lib/peipkg-manager/repo/` for the result. |
| Testing | Easier to assert against than the daemon (no cancellation timing dance). |

For continuous operation with low-latency response to webhooks, daemon mode is the right choice. One-shot mode is the option for "I don't want a daemon running."

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Clean exit (daemon: SIGTERM received and drain succeeded; one-shot: completed successfully). |
| `1` | Runtime error: failed to load config, failed to load recipes, missing dependency binary on PATH, signing key unreadable, etc. |
| `2` | Flag parsing error or invalid config schema. |

Build/publish failures within the daemon are *not* propagated as exit codes — they're logged and the daemon keeps running. The expected operator pattern is to alert on log entries (`level=error msg="build failed"`) or on `failures` map size in `/status`.

## Environment

`peipkg-manager` itself doesn't read environment variables (configuration is via the TOML file). The `build.sh` scripts it invokes do — see [Build scripts](../authoring-recipes/build-scripts) for what the script gets.

## What `peipkg-manager` does NOT do

- **Sandbox builds.** Build scripts run as the manager's user. The host is trusted. If you need stronger isolation, run `peipkg-manager` inside a container or VM.
- **Multi-host coordination.** v0 is single-host. There's no work queue across multiple manager processes; running two against the same `state_dir` is undefined behaviour.
- **Multi-arch matrix builds.** A recipe builds whatever architecture its `[[package]]` stanzas declare. To produce x86_64 AND aarch64 outputs from one recipe, write the recipe with both arch stanzas (rare) or run separate manager instances per arch (typical).
- **HTTP-based control plane.** There's no REST API to "trigger a build" or "remove a recipe." Operations are driven by editing `recipes_dir` + sending SIGHUP, or by webhook events.

These limits are intentional v0 simplifications. If they bite you, that's a signal the workload has outgrown v0; the right fix is design conversation, not feature stuffing.
