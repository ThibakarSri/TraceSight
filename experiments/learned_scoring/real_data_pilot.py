"""Leakage-conscious service-ranking pilot on cached OpenRCA ops-lite telemetry.

This is a scorer pilot, not a validated execution-history RCA experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURES = ['log_count', 'log_error_rate', 'span_count', 'span_error_rate',
            'http_5xx_rate', 'duration_median', 'duration_p95', 'join_fraction']


def stable_hash(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:16], 16)


def feature_rows(case, path):
    logs = pd.read_parquet(path / 'abnormal_logs.parquet', columns=[
        'trace_id', 'span_id', 'service_name', 'level'])
    spans = pd.read_parquet(path / 'abnormal_traces.parquet', columns=[
        'trace_id', 'span_id', 'service_name', 'duration', 'attr.status_code',
        'attr.http.response.status_code'])
    logs = logs[logs.service_name.notna()].copy()
    spans = spans[spans.service_name.notna()].copy()
    logs['_error'] = logs.level.fillna('').astype(str).str.contains('error|fatal', case=False, regex=True)
    spans['_error'] = spans['attr.status_code'].fillna('').astype(str).str.lower().eq('error')
    spans['_5xx'] = pd.to_numeric(spans['attr.http.response.status_code'], errors='coerce').ge(500)
    spans['_duration'] = pd.to_numeric(spans.duration, errors='coerce')
    l = logs.groupby('service_name').agg(log_count=('_error', 'size'), log_error_rate=('_error', 'mean'))
    s = spans.groupby('service_name').agg(span_count=('_error', 'size'), span_error_rate=('_error', 'mean'),
                                         http_5xx_rate=('_5xx', 'mean'), duration_median=('_duration', 'median'),
                                         duration_p95=('_duration', lambda x: x.quantile(.95)))
    lk = ['trace_id', 'span_id', 'service_name']
    valid = logs[logs.trace_id.notna() & logs.span_id.notna()]
    keys = spans[lk].drop_duplicates()
    matched = valid[lk].merge(keys.assign(_match=1), how='left', on=lk)
    j = matched.assign(_match=matched._match.fillna(0)).groupby('service_name')._match.mean().rename('join_fraction')
    f = l.join(s, how='outer').join(j, how='left')
    f[['log_count', 'span_count']] = f[['log_count', 'span_count']].fillna(0)
    roots = set(case['root_services'])
    out = []
    for service, row in f.iterrows():
        out.append({'case': case['name'], 'system': case['system'], 'service': service,
                    'target': int(service in roots), **{k: float(row[k]) for k in FEATURES}})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--max-cases', type=int, default=120)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = [json.loads(x) for x in args.manifest.read_text().splitlines()]
    # Select without looking at outcomes; root_services are read only for target construction.
    cases = sorted(cases, key=lambda c: stable_hash(c['name']))[:args.max_cases]
    rows, failures = [], []
    for c in cases:
        try:
            rows += feature_rows(c, args.root / 'cases' / c['name'])
        except Exception as exc:
            failures.append({'case': c['name'], 'error': str(exc)})
    data = pd.DataFrame(rows)
    data.to_csv(args.output / 'service_features.csv', index=False)
    # Hold out entire incidents; never train and test on services from the same incident.
    ids = sorted(data.case.unique(), key=stable_hash)
    cut = max(1, int(.7 * len(ids)))
    train = data[data.case.isin(ids[:cut])].copy()
    test = data[data.case.isin(ids[cut:])].copy()
    pipe = make_pipeline(SimpleImputer(strategy='constant', fill_value=0, add_indicator=True),
                         StandardScaler(), LogisticRegression(max_iter=1000, class_weight='balanced', random_state=0))
    pipe.fit(train[FEATURES], train.target)
    test['probability'] = pipe.predict_proba(test[FEATURES])[:, 1]
    test['error_baseline'] = test.log_error_rate.fillna(0) + test.span_error_rate.fillna(0)
    test['split'] = 'held_out'
    test.to_csv(args.output / 'held_out_predictions.csv', index=False)

    def rank_metric(score):
        result = []
        for _, g in test.groupby('case'):
            ranked = g.sort_values([score, 'service'], ascending=[False, True])
            if not ranked.target.any():
                continue  # roots not represented among observed services
            hits = np.flatnonzero(ranked.target.to_numpy())
            result.append((int(hits[0] == 0), int(hits[0] < 3), float(1 / (hits[0]+1))))
        return {'evaluable_cases': len(result), 'top1': float(np.mean([x[0] for x in result])) if result else None,
                'top3': float(np.mean([x[1] for x in result])) if result else None,
                'mrr': float(np.mean([x[2] for x in result])) if result else None}
    report = {'dataset': 'cached ops-lite abnormal logs and spans', 'sampled_cases': len(cases),
              'processed_cases': len(ids), 'failed_cases': failures,
              'train_cases': len(ids[:cut]), 'held_out_cases': len(ids[cut:]),
              'train_service_rows': len(train), 'held_out_service_rows': len(test),
              'root_present_train': int(train.target.sum()), 'root_present_test': int(test.target.sum()),
              'logistic_regression': rank_metric('probability'), 'simple_error_rate': rank_metric('error_baseline'),
              'semantic_witnesses_verified': False, 'compatible_history_integration': False,
              'interpretation': 'Preliminary observed-service scorer only; no validated full TraceSight inference or external benchmark claim.'}
    (args.output / 'results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
