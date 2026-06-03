"""Tests for database.py – SQLite fallback CRUD operations.

Covers: inicializar_banco, salvar_cliente, listar_clientes,
        buscar_cliente_por_chassi, atualizar_cliente, deletar_cliente,
        get_db_connection
"""

import importlib
import os
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def db(monkeypatch, tmp_path):
    """Import database.py in SQLite mode with a temp DB file."""
    # Ensure Supabase is NOT detected
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)

    # Remove cached modules so re-import picks up env changes
    for mod_name in ["database", "database_supabase"]:
        sys.modules.pop(mod_name, None)

    import database

    # Point DB to temp dir
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_NAME", db_path)

    database.inicializar_banco()
    return database


# ------------------------------------------------------------------
# inicializar_banco
# ------------------------------------------------------------------

class TestInicializarBanco:
    def test_creates_tables(self, db):
        import sqlite3

        conn = sqlite3.connect(db.DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        conn.close()

        assert "clientes" in tables
        assert "historico_exclusoes" in tables
        assert "historico_geral" in tables

    def test_idempotent(self, db):
        db.inicializar_banco()  # calling a second time should not raise


# ------------------------------------------------------------------
# salvar_cliente
# ------------------------------------------------------------------

class TestSalvarCliente:
    def test_basic_insert(self, db):
        row_id = db.salvar_cliente({
            "nome": "Tanaka",
            "chassi": "ABC123",
            "veiculo": "Toyota Prius",
        })
        assert row_id is not None and row_id > 0

    def test_duplicate_chassi_raises(self, db):
        db.salvar_cliente({"nome": "A", "chassi": "DUP"})
        with pytest.raises(Exception):
            db.salvar_cliente({"nome": "B", "chassi": "DUP"})

    def test_minimal_fields(self, db):
        row_id = db.salvar_cliente({"nome": "Min"})
        assert row_id is not None


# ------------------------------------------------------------------
# listar_clientes
# ------------------------------------------------------------------

class TestListarClientes:
    def test_empty_table(self, db):
        df = db.listar_clientes()
        assert len(df) == 0

    def test_returns_inserted(self, db):
        db.salvar_cliente({"nome": "Sato", "chassi": "XYZ"})
        db.salvar_cliente({"nome": "Suzuki", "chassi": "QWE"})
        df = db.listar_clientes()
        assert len(df) == 2

    def test_with_where_clause(self, db):
        db.salvar_cliente({"nome": "Find Me", "chassi": "FM1"})
        db.salvar_cliente({"nome": "Other", "chassi": "OT1"})
        df = db.listar_clientes("nome = ?", ("Find Me",))
        assert len(df) == 1
        assert df.iloc[0]["nome"] == "Find Me"


# ------------------------------------------------------------------
# buscar_cliente_por_chassi
# ------------------------------------------------------------------

class TestBuscarClientePorChassi:
    def test_found(self, db):
        db.salvar_cliente({"nome": "Yamada", "chassi": "CH001"})
        result = db.buscar_cliente_por_chassi("CH001")
        assert result is not None
        assert result["nome"] == "Yamada"

    def test_not_found(self, db):
        assert db.buscar_cliente_por_chassi("NOPE") is None


# ------------------------------------------------------------------
# atualizar_cliente
# ------------------------------------------------------------------

class TestAtualizarCliente:
    def test_update_fields(self, db):
        row_id = db.salvar_cliente({"nome": "Old", "chassi": "UP1"})
        db.atualizar_cliente(row_id, {"nome": "New"})
        result = db.buscar_cliente_por_chassi("UP1")
        assert result["nome"] == "New"

    def test_update_multiple_fields(self, db):
        row_id = db.salvar_cliente({"nome": "A", "chassi": "UP2", "veiculo": "Old Car"})
        db.atualizar_cliente(row_id, {"nome": "B", "veiculo": "New Car"})
        result = db.buscar_cliente_por_chassi("UP2")
        assert result["nome"] == "B"
        assert result["veiculo"] == "New Car"


# ------------------------------------------------------------------
# deletar_cliente
# ------------------------------------------------------------------

class TestDeletarCliente:
    def test_delete(self, db):
        row_id = db.salvar_cliente({"nome": "ToDelete", "chassi": "DEL1"})
        db.deletar_cliente(row_id)
        assert db.buscar_cliente_por_chassi("DEL1") is None

    def test_delete_nonexistent(self, db):
        db.deletar_cliente(99999)  # should not raise


# ------------------------------------------------------------------
# get_db_connection
# ------------------------------------------------------------------

class TestGetDbConnection:
    def test_context_manager(self, db):
        with db.get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1

    def test_rollback_on_error(self, db):
        db.salvar_cliente({"nome": "Exists", "chassi": "RB1"})
        try:
            with db.get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO clientes (nome, chassi) VALUES (?, ?)", ("Bad", "RB1"))
        except Exception:
            pass
        result = db.buscar_cliente_por_chassi("RB1")
        assert result["nome"] == "Exists"
