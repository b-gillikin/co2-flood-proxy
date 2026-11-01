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
- `copernicus`: held modern runtime plus task-only OpenMMLab packages. Dependency
  checks pass, but native `mmseg.models` import fails on absent `mmcv._ext`.
  `mmcv-lite` does not supply compiled operators. This is **not a ready native
  change-segmentation runtime**. Do not install a fake operator module or claim
  a classification backbone check validates its decoder.

Additional pinned Copernicus overlay packages include mmcv-lite2.1.0,
mmengine0.10.7, mmsegmentation1.2.2, NumPy1.26.4, SciPy1.14.1,
OpenCV4.11.0.86, matplotlib3.10.8, contourpy1.3.3, ftfy6.3.1 and regex2024.11.6.
The exact full dependency set is in the freeze file. No new model weights were
downloaded. A supported compiled runtime or a separately validated, explicitly
named portable head is remaining work.
