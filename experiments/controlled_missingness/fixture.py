"""Synthetic source-audited fixture, NOT OpenRCA or a real payment system."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

SCOPE = dict(incident='SYNTH-01', service='Payment', trace_id='a'*32,
             span_id='b'*16, operation='charge_simulated', attempt='A1')
SOURCE_VERSION = 'controlled-fixture-1'


def charge_simulated(approve: bool = True):
    """Completion means the defined simulated business work succeeded, not caller receipt."""
    records = []
    def emit(event, record_id):
        records.append(dict(scope=dict(SCOPE), event=event, record_id=record_id,
                            emitter=SOURCE_VERSION))
    emit('handler_started', 'E1')  # WR-01: first statement of operation's observed body
    if not approve:
        return False, records
    result = True  # simulated business work completed successfully
    if result:
        emit('operation_succeeded', 'E2')  # WR-02: reached only after simulated work succeeded
    return result, records
