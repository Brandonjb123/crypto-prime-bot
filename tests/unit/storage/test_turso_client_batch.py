"""Regression test — TursoClient.batch() delegates to underlying client.

C0.0.3 production blocker: create_with_supersede() calls TursoClient.batch()
but the wrapper previously did not expose batch(). This test prevents
re-introduction.
"""

from unittest.mock import MagicMock

import pytest

from src.storage.adapters.turso_client import TursoClient


class TestTursoClientBatchDelegation:
    def test_unconnected_batch_raises_runtime_error(self):
        client = TursoClient(url="libsql://fake", auth_token="fake")
        with pytest.raises(RuntimeError, match="not connected"):
            client.batch([("SELECT 1", [])])

    def test_connected_batch_delegates_to_underlying(self):
        client = TursoClient(url="libsql://fake", auth_token="fake")
        fake_inner = MagicMock()
        fake_inner.batch.return_value = ["result1", "result2"]
        client._client = fake_inner

        stmts = [
            ("UPDATE t SET x = ? WHERE id = ?", [1, "a"]),
            ("INSERT INTO t (x) VALUES (?)", [2]),
        ]
        result = client.batch(stmts)

        fake_inner.batch.assert_called_once_with(stmts)
        assert result == ["result1", "result2"]

    def test_batch_forwards_arguments_unchanged(self):
        client = TursoClient(url="libsql://fake", auth_token="fake")
        fake_inner = MagicMock()
        client._client = fake_inner

        stmts = [("INSERT INTO t (x) VALUES (?)", [42])]
        client.batch(stmts)

        called_stmts = fake_inner.batch.call_args[0][0]
        assert called_stmts is stmts  # identity, not copy


class TestTursoClientExecuteUnchanged:
    """Guard: adding batch() must not affect existing execute() semantics."""

    def test_unconnected_execute_raises(self):
        client = TursoClient(url="libsql://fake", auth_token="fake")
        with pytest.raises(RuntimeError, match="not connected"):
            client.execute("SELECT 1")

    def test_connected_execute_delegates(self):
        client = TursoClient(url="libsql://fake", auth_token="fake")
        fake_inner = MagicMock()
        client._client = fake_inner

        client.execute("SELECT 1", [])
        fake_inner.execute.assert_called_once_with("SELECT 1", [])