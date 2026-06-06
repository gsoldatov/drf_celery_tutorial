---
name: python-coding-style
description: Provides general instructions on how to write Python code. Use when writing or modifying Python code.
---

The rules from the following list should apply to any Python code written, unless user instructs to do otherwise:
- stick to PEP8;
- use type hints for code you add or update;
- use the newer features of Python when appropriate, if Python version is specified (e.g. use `list[str] | list[int]` instead of `Union[List[str], List[int]]`)
- add docstrings and comments to functions & methods, but keep them short:
    - docstrings should contain:
        - basic description of the function;
        - important non-obvious information about function parameters;
        - parameters & return value descriptions should be kept as short as possible;
    - comments should be added only:
        - to explain complex code parts;
        - to explain business rules and edge cases, which are not obvious from the scope of the function;
- use double quotes for for single or multiline strings by default (literals containing double quotes may be wrapped into single-quotted strings);
