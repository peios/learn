---
title: Informative Text
---

## Default

All text in a PSD is normative unless explicitly marked otherwise.

## Informative markers

Text MUST be marked as informative using one of the following:

- **Block quotes** with the `[!INFORMATIVE]` callout:

  ```markdown
  > [!INFORMATIVE]
  > This text provides context but does not define behavior.
  ```

- **Inline introduction** using "For example" or "Note:":

  ```markdown
  For example, a token with no groups would have an empty group list.

  Note: this behavior differs from the Windows implementation.
  ```

Informative text MUST NOT contain normative keywords (MUST, SHALL, etc.) used in their RFC 2119 sense. If an informative block needs to describe required behavior, it SHOULD refer to the normative clause that defines it.

## Clause numbering

Informative text MUST NOT receive clause numbers. Only normative statements are numbered (see §6.1).
