"""R4 regression: per-row parse failure must NOT become Absent."""

from uuid import uuid4

from src.storage.adapters.turso_signal_lifecycle_repository import (
    TursoSignalLifecycleRepository,
)


class _MockResult:
    def __init__(self, rows):
        self.rows = rows


class _MockClient:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params):
        return _MockResult(self._rows)


def _repo_with_rows(rows):
    repo = TursoSignalLifecycleRepository.__new__(TursoSignalLifecycleRepository)
    repo.client = _MockClient(rows)
    return repo


def test_malformed_signal_id_marks_whole_chunk_failed_not_absent():
    sid_a = uuid4()
    sid_b = uuid4()
    repo = _repo_with_rows([["not-a-uuid", "ACTIVE", None]])

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert len(result.found) == 0
    assert sid_a not in result.absent
    assert sid_b not in result.absent
    assert sid_a in result.failed
    assert sid_b in result.failed


def test_unparseable_expires_at_goes_to_failed_not_absent():
    sid = uuid4()
    repo = _repo_with_rows([[str(sid), "ACTIVE", "not-an-iso-date"]])

    result = repo.get_lifecycle_lookup([sid])

    assert sid not in result.absent
    assert sid in result.failed
    assert sid not in result.found


def test_clean_absent_when_no_rows_returned():
    """When chunk query returns no rows at all → absent is legitimate."""
    sid_a = uuid4()
    sid_b = uuid4()
    repo = _repo_with_rows([])

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert result.found == {}
    assert result.failed == set()
    assert result.absent == {sid_a, sid_b}


def test_valid_row_parsed_to_found():
    sid = uuid4()
    repo = _repo_with_rows(
        [[str(sid), "EXPIRED", "2026-10-09T04:00:00+00:00"]]
    )

    result = repo.get_lifecycle_lookup([sid])

    assert sid in result.found
    assert result.found[sid].status == "EXPIRED"
    assert sid not in result.absent
    assert sid not in result.failed


def test_query_failure_marks_chunk_failed():
    sid_a = uuid4()
    sid_b = uuid4()

    class _BrokenClient:
        def execute(self, sql, params):
            raise RuntimeError("simulated db failure")

    repo = TursoSignalLifecycleRepository.__new__(TursoSignalLifecycleRepository)
    repo.client = _BrokenClient()

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert result.found == {}
    assert result.absent == set()
    assert result.failed == {sid_a, sid_b}

def test_active_with_null_expires_at_goes_to_failed():
    """B1: ACTIVE row with NULL expires_at must not be in found."""
    sid = uuid4()
    repo = _repo_with_rows([[str(sid), "ACTIVE", None]])

    result = repo.get_lifecycle_lookup([sid])

    assert sid not in result.found
    assert sid in result.failed
    assert sid not in result.absent


def test_expired_with_null_expires_at_stays_found():
    """B1: status-driven rule — only ACTIVE requires expires_at."""
    sid = uuid4()
    repo = _repo_with_rows([[str(sid), "EXPIRED", None]])

    result = repo.get_lifecycle_lookup([sid])

    assert sid in result.found
    assert result.found[sid].status == "EXPIRED"
    assert sid not in result.failed
    assert sid not in result.absent    


def test_chunk_ambiguous_overrides_all_results_r5():
    """R5: if any row has malformed signal_id, whole chunk → failed."""
    sid_valid = uuid4()
    rows = [
        [str(sid_valid), "ACTIVE", "2026-10-12T00:00:00+00:00"],  # valid
        ["not-a-uuid", "ACTIVE", None],                           # malformed
    ]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid_valid])

    # R5: valid row must NOT remain in found
    assert sid_valid not in result.found
    assert sid_valid in result.failed
    assert sid_valid not in result.absent


