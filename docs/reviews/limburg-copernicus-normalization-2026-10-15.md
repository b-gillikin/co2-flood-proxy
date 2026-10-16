# Copernicus-FM normalization review

Internal preparation note. No real event inference, model ranking, new data
requirement or dissertation prose. SkySense is outside the usable screen per
Brian's decision; its downloaded code remains only as provenance.

## Conclusion

The earlier missing-key flag was too categorical. The released checkpoint is
not missing its trained Transformer normalization layers. The authors' official
benchmark explicitly expects the *new output* `fc_norm.weight` and `fc_norm.bias`
to be absent. The implementation creates this LayerNorm with deterministic
scale one, bias zero and epsilon 1e-6. These defaults standardize the output;
they do not introduce a random or fitted correction.

Evidence: pinned
[classification wrapper](https://github.com/zhu-xlab/Copernicus-FM/blob/da95635d76a1feef3006eba474f6175325b4037b/Copernicus-Bench/src/foundation_models/copernicusfm_wrapper.py)
asserts precisely the absent output-normalization keys (and optionally the
classification head). The
[backbone](https://github.com/zhu-xlab/Copernicus-FM/blob/da95635d76a1feef3006eba474f6175325b4037b/Copernicus-FM/src/model_vit.py)
defines the corresponding LayerNorm and pooling choices. The initial check used
the README's class-token convention, which exposes the analogous `norm` keys.
Neither case justifies a blanket assertion that the pretrained encoder is unusable.

For frozen feature preparation, use the benchmark's mean of patch tokens,
followed by this fixed output LayerNorm, with no classifier. This selects one
documented convention before any event comparison; it does not add a pooling
search. All pretrained backbone parameters must match. The local checker now
permits only the exact two expected output keys and verifies their defaults;
any other missing or unexpected key still fails the loading check. No third-party
source code or downloaded checkpoint was changed.

## Actual check

```sh
.venvs-eo/legacy/bin/python environments/eo-screen/check_load.py --model copernicus_fm --probe
```

With the pinned base checkpoint and Torch 2.2.1, this passed:

- Synthetic input: seeded four-band 224 x 224 tensor, seed 1729, publisher's
  wavelengths/bandwidths and unknown-metadata example.
- Frozen/evaluation mode; no event data, training or gradients.
- Output shape 1 x 768, all finite and exactly repeatable on the tested CPU runtime.
- Output equals non-affine LayerNorm of the same pooled features within 1e-6.

The real checkpoint check is recorded in
`data/raw/limburg_dynamic_model_weights/load_checks/copernicus_fm.json` and
summarized in the tracked asset manifest. Small regression tests additionally
reject missing Transformer weights, unexpected keys and changed output scale.
The three normalization regression cases passed in the isolated legacy runtime;
the nine existing asset-acquisition checks also passed in the downloader runtime.
This establishes a usable loader and normalization convention, not hydrological
skill or successful real-imagery adaptation.

## Input normalization is a separate issue

The author confirms the published Sentinel-2 pretraining means and standard
deviations in [issue 4](https://github.com/zhu-xlab/Copernicus-FM/issues/4).
The pinned
[dataset configuration](https://github.com/zhu-xlab/Copernicus-FM/blob/da95635d76a1feef3006eba474f6175325b4037b/Copernicus-Bench/src/configs/dataset/cobench_dfc2020_s2.yaml)
provides named bands, means/stds, wavelengths and bandwidths, including B10.
All thirteen entries and the configuration's SHA-256 are retained in
`config/limburg_eo_model_assets.json`; select only the ten observed bands by name.

The statistics are in Sentinel DN units. Our held harmonized S2 SR bands retain
those scaled DN units, so apply `(DN - mean_DN) / std_DN` once. If an adapter first
converts to physical reflectance, multiply back by 10000 before this formula, or
equivalently divide both means and standard deviations by 10000. Do not multiply
already scaled DN by 10000. Handle QA/nodata and band regridding explicitly rather
than treating masked zeros as observed reflectance.

Pretraining uses S2 TOA; our archive supplies surface reflectance. Applying the
documented normalization to SR is a transfer assumption to evaluate, not proof
of equivalent input distributions. It does not require an additional TOA archive
merely to run the bounded compatibility test. Sensor-specific raw-feature
comparisons and the same held observations remain relevant to the later screen.

The author also explains in [issue 5](https://github.com/zhu-xlab/Copernicus-FM/issues/5)
that arbitrary early fusion of spectral/variable modalities or S1/S2 was not part
of pretraining. Encode modalities separately if needed; do not invent a joint
input tensor and assume it has been validated. This review adds neither a new
fusion experiment nor a need for more modalities.
