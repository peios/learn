---
title: Submitting a Job
description: The definition a submitter sends — every field, its default and its validation — what the manager does with it, and when and with what the submit is answered.
---

A `submit` carries the whole definition of the job in the request
object. There is no persistent definition, no name, and no policy: a
submitted job runs once, as described, and is then gone.

## The definition

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `image_path` | string | yes | — | The program to execute. An absolute path. |
| `arguments` | array of strings | no | `[]` | Its arguments, after the program name. |
| `environment` | object of string → string | no | `{}` | Variables to set. §7.6 below. |
| `working_directory` | string | no | `/` | The working directory. An absolute path. |
| `description` | string | no | `""` | A human-readable label, for views and records. |
| `timeout` | integer | no | `0` | Seconds the job may run before it is stopped. `0` is no limit. |
| `stop_timeout` | integer | no | §7.A | Seconds between the termination signal and the kill. |
| `readiness` | string | no | `none` | `none`, or `notify` to wait for `READY=1`. |
| `readiness_timeout` | integer | no | §7.A | Seconds a `notify` job has to become ready. |
| `success_exit_codes` | array of integers | no | `[]` | Non-zero exit codes that count as success. |
| `descriptors` | array of strings | no | `[]` | Names for the descriptors to inject. §7.9 |
| `output` | bool | no | `false` | Whether the last attached descriptor is an output sink. §7.9 |
| `security_descriptor` | string | no | §7.8 | The job's descriptor, in SDDL. §7.8 |

Nothing here restarts, depends, probes, or schedules. A program that
needs a restart policy, dependencies, a health check or a trigger is a
service, and its definition belongs in the registry (§4.1). The
manager MUST NOT accept a policy field on a `submit`, and MUST NOT add
one (§7.11).

### Validation

The manager MUST answer `INVALID_ARGUMENTS`, creating nothing, when:

- `image_path` is absent, not a string, empty, not absolute, or
  contains a NUL byte;
- `working_directory` is present and not an absolute string, or
  contains a NUL byte;
- any element of `arguments` is not a string or contains a NUL byte;
- any key of `environment` is empty, contains `=`, or contains a NUL
  byte; or any value contains a NUL byte;
- any of `timeout`, `stop_timeout`, `readiness_timeout` is present and
  not a non-negative integer, or `stop_timeout` is `0`;
- `readiness` is present and not one of the two values;
- any element of `success_exit_codes` is not an integer in 0–255;
- `descriptors` does not match the attached descriptors (§7.9);
- `security_descriptor` is present and is not a valid descriptor with
  an owner and a DACL (§7.8);
- the total size of the resulting `argv` and environment exceeds what
  the manager can pass to `execve`.

The manager MUST NOT validate that `image_path` exists or is
executable. That is decided at `execve`, by the job's own token
against the file's descriptor, and a job whose program cannot be run
becomes a failed job (§7.7) rather than a refused submission. Checking
in advance would either check with the wrong identity or duplicate the
kernel's decision.

### The environment

The manager MUST build the job's environment as it builds a service's,
with `environment` in the place a service definition's own variables
occupy: above any manager-wide layer an administrator configures, and
below the protocol variables the manager sets last. A submitter MUST
NOT be able to override `NOTIFY_SOCKET`, `LISTEN_FDS`,
`LISTEN_FDNAMES` or `LISTEN_PID`.

The manager sets no `HOME`, `USER`, `LOGNAME` or `SHELL` — it knows
nothing about the job identity beyond its token, and a submitter that
knows the principal's home directory supplies it. A submitter that
originated a logon has these from the logon's profile (PGSS §2.9).

## What the manager does

On an accepted `submit` the manager MUST, in order:

1. Establish the job identity (§7.5) and refuse with `BAD_TOKEN` if
   it cannot.
2. Check the submitter's quota and refuse with `QUOTA_EXCEEDED` if the
   job would exceed it.
3. Create the job record, with its identifier, in the `created` state,
   owned by the submitter with the descriptor of §7.8.
4. Start the process — install the identity, set up its streams,
   inject descriptors, execute — as it starts a service's main process.
5. Answer the `submit`.

Steps 1 and 2 MUST both precede step 3: a refused submission MUST
leave no record, emit no lifecycle event, and consume no quota.

## When the submit is answered

The manager MUST answer a `submit` when the job has **left the
`created` state**: when the process has confirmed a successful
`execve`, or when starting it has failed.

It MUST NOT answer earlier. A submitter holding a response holds a job
that either exists as a running process or has definitively failed to
— never one whose fate is still being decided in the setup between
fork and exec.

It MUST NOT answer later. In particular a `readiness: notify` job is
answered when it is running, not when it is ready; a submitter that
wants to block until readiness follows with a `wait` (§7.8).

## The response

The response is the job view (§7.7).

If the job is `running`, the response MUST carry the job's process
handle — a pidfd referring to the job's main process — as an attached
descriptor. The handle lets the submitter observe the process's exit
with `poll` or `waitid`, and signal it, with no further protocol; the
kernel applies its ordinary process access rules to whatever the
submitter does with it. A submitter that declined to receive ancillary
data simply does not get the handle (§7.4).

If the job is `failed`, the response carries no descriptor, and the
view's `cause` says why (§7.7). The submission itself succeeded — a
job was created, recorded and reported — so the response is
`"status": "ok"`. Only a submission the manager refused outright, at
steps 1–3, is an error response.

> [!NOTE]
> A submitter that needs the process handle as a *child* would have
> — to `waitpid` on it, or to be its parent for `PR_SET_PDEATHSIG` —
> does not get that, because the job is the manager's child, not the
> submitter's. Exit status reaches the submitter through the job view,
> through `wait`, or through the manager's event stream; the pidfd is
> for polling, signalling, and passing to something else.
