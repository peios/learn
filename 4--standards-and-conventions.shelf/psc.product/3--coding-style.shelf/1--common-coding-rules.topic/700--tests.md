---
title: Tests
type: reference
description: Test behavior, regressions, repeatability, and useful failure
  details.
---

Prefer tests of observable behavior over tests of incidental implementation
steps. For example, check that saving and reopening a document preserves its
contents rather than requiring the save function to call particular helpers.
Internal restructuring that preserves the required behavior should not break
otherwise valid tests.

Test internal details when those details are themselves part of a real
requirement. This preference does not restrict tests to public APIs or prevent
focused tests of internal components.

## Regression tests

Strongly prefer adding a regression test when fixing a bug: a test that
catches the faulty behavior and passes with the fix. For example, a fix for a
crash on an empty filename should normally include a test of that case.

Allow justified exceptions when a useful automated test is impractical. Record
why the test was omitted and how the fix was checked in the associated work's
validation record.

## Independence and repeatability

Prefer tests that work independently and give repeatable results. Do not rely
on another test leaving files or other state behind. Control inputs such as
time, randomness, and external services where practical, and clean up
resources owned by the test.

Tests that genuinely require a network, special hardware, or randomness should
make those requirements explicit and provide enough information to investigate
failures. For example, report the seed or failing input for a randomized test
when that helps reproduce the failure.

## Names and failure details

Use descriptive test names or case descriptions that explain the behavior
being checked. For example, `empty_filename_returns_error` is more useful than
`test_7`.

Make failures informative, including relevant expected and actual values where
appropriate. Use the test framework's existing diagnostics; do not add
messages that merely repeat information it already reports.
