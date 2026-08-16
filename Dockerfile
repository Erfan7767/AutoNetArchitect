# AutoNetArchitect V1 multi-stage release image.
# The runtime image exposes the local API boundary. Production network changes
# remain subject to application governance, approval, backup, verification, and rollback gates.

FROM python:3.14-slim AS builder

WORKDIR /build

# Build dependencies are confined to the builder image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Metadata and requirements are copied before application sources for layer reuse.
COPY pyproject.toml setup.py README.md LICENSE MANIFEST.in requirements.txt ./

# Build the complete installable source tree. The runtime stage copies only the
# application paths needed by the V1 API/UI/CLI boundaries and the non-packaged data.
COPY . .

ARG INSTALL_EXTRAS=""
RUN if [ -n "$INSTALL_EXTRAS" ]; then \
        python -m pip install --no-cache-dir --prefix=/install ".[${INSTALL_EXTRAS}]"; \
    else \
        python -m pip install --no-cache-dir --prefix=/install .; \
    fi

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AUTONET_API_ROOT=/var/lib/autonetarchitect \
    AUTONET_API_HOST=0.0.0.0 \
    AUTONET_API_PORT=8000

# Security: the application never runs as root.
RUN groupadd --system --gid 10001 autonet && \
    useradd --system --uid 10001 --gid 10001 --create-home --home-dir /home/autonet autonet

WORKDIR /app

# Runtime-only native dependency used by supported diagram/report paths.
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python dependencies and package metadata from the builder.
COPY --from=builder /install /usr/local

# Copy the V1 API/CLI source boundary and runtime data. Other source packages are
# installed by setuptools in /usr/local and are not duplicated into the image.
COPY --from=builder /build/api ./api
COPY --from=builder /build/auth ./auth
COPY --from=builder /build/audit ./audit
COPY --from=builder /build/orchestrators ./orchestrators
COPY --from=builder /build/persistence ./persistence
COPY --from=builder /build/source_of_truth ./source_of_truth
COPY --from=builder /build/secrets ./secrets
COPY --from=builder /build/config_generators ./config_generators
COPY --from=builder /build/documentation ./documentation
COPY --from=builder /build/reports ./reports
COPY --from=builder /build/diagrams ./diagrams
COPY --from=builder /build/cli ./cli
COPY --from=builder /build/ui ./ui
COPY --from=builder /build/autonetarchitect ./autonetarchitect
COPY --from=builder /build/data ./data
COPY --from=builder /build/constants.py ./constants.py
COPY --from=builder /build/exceptions.py ./exceptions.py
COPY --from=builder /build/schema_version.py ./schema_version.py

# Local state is kept in a declared volume and application-owned directories are
# writable only by the non-root runtime user.
RUN mkdir -p /app/projects /app/logs /app/cache /app/backups /app/exports /app/reports /var/lib/autonetarchitect \
    && chown -R autonet:autonet /app /var/lib/autonetarchitect

USER autonet

VOLUME ["/var/lib/autonetarchitect"]

# The image runs the implemented API entry point by default. CLI smoke checks can
# override CMD, e.g. `docker run --rm image autonet --help`.
CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).read()"
