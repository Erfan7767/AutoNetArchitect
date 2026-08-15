# Dependency Policy

The root foundation layer is independent of higher product layers. Optional integrations must use `utils.dependency_utils.optional_import` or an equivalent explicit fallback. Missing optional dependencies must degrade safely and must not silently create a false production-ready state.

The canonical schema version and project constants live in root `constants.py`. Services may consume these constants but must not duplicate them. Sensitive values are redacted before logging, and cryptographic failures fail closed.
