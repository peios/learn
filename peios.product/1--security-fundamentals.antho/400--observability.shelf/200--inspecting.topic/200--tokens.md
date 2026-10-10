---
title: Inspecting tokens
type: how-to
description: Select the right token, read its identity and security fields with token, and distinguish what the report proves from what needs object policy or historical evidence.
related:
  - peios/system-and-processes/token
  - peios/access-decisions/debugging-a-denial
  - peios/inspecting/overview
  - peios/inspecting/sessions
  - peios/inspecting/processes
  - peios/tokens/overview
  - peios/sdk-tokens/query
---

Use the read-only forms of [`token`](~peios/system-and-processes/token) to learn
who a process acts as and what identity, privileges and restrictions its token
carries. Choose the target first: the inspection tool's token, a process's
primary token and a thread's impersonation token can describe different callers.

A report is current state, not a record of an earlier failure and not a list of
everything that caller may access. For a denial, keep the object and requested
operation alongside it; follow [Debugging a denial](~peios/access-decisions/debugging-a-denial).

## Reading from the shell

Start with a summary, then request only the detail needed:

```console
token
token show --all
token show --pid PID --all
token groups --pid PID
token privs --pid PID
token stats --pid PID
```

The first two inspect the token running the command. `--pid PID` selects the
identified process's **primary token**. Use [Task Manager](~peios/threads-and-processes/task-manager)
to find and check the process rather than guessing its PID.

For impersonation, the command documents `--tid TID` together with `--pid PID`:

```console
token show --pid PID --tid TID --all
```

The failing thread's **effective token** is its impersonation token while
impersonating, otherwise the primary token. A primary-token report cannot stand
in for an impersonated client's identity. If the thread has exited or reverted,
keep that limitation with the result. Do not assume a query made later
reconstructs the token used earlier.

