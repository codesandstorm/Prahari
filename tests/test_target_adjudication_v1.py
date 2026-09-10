import copy,csv
from pathlib import Path
from src.ml.adjudication import EVIDENCE_FIELDS,HUMAN_FIELDS,LABELS,read_csv,validate_review
ROOT=Path(__file__).resolve().parents[1]
S1=ROOT/'validation/s1/s1_human_validation_v1.csv';S2=ROOT/'validation/s2/s2_human_validation_v1.csv'
def test_samples_are_separate_stable_and_blank():
    for target,path in [('S1',S1),('S2',S2)]:
        rows=read_csv(path);assert len(rows)==60
        assert [r['review_row_id'] for r in rows]==[f'{target}-VAL-{i:04d}' for i in range(1,61)]
        assert all(r['target_family']==target for r in rows)
        assert all(not r.get(f) for r in rows for f in HUMAN_FIELDS)
def test_strata_include_weak_correction_and_negative_controls():
    for path in (S1,S2):
        rows=read_csv(path);strata={r['review_stratum'] for r in rows}
        assert {'WEAK_REGIME','CORRECTION_LIKE','NEGATIVE_CONTROL'}<=strata
def test_provenance_and_source_evidence_preserved():
    for path in (S1,S2):
        assert all(r['source_report_ids'] and r['source_sha256s'] and r['page_table_provenance'] and r['source_evidence_excerpt'] for r in read_csv(path))
def completed(rows):
    x=copy.deepcopy(rows);r=x[0];r.update(manual_label=LABELS[0],reviewer_name_or_id='reviewer-1',review_confidence='HIGH',evidence_verified='YES',source_page_verified='YES',identity_verified='YES',review_timestamp='2026-09-11T10:00:00+05:30');return x
def test_validator_completion_count_and_valid_label():
    base=read_csv(S1);result=validate_review(base,completed(base));assert result['valid'] and result['reviewed']==1 and result['unresolved']==59
def test_validator_rejects_tampering_unknown_duplicate_and_invalid_label():
    base=read_csv(S1)
    x=completed(base);x[0]['baseline_date']='2099-01-01';assert not validate_review(base,x)['valid']
    x=completed(base);x[0]['review_row_id']='UNKNOWN';assert not validate_review(base,x)['valid']
    x=completed(base);x.append(copy.deepcopy(x[0]));assert not validate_review(base,x)['valid']
    x=completed(base);x[0]['manual_label']='YES';assert not validate_review(base,x)['valid']
def test_source_audit_hashes_and_availability():
    rows=read_csv(ROOT/'validation/target_adjudication_v1/source_availability_audit.csv')
    assert rows and all(r['pdf_status']=='SOURCE_AVAILABLE' and r['hash_matches']=='True' for r in rows)
