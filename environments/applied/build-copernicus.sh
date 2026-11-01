#!/bin/sh
# Isolated Apple Silicon CPU extension build, leaving held extraction env intact.
set -eu
cd "$(dirname "$0")/../.."
task_python="$PWD/.venvs-applied/copernicus/bin/python"
"$task_python" -m pip install --no-deps setuptools==80.9.0 ninja==1.13.2
MMCV_WITH_OPS=1 MAX_JOBS=1 "$task_python" -m pip wheel mmcv==2.1.0 \
  --no-deps --no-build-isolation --wheel-dir .venvs-applied/wheels
"$task_python" -m pip uninstall -y mmcv-lite
"$task_python" -m pip install --no-deps .venvs-applied/wheels/mmcv-2.1.0-*.whl
"$task_python" -m pip check
"$task_python" scripts/193_check_copernicus_runtime.py
