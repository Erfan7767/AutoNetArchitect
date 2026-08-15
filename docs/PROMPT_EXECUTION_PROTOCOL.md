# Prompt Execution Protocol

## Purpose
This protocol governs delivery of each phase. A phase prompt must identify its objective, files, contracts, dependencies, constraints, acceptance criteria, and validation commands.

## Output contract
The agent must return complete files and must not use incomplete implementation markers or ellipses. Every Python file includes type hints and docstrings. Models and their tests remain in one sub-prompt.

## Validation
After generation, run syntax compilation, import-graph checks, signature checks, unit tests, and a diff review. Do not advance until validation is green or the known issue is explicitly recorded.

## Recovery
For token overflow, reduce the file set while preserving model-test pairs. For incomplete output, regenerate the complete file rather than accepting fragments. For failures, classify the error and apply the matching correction strategy.
