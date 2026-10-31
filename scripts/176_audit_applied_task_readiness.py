"""Check held author task contracts and acquired metadata without running models.

This verifies setup evidence, not scientific readiness or predictive performance.
It never imports an encoder, downloads imagery or submits to the active queue.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config = ROOT / 'config/limburg_applied_tasks_v1.json'
    plan = json.loads(config.read_text())
    for source in plan['sources'].values():
        assert digest(ROOT / source['path']) == source['sha256'], source['path']
    tiny = yaml.safe_load((ROOT / plan['sources']['terramind_tiny']['path']).read_text())
    task = tiny['model']['init_args']
    assert task['freeze_backbone'] is True
    assert task['model_args']['backbone'] == 'terramind_v1_tiny'
    assert task['model_args']['decoder'] == 'UNetDecoder'
    assert task['model_args']['backbone_modalities'] == ['S2L1C', 'S1GRD']
    assert task['ignore_index'] == -1
    flood = yaml.safe_load((ROOT / plan['sources']['copernicus_dataset']['path']).read_text())
    assert flood['num_classes'] == 3 and flood['ignore_index'] == 3
    assert flood['input_mode'] == 'spectral' and flood['num_channels'] == 2
    compact = json.loads((ROOT / plan['sources']['galileo_flood_config']['path']).read_text())
    assert compact['task_type'] == 'seg' and compact['num_classes'] == 2
    assert compact['input_height_width'] == 64 and list(compact['band_info']) == ['s1']
    evidence = ROOT / 'docs/reviews/applied-task-config-2026-10-31'
    sizes = json.loads((evidence / 'sen1floods11-size-summary.json').read_text())
    core = [r for r in sizes if r['folder'] in ['LabelHand', 'S1Hand', 'S2Hand']]
    assert len(core) == 3 and all(r['objects'] == 446 for r in core)
    receipts = json.loads((evidence / 'sample-download-receipts.json').read_text())
    for r in receipts:
        assert digest(ROOT / r['file']) == r['sha256']
    sample = json.loads((evidence / 'sample-raster-inspection.json').read_text())
    assert len({Path(r['file']).name.split('_')[0] + '_' + Path(r['file']).name.split('_')[1] for r in sample}) == 1
    assert all(r['shape'][-2:] == [512, 512] for r in sample)
    assert next(r for r in sample if 'LabelHand' in r['file'])['classes'] == [-1, 0, 1]
    report = dict(
        status='source_contracts_and_small_sample_checked_no_model_run',
        plan_sha256=digest(config), script_sha256=digest(Path(__file__)),
        source_contracts_verified=len(plan['sources']),
        tasks=[dict(id=r['id'], model=r['model'], status='identified_not_training_ready') for r in plan['tasks']],
        hand_labeled_dataset_bytes=sum(r['bytes'] for r in core),
        hand_labeled_dataset_gib=sum(r['bytes'] for r in core) / 1024**3,
        source_sample_bytes=sum(r['bytes'] for r in receipts if r['file'].endswith('.tif')),
        not_verified=['full benchmark data integrity', 'runtime heads/backward pass', 'local reference AOI overlap and acquisition matching', 'fair accuracy/resource comparisons'],
        source_hashes=plan['sources'],
    )
    (evidence / 'source-contract-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Checked {len(plan['sources'])} source contracts; 3 aligned sample rasters; no model run")


if __name__ == '__main__':
    main()
