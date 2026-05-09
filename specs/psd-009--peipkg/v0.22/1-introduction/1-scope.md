---
title: Scope
---

This specification defines peipkg, the package format and
repository protocol for the Peios operating system. peipkg is
the binary distribution primitive -- the unit of build,
distribution, and trust for software shipped to a Peios system.

peipkg is intentionally narrow in scope. It defines how binaries
reach a system; it does not define how those binaries are
integrated into services, applications, roles, or features.
Higher-level concepts (roles, role features, core features, CLI
applets, GUI applets) reference packages but are specified
separately. A package is an implementation detail beneath these
user-facing primitives.

This specification covers:

- The on-wire package format -- container, internal layout,
  manifest schema
- Package identity -- naming, versioning, architecture
- Dependency expression and resolution semantics
- Declarative side-effect mechanisms for standard Linux
  maintenance operations (ldconfig, depmod, man-db)
- Per-file and per-package integrity
- Package signing -- algorithms, envelope, verification
- Repository protocol -- descriptor, active and archive
  indexes, URL conventions
- Repository trust model -- signing policy, custom repositories
- Package manager semantics -- install, upgrade, uninstall,
  transactions, rollback

This specification does not cover:

- Roles, role features, or core features (separate subsystems,
  to be specified)
- CLI applets and GUI applets (separate subsystem, to be
  specified)
- Integration metadata that higher-level artifacts attach to
  packages -- peinit service descriptors, KACS security
  descriptors, LCS registry seeds, reconciller manifests --
  these belong to the artifacts that compose packages, not to
  packages themselves
- The build infrastructure that produces packages
  (operational; see appendix A for guidance)
- KACS security descriptors and xattrs applied to installed
  files -- PSD-004
- LCS registry interactions during install -- PSD-005
- peinit lifecycle integration of installed services -- PSD-007
