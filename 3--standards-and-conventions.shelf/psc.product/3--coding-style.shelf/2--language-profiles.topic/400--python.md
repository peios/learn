---
title: Python
type: reference
description: Peios coding conventions for Python.
---

Use four spaces and the shared naming conventions. Retain the Peios 100-column
target rather than adopting PEP 8's shorter line recommendation. Use
docstrings for the public interfaces and non-obvious contracts covered by the
common rule.

Give ordinary functions in maintained Python code type hints for parameters
and return values, including functions in maintained scripts. Allow justified
exceptions, and omit redundant annotations such as the usual `self` parameter.
For example, `def load_config(path: Path) -> Config` makes the interface
clear.

Type hints support readers and automatic checking; they do not validate
incoming data at runtime. The validation-boundary rules still apply.

Use context managers for scoped resource cleanup where appropriate. Use the
language's explicit absence value, `None`, without conflating it with valid
values such as zero or an empty collection.

References: [PEP 8](https://peps.python.org/pep-0008/) and [Python typing
guidance](https://typing.python.org/en/latest/guides/libraries.html).
