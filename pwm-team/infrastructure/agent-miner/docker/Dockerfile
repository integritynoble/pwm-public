# PWM solver sandbox — provides Python 3.11 runtime only.
# Solvers are injected at runtime via volume mounts; nothing is COPY-ed in.
#
# GPU support: pass --gpus all (or --gpus device=0) to `docker run` when an
# NVIDIA GPU is present and nvidia-docker / the NVIDIA Container Toolkit is
# installed.  Without that flag the container runs on CPU automatically.
#
# Resource limits are enforced at `docker run` time, e.g.:
#   --memory 8g --memory-swap 8g --cpus 4
#   --gpus all --env NVIDIA_VISIBLE_DEVICES=0
#
# Typical invocation:
#   docker run --rm \
#     --network none \
#     --read-only \
#     --mount type=bind,src=/host/input,dst=/input,readonly \
#     --mount type=bind,src=/host/output,dst=/output \
#     --memory 8g \
#     pwm-sandbox

FROM python:3.11-slim

# Install only what is needed to run scientific Python solvers.
# Clean the apt cache in the same layer to keep the image lean.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc \
        libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# Common scientific Python dependencies solvers are likely to need.
RUN pip install --no-cache-dir \
        numpy \
        scipy

# Create a non-root user (uid 1000) that will own the working directory.
RUN useradd --uid 1000 --no-create-home --shell /bin/false miner

# Provide the two mount-point directories with correct ownership.
# /input  — read-only bind mount (solver source + data injected at runtime)
# /output — read-write bind mount (solver writes results here)
RUN mkdir /input /output \
 && chown miner:miner /input /output

# Working directory inside the container.
WORKDIR /solver
RUN chown miner:miner /solver

# Drop privileges — never run as root.
USER miner

# Default entrypoint: run the solver that the caller placed in /input.
# The host executor may override CMD or pass extra flags; the entrypoint
# itself is fixed so callers cannot accidentally skip the solve step.
ENTRYPOINT ["python", "/input/solve.py", "--input", "/input", "--output", "/output"]
