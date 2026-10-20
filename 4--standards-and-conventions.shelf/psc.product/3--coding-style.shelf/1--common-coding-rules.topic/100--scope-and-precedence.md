---
title: Scope and Precedence
type: reference
description: How common rules, language conventions, and repository exceptions
  interact.
---

This is the consolidated working draft developed with Jack under PEI-1506. It
records the agreed policies and applies them to the language profiles. An
unanswered proposal is not a rule. Requirements, preferences, and soft review
thresholds retain their stated strength; a formatter must not silently turn a
preference into a mandatory rule.

The [style tooling guide](~psc/style-tooling) explains the available
configurations and checks. These tools implement the policies; they do not
replace them. The kernel exception guide,
`kernel/peios/CODING_STYLE.md`, defines the scope of the kernel's deviations.
Git workflow and commit rules remain in [Using Git](~psc/development-model).

## Shared defaults and language conventions

Use the Peios default when a language's community has several reasonable
conventions. A merely popular preference does not override the Peios baseline.

Follow a language convention when it is strongly established across the
ecosystem. Jack's comparison of roughly 60% versus 90% adoption describes the
strength of consensus intended, not measured thresholds or a requirement to
invent adoption statistics.

Assess that strength using language guidance, standard tooling, and
established practice together. A configurable formatter's default or one
organization's styleguide alone does not establish an ecosystem-wide
convention. Record the reason for each language-specific departure from the
shared default; discuss unclear cases before adopting an exception.

## Rule organization

Keep common rules and per-language rules in the central Peios styleguide.
Repository-specific guides describe explicit, scoped deviations from that
baseline. A repository exception should identify the rule it overrides, the
files or language it covers, and its rationale.

Apply language syntax and required external contracts first, then explicit
repository exceptions for their stated scope, then language-specific rules,
then common defaults. An exception overrides only the rules it identifies; it
does not discard the rest of the guide. Bring unresolved conflicts back for
discussion instead of inferring an exemption.

The kernel has its own exception guide. Its kernel C conventions do not apply
to Peios-only Python scripts or Bazel files because they share a repository.
