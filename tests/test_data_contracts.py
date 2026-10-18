import polars as pl
from support_policy.validate_data import validate_frames

def test_valid_fixture(frames):
    assert all(validate_frames(frames).values())

def test_duplicate_assignment_is_rejected(frames):
    frames['assignments']=pl.concat([frames['assignments'],frames['assignments'].head(1)])
    assert not validate_frames(frames)['assignments_unique_key']

def test_orphan_refund_is_rejected(frames):
    frames['refund_transactions']=frames['refund_transactions'].with_columns(pl.lit(999).alias('case_id'))
    assert not validate_frames(frames)['refund_transactions_foreign_key']

def test_negative_refund_is_rejected(frames):
    frames['refund_transactions']=frames['refund_transactions'].with_columns(pl.lit(-1.).alias('amount_usd'))
    assert not validate_frames(frames)['nonnegative_refunds']

def test_wrong_customer_index_case_is_rejected(frames):
    frames['assignments']=frames['assignments'].with_columns(pl.lit(1).alias('index_case_id'))
    assert not validate_frames(frames)['correct_index_case']
