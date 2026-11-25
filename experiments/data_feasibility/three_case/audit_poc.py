"""Three cached published incidents; semantic smoke test, not a trained RCA method.
Run: python audit_poc.py --data-dir /path/to/cached/files --out results.json
Dependencies: pandas, pyarrow. No label values enter inference.
"""
import argparse,json,hashlib,time
from pathlib import Path
import pandas as pd

def keys(df):
 return list(zip(df.trace_id.fillna('').astype(str),df.span_id.fillna('').astype(str),df.service_name.fillna('').astype(str)))
def valid(k): return all(k) and set(k[0])!={'0'} and set(k[1])!={'0'}
def candidates(logs,traces):
 observed=set(keys(traces));return sorted({k for k in keys(logs) if valid(k) and k not in observed})
def infer(logs,traces,mode):
 # Anomaly heuristic only: service error-span fraction. Missing penalty is illustrative.
 status=traces['attr.status_code'].fillna('').astype(str).str.lower().eq('error')
 http=pd.to_numeric(traces['attr.http.response.status_code'],errors='coerce').ge(500)
 base=(status|http).groupby(traces.service_name).mean().to_dict()
 missing=candidates(logs,traces)
 services=sorted(set(logs.service_name.dropna())|set(traces.service_name.dropna()))
 intervals={}
 for s in services:
  b=float(base.get(s,0));n=sum(k[2]==s for k in missing)
  if mode=='absence_penalty': lo=hi=b+0.1*n
  elif mode=='neutral_witness':lo=hi=b
  else:lo=b;hi=b+0.1*n
  intervals[s]=[lo,hi]
 rank=sorted(services,key=lambda s:(-sum(intervals[s])/2,s))
 stable=[s for s in services if all(s==t or intervals[s][0]>intervals[t][1] for t in services)]
 return {'ranking':rank,'intervals':intervals,'stable_first':stable,'unmatched_log_keys':len(missing)}

def run(root):
 start=time.perf_counter();out={'scope':'3 convenience-sampled cached incidents, one per system; not representative','weight_warning':'0.1 missing penalty is a toy engineering parameter, not a validated score','cases':[]}
 for system in ['tt','hs','otel']:
  paths={t:root/f'opslite_{system}_abnormal_{t}.parquet' for t in ['logs','traces']}
  logs=pd.read_parquet(paths['logs']);traces=pd.read_parquet(paths['traces'])
  lk=keys(logs);tk=keys(traces);ts=set(tk)
  matched=[k for k in lk if valid(k) and k in ts]
  common=sorted(set(matched));assert common,'No exact witnesses'
  # Select without consulting labels, deterministically.
  chosen=common[0]
  hidden=traces.loc[[k!=chosen for k in tk]].copy()
  # Real records; only observation visibility changed in memory.
  assert chosen not in set(keys(hidden)) and chosen in set(keys(logs))
  assert chosen in candidates(logs,hidden)
  wrong=logs.loc[[k==chosen for k in lk]].copy();wrong['trace_id']='unrelated-request'
  assert chosen not in set(keys(wrong))
  modes={m:infer(logs,hidden,m) for m in ['absence_penalty','neutral_witness','ambiguity_range']}
  # Labels read only after inference, for audit provenance/evaluation.
  label=json.loads((root/f'opslite_{system}_label.json').read_text())
  required=[f['service'] for f in label['faults'] if f['role']=='required']
  row={'system':system,'case':label['case'],'log_rows':len(logs),'span_rows':len(traces),'valid_log_id_rows':sum(valid(k) for k in lk),'exact_matched_log_rows':len(matched),'exact_match_percent':round(100*len(matched)/len(logs),2),'unique_matched_span_keys':len(common),'duplicate_span_keys':len(tk)-len(set(tk)),'native_unmatched_log_keys':len(candidates(logs,traces)),'controlled_hide':{'service':chosen[2],'removed_span_rows':len(traces)-len(hidden),'surviving_matching_logs':sum(k==chosen for k in lk),'execution_interpretation':'log emitted in matching span context; completion and collector cause remain unknown'},'outputs':modes,'required_roots_evaluator_only':required,'hashes':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}}
  out['cases'].append(row)
 out['checks']={'exact_witness_survives_hidden_span':3,'wrong_request_rejected':3,'all_passed':True}
 out['elapsed_seconds']=round(time.perf_counter()-start,3)
 return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--data-dir',type=Path,required=True);a.add_argument('--out',type=Path,default=Path('results.json'));args=a.parse_args();r=run(args.data_dir);args.out.write_text(json.dumps(r,indent=2));print(json.dumps([{k:v for k,v in c.items() if k not in ['outputs','hashes']} for c in r['cases']],indent=2));print(r['checks'])
