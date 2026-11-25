"""Reproduce controlled masking with the original TraceSight v0.1.0 engine.
No ML training, real dataset, or ground-truth labels enter inference.
"""
from dataclasses import asdict, replace
from itertools import product
from pathlib import Path
import argparse
import csv
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from tracesight.model import Variable, Constraint, Term, Problem
from tracesight.witnesses import Scope, Witness, constraints_for
from tracesight.inference import infer, score
from fixture import SCOPE, SOURCE_VERSION, charge_simulated

RULES = {'handler_started': 'WR-01', 'operation_succeeded': 'WR-02'}
TARGET = Scope(**SCOPE)
FIXTURE_SHA = hashlib.sha256((HERE / 'fixture.py').read_bytes()).hexdigest()


def compile_records(records, scope=TARGET):
    """Trust only the two reviewed fixture emitters; reject incomplete scope.
    The caller must establish authenticity; this is not a production verifier.
    """
    witnesses, sources = [], {}
    if not all(isinstance(x, str) and x.strip() for x in asdict(scope).values()):
        raise ValueError('All scope fields must be established for this demo')
    for record in records:
        rule = RULES.get(record.get('event'))
        if not rule or record.get('emitter') != SOURCE_VERSION:
            continue
        if set(record.get('scope', {})) != set(asdict(scope)):
            continue
        other = Scope(**record['scope'])
        if other != scope or not all(isinstance(x, str) and x.strip() for x in asdict(other).values()):
            continue
        rid = record['record_id']
        sources[rid] = f"Synthetic observed record {rid}: {record['event']}"
        sources[rule] = f"Reviewed fixture.py; version {SOURCE_VERSION}; SHA256 {FIXTURE_SHA}"
        witnesses.append(Witness(other, record['event'], rid, rule, True))
    return constraints_for(scope, 'payment', witnesses), sources


def make_problem(records):
    constraints, sources = compile_records(records)
    sources.update({'ORDER': 'Declared fixture model: successful completion requires entry; no terminal-failure claim from no completion.',
                    'SCORE': 'Fixed illustrative scores selected for the software test only; not calibrated or learned.'})
    constraints.append(Constraint('stage_order', ('payment.entered','payment.completed'),
                                  (('no','no'),('yes','no'),('yes','yes')), ('ORDER',)))
    return Problem(('Checkout','Payment'),
                   (Variable('payment.entered',('no','yes')),Variable('payment.completed',('no','yes'))),
                   tuple(constraints), {'Checkout':6.0,'Payment':2.0},
                   (Term('Payment', (('payment.entered','yes'),('payment.completed','no')),7.0,('SCORE',)),),
                   sources, 'synthetic_controlled_masking_only')


def evaluate(records):
    problem = make_problem(records)
    result = infer(problem)
    histories = []
    for values in product(*(v.domain for v in problem.variables)):
        state = dict(zip((v.name for v in problem.variables),values))
        if all(tuple(state[v] for v in c.variables) in c.allowed for c in problem.constraints):
            s = score(problem,state)
            highest = max(s.values())
            histories.append({'state':state,'scores':s,'winners':[k for k,v in s.items() if v == highest]})
    facts = {}
    for var in problem.variables:
        values = {h['state'][var.name] for h in histories}
        facts[var.name] = next(iter(values)) if len(values)==1 else 'unknown'
    return dict(result, compatible_histories=histories, execution_facts=facts,
                observed_record_ids=[r['record_id'] for r in records],
                last_verified_progress=('operation_success' if facts['payment.completed']=='yes' else
                                        'handler_entry' if facts['payment.entered']=='yes' else 'unknown'))


