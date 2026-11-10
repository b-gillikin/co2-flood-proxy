import json,statistics,collections,hashlib
from pathlib import Path
base=Path('results/applied_study_v5/ready-v2/synthesis/final'); b=json.loads((base/'benchmark.json').read_text()); jobs=b['job_ledger'];out={}
for task in ['terramind','galileo','prithvi','copernicus']:
 out[task]={}
 for budget in [1.,.2,.05]:
  out[task][str(budget)]={}
  for learner in ['native','unet','unet_standard','linear','physical']:
   rows=[r for key,r in jobs.items() if key.startswith(task+'-'+learner+'-group') and (learner=='physical' or '-'+str(budget).rstrip('0').rstrip('.')+'-' in key)]
   vals=collections.defaultdict(list)
   for r in rows:
    for e,m in r['target_event_metrics'].items():
     if m['iou'] is not None:vals[e].append(m['iou'])
   ev={e:statistics.mean(v) for e,v in vals.items()}
   def rng(key):
    v=[r[key] for r in rows if isinstance(r.get(key),(float,int))];return [min(v),statistics.median(v),max(v)] if v else None
   labels=[r['label_accounting'] for r in rows]
   combined=[x.get('combined_selection_label_fraction') for x in labels if x.get('combined_selection_label_fraction') is not None]
   out[task][str(budget)][learner]={'jobs':len(rows),'mean_event_iou':statistics.mean(ev.values()),'event_iou':ev,'tuning_seconds_min_median_max':rng('tuning_wall_s'),'scoring_seconds_min_median_max':rng('test_scoring_wall_s'),'lr_boundary':sum(bool(r.get('learning_rate_boundary')) for r in rows),'epoch_at_ceiling':sum(bool(r.get('epoch_at_ceiling')) for r in rows),'failed_candidates':sum(r.get('failed_candidates',0) for r in rows),'combined_label_fraction_range':[min(combined),max(combined)] if combined else None}
print('BENCHMARK IOU native/unet/standard/linear/physical')
for t,bb in out.items():
 for bud,rr in bb.items():print(t,bud,[round(r['mean_event_iou'],3) for r in rr.values()], 'labels',rr['native']['combined_label_fraction_range'],'flags',[rr['native'][k] for k in ['lr_boundary','epoch_at_ceiling']])
local={}
for task in out:
 casevals=collections.defaultdict(lambda:collections.defaultdict(list));meta={}
 for f in base.joinpath('local').glob(task+'-*-reference-agreement.json'):
  d=json.loads(f.read_text())
  for r in d['case_summaries']:
   m=r['support']['common'];casevals[r['case']][r['model']].append(m['iou']);meta[r['case']]={'offset_hours':r['reference_offset_hours'],'dependence':r['reference_dependence'],'coverage':m['coverage_fraction'],'support_pixels':m['support_pixels'],'reference_positive_pixels':m['tp']+m['fn']}
 cases={c:{'meta':meta[c],'mean_iou':{m:statistics.mean(v) if all(x is not None for x in v) else None for m,v in mm.items()},'repeats':{m:len(v) for m,v in mm.items()}} for c,mm in casevals.items()}
 local[task]=cases
 print('LOCAL',task,'cases',len(cases),'offset range',min(x['meta']['offset_hours'] for x in cases.values()),max(x['meta']['offset_hours'] for x in cases.values()))
 for c,x in cases.items(): print(c.split(':')[0],round(x['meta']['offset_hours'],1),round(x['meta']['coverage'],3),x['meta']['reference_positive_pixels'],{m:round(v,3) if v is not None else None for m,v in x['mean_iou'].items()})
Path('results/findings-review-2026-11-10/summary.json').write_text(json.dumps({'benchmark':out,'local':local,'source_sha256':hashlib.sha256((base/'benchmark.json').read_bytes()).hexdigest()},indent=2))
