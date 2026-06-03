"""Tests for auth.py – config/session persistence and permissions.

Covers: PERMISSIONS, _save_config, _load_config, _save_session,
        _load_session, _clear_session, can
"""

import importlib
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def auth_mod(monkeypatch, tmp_path):
    """Import auth with file paths redirected to a temp directory."""
    sys.modules.pop("auth", None)

    import auth

    # Redirect file paths to tmp_path
    monkeypatch.setattr(auth, "_SESSION_FILE", str(tmp_path / "session.json"))
    monkeypatch.setattr(auth, "_CONFIG_FILE", str(tmp_path / "config.json"))

    return auth


# ------------------------------------------------------------------
# PERMISSIONS
# ------------------------------------------------------------------

class TestPermissions:
    def test_admin_has_all(self, auth_mod):
        expected = {"buscar", "visualizar", "registrar", "editar", "excluir", "desfazer", "status"}
        assert auth_mod.PERMISSIONS["admin"] == expected

    def test_secretaria_matches_admin(self, auth_mod):
        assert auth_mod.PERMISSIONS["secretaria"] == auth_mod.PERMISSIONS["admin"]

    def test_operador_limited(self, auth_mod):
        assert auth_mod.PERMISSIONS["operador"] == {"buscar", "visualizar", "status"}

    def test_operador_cannot_edit(self, auth_mod):
        assert "editar" not in auth_mod.PERMISSIONS["operador"]

    def test_unknown_role_empty(self, auth_mod):
        assert auth_mod.PERMISSIONS.get("unknown", set()) == set()


# ------------------------------------------------------------------
# _save_config / _load_config
# ------------------------------------------------------------------

class TestConfig:
    def test_save_and_load(self, auth_mod):
        auth_mod._save_config(True, False)
        result = auth_mod._load_config()
        assert result["dark_mode"] is True
        assert result["celebration_enabled"] is False

    def test_load_default_when_missing(self, auth_mod):
        result = auth_mod._load_config()
        assert result == {"dark_mode": False, "celebration_enabled": True}

    def test_save_overwrites(self, auth_mod):
        auth_mod._save_config(False, True)
        auth_mod._save_config(True, True)
        result = auth_mod._load_config()
        assert result["dark_mode"] is True

    def test_load_corrupt_file_returns_default(self, auth_mod):
        with open(auth_mod._CONFIG_FILE, "w") as f:
            f.write("not json")
        result = auth_mod._load_config()
        assert result == {"dark_mode": False, "celebration_enabled": True}


# ------------------------------------------------------------------
# _save_session / _load_session / _clear_session
# ------------------------------------------------------------------

class TestSession:
    def test_save_and_load(self, auth_mod):
        auth_mod._save_session("admin", "admin", "Admin User", True)
        result = auth_mod._load_session()
        assert result["usuario"] == "admin"
        assert result["role"] == "admin"
        assert result["nome"] == "Admin User"
        assert result["lembrar"] is True

    def test_load_returns_none_when_no_file(self, auth_mod):
        assert auth_mod._load_session() is None

    def test_clear_session(self, auth_mod):
        auth_mod._save_session("user", "operador", "User", False)
        assert auth_mod._load_session() is not None
        auth_mod._clear_session()
        assert auth_mod._load_session() is None

    def test_clear_session_no_file(self, auth_mod):
        auth_mod._clear_session()  # should not raise

    def test_save_session_without_lembrar(self, auth_mod):
        auth_mod._save_session("user", "operador", "User", False)
        result = auth_mod._load_session()
        assert result["lembrar"] is False


# ------------------------------------------------------------------
# can
# ------------------------------------------------------------------

class TestCan:
    def test_admin_can_edit(self, auth_mod, monkeypatch):
        st = sys.modules["streamlit"]
        st.session_state = {"role": "admin"}
        assert auth_mod.can("editar") is True

    def test_operador_cannot_edit(self, auth_mod, monkeypatch):
        st = sys.modules["streamlit"]
        st.session_state = {"role": "operador"}
        assert auth_mod.can("editar") is False

    def test_operador_can_buscar(self, auth_mod, monkeypatch):
        st = sys.modules["streamlit"]
        st.session_state = {"role": "operador"}
        assert auth_mod.can("buscar") is True

    def test_no_role(self, auth_mod, monkeypatch):
        st = sys.modules["streamlit"]
        st.session_state = {}
        assert auth_mod.can("buscar") is False

    def test_unknown_permission(self, auth_mod, monkeypatch):
        st = sys.modules["streamlit"]
        st.session_state = {"role": "admin"}
        assert auth_mod.can("nonexistent") is False
