---
title: Version Resolution
---

When a specification references another PSD by number without an explicit version, the applicable version MUST be resolved as follows:

The resolved version is the highest version of the referenced PSD whose version number is less than or equal to the version of the referencing document, using SemVer ordering.

> [!INFORMATIVE]
> Example: PSD-010 at v0.25 references PSD-004. PSD-004 has versions v0.20 and v0.22. The resolved version is PSD-004 at v0.22 (highest ≤ v0.25). If PSD-004 only has v0.20, it resolves to v0.20.

Only `final` versions participate in version resolution. A `draft` version MUST NOT be selected by the resolution rule. A `withdrawn` version MUST NOT be selected by the resolution rule.

If no `final` version of the referenced PSD exists at or below the referencing version, the reference is unresolvable. This SHOULD be treated as an error during cross-reference validation.

## Explicit version pinning

A reference MAY include an explicit version to override the resolution rule:

```
PSD-004 v0.22 §3.2(1)
```

Explicit version pinning SHOULD only be used when citing historical behavior that has since changed.

> [!INFORMATIVE]
> Example: "This field was removed in v0.25; see PSD-004 v0.22 §3.2(1) for the original definition."
