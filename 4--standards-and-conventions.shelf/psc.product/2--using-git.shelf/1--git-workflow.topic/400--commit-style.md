---
title: Commit Style
type: reference
description: Commit subjects, scopes, task references, and breaking-change
  footers.
---

Use [Conventional Commits
1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) for Peios-authored
commits across Panorama, the kernel fork, and satellite repositories:

```text
<type>(<scope>): <imperative summary>

Optional explanation of the problem, resulting behavior, and significant
reasoning. Describe relevant validation and remaining limitations.

Refs: PEI-1234
```

Each commit should contain one coherent change, independently reviewable and
revertible where practical. Separate unrelated fixes, formatting, and
generated changes. A series can contain dependent commits when that makes the
work easier to review.

Use a concise, imperative subject: "preserve module paths", rather than
"updated packaging". Aim for 72 characters without sacrificing clarity. Use
these lowercase types:

| Type | Purpose |
| --- | --- |
| `feat` | Add functionality. |
| `fix` | Correct faulty behavior. |
| `refactor` | Restructure code without changing its behavior. |
| `perf` | Improve performance. |
| `docs` | Change documentation. |
| `test` | Add or change tests. |
| `build` | Change build tooling, dependencies, or packaging. |
| `ci` | Change continuous integration configuration or automation. |
| `chore` | Other maintenance that does not fit the types above. |
| `revert` | Revert an earlier change; identify the reverted commit in the body. |

Choose a meaningful scope. In Panorama, normally use the component. In a
dedicated repository, use the subsystem or area, such as `kacs`, `stratafs`,
or `packaging`. Omit the scope when no single scope meaningfully describes the
change. Commit types do not expand the types in
[Work Branches](~psc/work-branches).

Include a body when explanation matters. Describe the problem, resulting
behavior, and significant reasoning rather than repeating the diff. Small,
obvious changes do not need boilerplate. Validation statements must describe
what was actually checked and any relevant limitations.

Put related Acta task IDs in a `Refs:` footer, separated from the body by a
blank line. Do not append task IDs to the subject. For several tasks, use a
comma-separated list, for example `Refs: PEI-1234, PEI-1235`. A reference
records the association; it does not assert that the task is complete.
Work-branch names continue to include their Acta task number.

For a breaking change, append `!` before the subject's colon, for example
`feat(authd)!: require an explicit token audience`. Include a
`BREAKING CHANGE:` footer explaining the affected contract and how callers
or users should migrate.

Imported upstream commits and merge commits are exempt from subject-format
enforcement. Preserve upstream history and the integration ancestry required
by the branch model; do not rewrite existing history merely to adopt this
style.

Commit types can inform release notes, but package versions remain explicit
release decisions. Do not automatically bump every package touched by a
commit.