def save(path, obj):
    path.write_text(json.dumps(obj,indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'local_runs' / 'controlled_missingness')
    output = parser.parse_args().output.resolve()
    for d in ('inputs', 'results', 'evidence'):
        (output/d).mkdir(parents=True, exist_ok=True)
    outcome, original = charge_simulated(True)
    masked = [r for r in original if r['event']!='operation_succeeded']
    variants = {'original':original,'masked':masked,'restored':list(original)}
    results = {}
    for name, records in variants.items():
        save(output/'inputs'/f'{name}.json',records)
        result = evaluate(records)
        save(output/'results'/f'{name}.json',result)
        save(output/'inputs'/f'{name}_problem.json',asdict(make_problem(records)))
        results[name]=result
        print(f"{name:8} records={len(records)} histories={result['compatible_states']} "
              f"facts={result['execution_facts']} status={result['status']} "
              f"stable={result['stable_first']} shortlist={result['undominated_candidates']}")
        for h in result['compatible_histories']:
            print('   ',h)
    checks = {
        'fixture returned success': outcome is True,
        'exactly one observation removed': len(original)-len(masked)==1,
        'entry survives masking': results['masked']['execution_facts']['payment.entered']=='yes',
        'completion becomes unknown': results['masked']['execution_facts']['payment.completed']=='unknown',
        'history count expands 1 to 2': (results['original']['compatible_states'],results['masked']['compatible_states'])==(1,2),
        'original stable Checkout': results['original']['stable_first']==['Checkout'],
        'masked ambiguous with two rivals': results['masked']['status']=='ambiguous' and set(results['masked']['undominated_candidates'])=={'Checkout','Payment'},
        'restored logical result matches original': {k:v for k,v in results['original'].items() if k!='seconds'}=={k:v for k,v in results['restored'].items() if k!='seconds'},
        'scorer fixed across variants': all(r['score_definition']==results['original']['score_definition'] for r in results.values()),
        'masked sources exclude hidden record': 'E2' not in results['masked']['sources'] and 'WR-02' not in results['masked']['sources'],
    }
    wrong = dict(original[1],scope=dict(SCOPE,attempt='A2'))
    checks['wrong retry success rejected'] = evaluate(masked+[wrong])['execution_facts']['payment.completed']=='unknown'
    unverified = dict(original[1],emitter='unreviewed')
    checks['unreviewed emitter rejected'] = evaluate(masked+[unverified])['execution_facts']['payment.completed']=='unknown'
    _, non_success = charge_simulated(False)
    checks['no success witness emitted on unsuccessful fixture path'] = all(r['event']!='operation_succeeded' for r in non_success)
    try:
        compile_records(original, replace(TARGET,attempt=''))
    except ValueError:
        checks['missing attempt rejected'] = True
    else:
        checks['missing attempt rejected'] = False
    checks['absence does not imply failure'] = any(h['state']['payment.completed']=='yes' for h in results['masked']['compatible_histories'])
    save(output/'results'/'checks.json',checks)
    # Evaluator-only record: never read by evaluate()/make_problem().
    save(output/'evidence'/'mask_manifest_evaluator_only.json',{
        'fixture_returned_success':outcome,'hidden_record_ids':['E2'],
        'mask_reason':'deliberate experiment removal; not a collector fault',
        'fixture_sha256':FIXTURE_SHA,'note':'Not an inference input. No incident root label is assigned.'})
    with (output/'results'/'summary.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['variant','retained_records','entry','completion','compatible_histories','decision','stable_first','undominated_candidates','min_checkout_minus_payment','min_payment_minus_checkout'])
        for name,r in results.items():
            m={(x['left'],x['right']):x['minimum_margin'] for x in r['comparisons']}
            w.writerow([name,len(variants[name]),r['execution_facts']['payment.entered'],r['execution_facts']['payment.completed'],r['compatible_states'],r['status'],';'.join(r['stable_first']),';'.join(r['undominated_candidates']),m['Checkout','Payment'],m['Payment','Checkout']])
    for name,ok in checks.items(): print(('PASS' if ok else 'FAIL')+' '+name)
    print(f"{sum(checks.values())}/{len(checks)} checks passed")
    if not all(checks.values()): raise SystemExit(1)

if __name__=='__main__': main()
