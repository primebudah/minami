"""Shared fixtures and mocks for all test modules."""

import sys
import types
from unittest.mock import MagicMock

import pytest


class _FakeSecrets(dict):
    """A dict subclass whose .get() returns *default* for missing keys
    and also supports attribute access (``st.secrets["KEY"]``)."""

    def get(self, key, default=""):
        if key in self:
            return self[key]
        return default


@pytest.fixture(autouse=True)
def _mock_streamlit(monkeypatch):
    """Provide a lightweight streamlit stub so modules that do
    ``import streamlit as st`` at the top level don't fail."""
    fake_st = types.ModuleType("streamlit")
    fake_st.secrets = _FakeSecrets()
    fake_st.session_state = {}
    fake_st.markdown = MagicMock()
    fake_st.warning = MagicMock()
    fake_st.error = MagicMock()
    fake_st.stop = MagicMock()
    fake_st.rerun = MagicMock()
    fake_st.query_params = MagicMock()
    fake_st.sidebar = MagicMock()
    fake_st.form = MagicMock()
    fake_st.text_input = MagicMock()
    fake_st.checkbox = MagicMock()
    fake_st.form_submit_button = MagicMock()

    fake_components = types.ModuleType("streamlit.components")
    fake_v1 = types.ModuleType("streamlit.components.v1")
    fake_components.v1 = fake_v1
    fake_st.components = fake_components

    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setitem(sys.modules, "streamlit.components", fake_components)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", fake_v1)
