---
title: Main and Component Branches
type: reference
description: How main and component version branches define development
  baselines.
---

In Panorama, `main` represents the consolidated source for the latest
qualified monthly OS release. Development for future component versions
happens on branches named `<component>/<version>`, such as `authd/0.8.0`.

A component's first development branch starts from the current `main`. When a
component version is released, its next development branch starts from the
exact released commit. For example, after tagging `authd/v0.8.0`, create
`authd/0.9.0` from that tag. Development can continue before the next monthly
includes 0.8.0.

Component versions use a semver-like `<MAJOR>.<MINOR>.<PATCH>` scheme.
Components do not have to share a version number or release on the monthly OS
schedule.