The other documented selectors are `--self` (the default), `--real` (your primary
token specifically), and `--peer SOCK_FD` (a connected socket's captured peer
identity). A peer token is the identity conveyed on that connection, not a
general lookup of another process. See [Choosing which token](~peios/system-and-processes/token#choosing-which-token).

`--raw` prints raw SIDs, `--label` uses labels where known, and `--json` requests
structured output. Preserve the selector, timestamp and any error with a saved
report. The command also has mutating subcommands; adjusting, duplicating,
restricting or impersonating a token is not part of read-only inspection.

## Read the fields as evidence

| Field or question | Read with | What to check |
|---|---|---|
| Principal | `token user` | The user SID; a displayed name is a label for that identity. |
| Groups | `token groups` | Group SIDs and attributes. Enabled groups can match allows; deny-only groups match denies. |
| Privileges | `token privs` | Present and enabled are different. A disabled privilege cannot contribute, and presence alone does not bypass other policy. |
| Integrity | `token integrity` | The token's level; compare it with the object's label and mandatory policy when diagnosing MIC. |
| Logon context | `token logon`, `token stats` | Logon type, logon SID and session identity. The LogonSession ID is separate from interactive-environment scope. |
| Confinement capabilities | `token caps` | Which capabilities are present; combine them with the confinement identity from the fuller report and the object's rules. |
| Claims | `token claims` | User/device attributes available to conditional ACEs; the application may additionally supply per-call local claims. |
| Default owner, group and DACL | `token owner`, `token group`, `token default-dacl` | Defaults for objects created with this token, not the security descriptor of every existing object. |
| Origin and source | `token origin`, `token source` | The originating session of a derived token and information about what minted it. |
| Type, impersonation level, restrictions, elevation and mandatory policy | `token show --all` | The full set of supported query classes, interpreted with the limits below. |

Apply the same target selector to these field commands; without it they inspect
your own token. `token query CLASS` is the documented raw named-class JSON form
for tooling. The complete class numbers and payloads are maintained in the
[Kernel ABI](~peios/peios-kernel/kacs/kacs-abi#token-constants)
and [token query payload reference](~peios/peios-kernel/kacs/kacs-abi-notes#token-query-payloads),
rather than duplicated here.

`show --all` means every supported query class, not every internal token field.
The ABI notes explicitly list fields with no query class, including
`audit_policy`, `write_restricted` and `confinement_exempt`. Do not infer these
from their absence in a report.

## Patterns by use case

**Who was this thread acting as?** Use the process and thread identity supplied
by the failure report, inspect the relevant token, and distinguish its type from
its impersonation level. A primary token also carries an impersonation ceiling;
the level alone does not tell you that the thread is impersonating. For earlier
state, correlate the available audit record instead.

**Which session is this?** `token show` displays the LogonSession LUID as
`session_id`; the underlying statistics field is `auth_id`.
`interactivity_scope` is a separate interactive-environment scope. Use the logon
session ID with [`logonse show ID`](~peios/system-and-processes/logonse#logonse-show),
subject to the session view's access limits.

**Is this the elevated half of a token pair?** The elevation type can be Full,
Limited or Default. Full and Limited describe the two sides of a linked pair;
Default means the token is not part of one. This is evidence about the token,
not a recommendation to elevate it. The separate `token linked` command reports
a linked counterpart where accessible.

**Did the token change?** Token statistics include its ID and `modified_id`,
which changes on adjustment. Keep both when comparing observations. Several
queries are not an atomic snapshot, and replacing a thread's token is not the
same as adjusting the one you previously inspected.

**Would this token be allowed to access an object?** The token is only one input.
For a file, use the documented `sd check` rehearsal and its
[limits](~peios/access-decisions/debugging-a-denial#rehearse-a-file-check-within-its-limits).
For other objects or caller-specific inputs, use their supported diagnostic
path or ask the component owner to investigate.

## Limits and refused queries

- Reading another process's token needs `PROCESS_QUERY_INFORMATION`, PIP
  dominance and the token's own `TOKEN_QUERY` grant. A refusal does not tell you
  which of those checks failed. Protected processes can remain closed to an
  administrator.
- Self-access depends on the surface. The documented own-process `/proc`
  token path is query-only without those checks; a direct self-open API checks
  the token's descriptor and can be denied after that descriptor changes.
- A missing or exited target, a denied query and an invalid request are
  different results. Keep the tool's message; a failed query is not an empty
  token.
- Process-based inspection cannot enumerate tokens held only by descriptors.
  Current queries cannot recover a destroyed token or historical fields.
- Queries do not grant adjustment, installation, duplication or impersonation
  rights. The `used` privilege state is not a timestamped history of each use;
  use audit evidence for that question.

See [Token access rights](~peios/peios-kernel/kacs/tokens/access-rights) for the
per-surface checks and [Inspecting security state](~peios/inspecting/overview)
for related views.

## Obtaining a token fd

This is the tool-author boundary. Token pseudo-files are **handles**, not
human-readable text: `cat /proc/<pid>/token` is not an inspection command.
The process path selects the primary token and
`/proc/<pid>/task/<tid>/token` selects the thread's effective token; the
`/sys/kernel/security/kacs/self` surface also provides a token handle.

The SDK [opening reference](~peios/sdk-tokens/opening-and-creating-tokens) covers
self, process, thread and socket-peer token acquisition and error results.
The Kernel TRM [access-rights chapter](~peios/peios-kernel/kacs/tokens/access-rights)
documents the query-only `/proc` handles, fixed peer-token rights, descriptor
checks and cached handle rights. A handle with only `TOKEN_QUERY` cannot perform
operations requiring other token rights.

## KACS_IOC_QUERY

Operators use `token` to perform and decode queries. Tool authors should start
with the SDK [query reference](~peios/sdk-tokens/query) and
[two-call buffer protocol](~peios/sdk-conventions/the-two-call-buffer-protocol).
The SDK provides typed readers for common fields and the generic class reader
for the rest.

For a raw-ABI consumer, the preserved
[querying-a-token-handle explanation](~peios/peios-kernel/kacs/kacs-abi-notes#querying-a-token-handle)
covers `KACS_IOC_QUERY`, size probes, short buffers and the two-call sequence.
The generated [KACS ABI](~peios/peios-kernel/kacs/kacs-abi) holds the exact ioctl
number, argument layout and class constants; its
[ABI notes](~peios/peios-kernel/kacs/kacs-abi-notes#token-query-payloads)
define the returned bytes. There is no need to decode those bytes by hand to
follow this operator workflow.

## See also

- [token](~peios/system-and-processes/token): the complete command interface.
- [Debugging a denial](~peios/access-decisions/debugging-a-denial): caller,
  object, requested action and audit evidence together.
- [Tokens](~peios/tokens/overview): the identity model behind the fields.
- [Working with tokens](~peios/sdk-access-control/working-with-tokens): developer
  tasks using the SDK.