def test_chunk_ambiguous_marks_all_chunk_ids_failed_r5():
    """R5: all query IDs in ambiguous chunk → failed, none found/absent."""
    sid_a = uuid4()
    sid_b = uuid4()
    rows = [["not-a-uuid", "ACTIVE", None]]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert result.found == {}
    assert result.absent == set()
    assert result.failed == {sid_a, sid_b}


def test_invalid_status_goes_to_failed_r6():
    """R6: unrecognized status must not enter found or absent."""
    sid = uuid4()
    repo = _repo_with_rows([[str(sid), "WEIRD_STATUS", None]])

    result = repo.get_lifecycle_lookup([sid])

    assert sid not in result.found
    assert sid not in result.absent
    assert sid in result.failed


def test_valid_statuses_only_r6():
    """R6: only ACTIVE and EXPIRED are accepted."""
    sid_a = uuid4()
    sid_b = uuid4()
    rows = [
        [str(sid_a), "ACTIVE", "2026-10-12T00:00:00+00:00"],
        [str(sid_b), "EXPIRED", None],
    ]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert result.found[sid_a].status == "ACTIVE"
    assert result.found[sid_b].status == "EXPIRED"
    assert result.failed == set()

def _assert_bucket_exclusivity(result):
    """R8: no signal_id may appear in more than one bucket."""
    f_keys = set(result.found.keys())
    overlap_fa = f_keys & result.absent
    overlap_ff = f_keys & result.failed
    overlap_af = result.absent & result.failed
    assert not overlap_fa, f"found ∩ absent: {overlap_fa}"
    assert not overlap_ff, f"found ∩ failed: {overlap_ff}"
    assert not overlap_af, f"absent ∩ failed: {overlap_af}"


def test_duplicate_rows_one_valid_one_malformed_same_id_r8():
    """R8: same signal_id with one valid + one malformed row → failed only."""
    sid = uuid4()
    rows = [
        [str(sid), "ACTIVE", "2026-10-12T00:00:00+00:00"],  # valid
        [str(sid), "ACTIVE", "not-an-iso-date"],            # malformed
    ]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid])

    assert sid in result.failed
    assert sid not in result.found
    assert sid not in result.absent
    _assert_bucket_exclusivity(result)


def test_duplicate_rows_invalid_status_then_valid_same_id_r8():
    """R8: same signal_id, invalid-status row + valid row → failed only."""
    sid = uuid4()
    rows = [
        [str(sid), "WEIRD_STATUS", None],                   # invalid status
        [str(sid), "EXPIRED", None],                        # valid
    ]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid])

    assert sid in result.failed
    assert sid not in result.found
    assert sid not in result.absent
    _assert_bucket_exclusivity(result)


def test_bucket_exclusivity_on_mixed_results_r8():
    """R8: mixed chunk with different ids — each id in exactly one bucket."""
    sid_found = uuid4()
    sid_absent = uuid4()
    sid_failed = uuid4()
    rows = [
        [str(sid_found), "EXPIRED", None],
        [str(sid_failed), "WEIRD_STATUS", None],
    ]
    repo = _repo_with_rows(rows)

    result = repo.get_lifecycle_lookup([sid_found, sid_absent, sid_failed])

    assert sid_found in result.found
    assert sid_absent in result.absent
    assert sid_failed in result.failed
    _assert_bucket_exclusivity(result)


def test_bucket_exclusivity_on_partial_chunk_failure_r8():
    """R8: query failure marks whole chunk failed, no residual in other buckets."""
    sid_a = uuid4()
    sid_b = uuid4()

    class _BrokenClient:
        def execute(self, sql, params):
            raise RuntimeError("db down")

    repo = TursoSignalLifecycleRepository.__new__(TursoSignalLifecycleRepository)
    repo.client = _BrokenClient()

    result = repo.get_lifecycle_lookup([sid_a, sid_b])

    assert result.found == {}
    assert result.absent == set()
    assert result.failed == {sid_a, sid_b}
    _assert_bucket_exclusivity(result)        