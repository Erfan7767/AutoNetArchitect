# Installation

## Runtime installation

Use Python 3.11 or newer in an isolated environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

The runtime manifest contains the dependencies needed by the V1 package. Development tooling is separated into `requirements-dev.txt`, optional rendering and analysis integrations remain in `requirements-optional.txt`, and documentation tooling is listed in `docs/requirements-docs.txt`.

## Development installation

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -e .
pre-commit install
```

The repository also supports `tox`, `nox`, and Make targets. These are convenience runners around the same declared dependency groups; they do not change application behavior.

## Container installation

The release container is built with:

```bash
docker build --tag autonetarchitect:0.1.0 .
docker run --rm autonetarchitect:0.1.0 autonet --help
```

The image runs as a non-root user and writes application state only to its declared state volume. Docker hardening is a baseline, not evidence that a target host or organization is production-ready.
