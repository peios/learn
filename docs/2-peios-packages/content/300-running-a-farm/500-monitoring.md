---
title: Monitoring
type: how-to
description: What peipkg-manager exposes through logs and the /status endpoint, and what to alert on.
related:
  - peios-packages/running-a-farm/configuration
---

`peipkg-manager` exposes its state two ways: structured logs to systemd's journal and a JSON `/status` endpoint over HTTP. Both are read-only — they don't modify daemon behaviour, so it's safe to scrape `/status` on a tight cadence.

## Logs

Run `journalctl -u peipkg-manager` to see what the daemon is doing. The output is structured (`level=`, `key=value` pairs) so it's easy to grep or feed into a structured log shipper.

Notable log events:

| Event | Severity | Meaning |
|---|---|---|
| `recipe roster loaded` | info | Startup; lists recipe count. |
| `peipkg-manager starting` | info | Startup; lists farm_id and mode (`daemon` or `once`). |
| `polling upstream` | info | A poll cycle started for one recipe. |
| `poll complete` | info | A poll cycle finished; reports `tags_seen` and `matches_emitted`. |
| `webhook server listening` | info | HTTP server is up. |
| `webhook accepted, triggering immediate poll` | info | A webhook fired for a recipe; an immediate poll is in progress. |
| `webhook signature invalid` | warn | An incoming webhook had a bad HMAC. Not necessarily an attack — could be a misconfigured webhook secret. |
| `starting build` | info | Build kicked off. |
| `build + publish complete` | info | Success. |
| `build failed` | error | Build failed; `next_retry_after` indicates the backoff. |
| `publish failed` | error | Build succeeded but publishing the index failed. Outputs are retained for the next attempt. |
| `dedup check failed` | warn | The archive index couldn't be read; the build proceeds anyway. Usually means the archive doesn't exist yet (first-run) or is malformed. |
| `clear staging dir failed` | warn | Cleanup after a successful publish hit an error. Doesn't affect the published state. |
| `manager.Run returned non-cancel error` | error | Daemon exited unexpectedly. Investigate. |

Logs are the canonical history. `/status` is a snapshot.

## The `/status` endpoint

When `[http].addr` is set, the daemon serves a JSON status report at `<addr>/status`. The response is a single JSON object — not streamed, not paginated.

Example:

```bash
$ curl -s http://localhost:8080/status | jq
```

```json
{
  "farm_id": "peios-build-1",
  "recipes": ["libfoo", "libz", "musl", "nginx"],
  "builds_attempted": 47,
  "builds_succeeded": 45,
  "in_flight": {
    "recipe": "nginx",
    "version": "1.27.0-1",
    "started_at": "2026-05-07T14:32:11Z"
  },
  "failures": {
    "musl@1.2.5-1": {
      "failures": 2,
      "next_retry": "2026-05-07T14:47:11Z"
    }
  }
}
```

### Field reference

| Field | Type | Meaning |
|---|---|---|
| `farm_id` | string | The farm's identifier from `[manager].id`. |
| `recipes` | string array | Names of all loaded recipes, in the order they appear in `recipes_dir`. |
| `builds_attempted` | integer | Total builds the daemon has started since process start. |
| `builds_succeeded` | integer | Total builds that completed all the way through publish. |
| `in_flight` | object or null | The build currently running, if any. Null when idle. |
| `in_flight.recipe` | string | The recipe ID. |
| `in_flight.version` | string | The package version being built. |
| `in_flight.started_at` | RFC 3339 string | When the build started. |
| `failures` | object or null | Map keyed by `<recipe>@<version>` of currently-backed-off builds. Null/absent when no failures. |
| `failures[k].failures` | integer | How many consecutive times this build has failed. |
| `failures[k].next_retry` | RFC 3339 string | The next time the daemon will retry this build. |

State is in-memory; restarting the daemon resets all counters and clears the failure map.

## What to alert on

For a production farm, useful alerts:

| Condition | Severity | Why |
|---|---|---|
| Daemon down (no response from `/healthz`) | page | Daemon process died or host is down. |
| Builds-attempted counter not increasing for > 24h | warning | Either no upstreams have new tags (normal for stable repos) or the daemon's poller is stuck. Check logs. |
| `failures` map non-empty for > 1h | warning | A build is persistently failing. Look at the recipe and the recent build logs. |
| Same in-flight build for > 1h | warning | Build is stuck (network issue cloning, runaway compilation). |
| Disk usage on `state_dir` partition > 80% | warning | Source caches and stage dirs are filling up; usually means a build is leaking. |
| Disk usage on web root partition > 80% | warning | Published repo is growing (normal trend); plan capacity. |

The HTTP server is plain HTTP. Put it behind a reverse proxy if you want TLS, auth on `/status`, or rate limiting. The webhook endpoint typically doesn't need to be reachable from arbitrary networks — point upstream's webhook at a tunnelled or internal address.

## Surfacing build failures to operators

A failing build is easy to miss in the logs. Two common patterns:

1. **Periodic `/status` scrape** into your monitoring system (Prometheus, Grafana, etc.). Map `failures` to a counter; alert when nonzero.
2. **Log shipper with alerting** on `level=error msg="build failed"`. Most log aggregators (Loki, Elasticsearch, Datadog) support this directly.

Neither is built into `peipkg-manager`. v0 deliberately keeps the surface narrow — observability is the operator's choice of tools.
