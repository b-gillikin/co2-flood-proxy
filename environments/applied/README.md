# Applied spatial runtime overlays

Prepared 1 November 2026 by `scripts/189_prepare_applied_runtimes.py`. Each new
`.venvs-applied/` environment has its own install location and reads an unchanged
held EO environment via `held-runtime.pth`. Existing extraction environments
were not upgraded. These are explicitly dependent overlays, not standalone
portable copies. `runtimes.json` records bases/Python/dependency checks; the
three visible-freeze files record resolved packages for reconstruction.
`source-code-snapshot.json` additionally fingerprints key held author/framework
files after the engineering checks; its timing is explicit rather than claimed
as an earlier capture. Preserve the held source collection when reconstructing
the local-file TerraTorch dependency.

- `spatial`: held TerraMind/TerraTorch runtime, for TerraMind and Prithvi tasks.
- `galileo`: held Nano runtime, for the native radar spatial probe.
- `copernicus`: held modern runtime plus task-only OpenMMLab packages. The
  initial mmcv-lite import failure was resolved on1November by a real
  mmcv2.1.0 CPU extension build, isolated from extraction environments.
  Native Feature2Pyramid/UPerHead/FCNHead forward/backward passed with held
  checkpoint and real pre/post imagery. MPS remains untested while occupied.

Pinned packages include mmcv2.1.0 (NOT mmcv-lite), mmengine0.10.7,
mmsegmentation1.2.2, NumPy1.26.4, SciPy1.14.1, OpenCV4.11.0.86,
matplotlib3.10.8, contourpy1.3.3, ftfy6.3.1 and regex2024.11.6. Build tools are
setuptools80.9.0 and ninja1.13.2; only one compilation worker is used. The
visible freeze records the resolved set. No new model weights were downloaded.

[Rebuild recipe](build-copernicus.sh), [native engineering evidence](copernicus-native-check.json),
and [scientific/runtime qualifications](../../docs/limburg-applied-preparation-2026-11-01.md).
The native adapter aliases the held renamed language dictionary to the source's
legacy filename to avoid a404 download, preserving original vendor Python.
