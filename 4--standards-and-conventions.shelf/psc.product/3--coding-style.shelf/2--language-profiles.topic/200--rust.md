---
title: Rust
type: reference
description: Peios coding conventions for Rust.
---

Use four spaces, a 100-column formatter target, `snake_case`
functions/modules, `PascalCase` types, and `SCREAMING_SNAKE_CASE` constants.
Follow `rustfmt` for mechanical layout. Use the edition and formatter
version selected by the project. Required Rust braces remain required; a short
early return can be expanded by the formatter.

Apply the ownership and error rules using ordinary Rust mechanisms: `Option`
for absence, `Result` for expected failures, and ownership/`Drop` for resource
lifetimes. Use `mut` where mutation is needed and keep visibility narrow. An
`unsafe` block needs the safety explanation required by the common guide,
including assumptions maintained outside the block.

Reference: [Rust style guide](https://doc.rust-lang.org/style-guide/).
