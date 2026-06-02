import os
import json
import base64
import streamlit as st

_SESSION_FILE = os.path.join(os.path.dirname(__file__), ".streamlit", "session.json")
_CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".streamlit", "config.json")

def _save_config(dark_mode, celebration_enabled):
    try:
        with open(_CONFIG_FILE, "w") as f:
            json.dump({"dark_mode": dark_mode, "celebration_enabled": celebration_enabled}, f)
    except Exception:
        pass

def _load_config():
    try:
        with open(_CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"dark_mode": False, "celebration_enabled": True}

def _save_session(usuario, role, nome, lembrar=True):
    try:
        with open(_SESSION_FILE, "w") as f:
            json.dump({"usuario": usuario, "role": role, "nome": nome, "lembrar": lembrar}, f)
    except Exception:
        pass

def _load_session():
    try:
        with open(_SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def _clear_session():
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception:
        pass

def _get_logo_b64():
    path = os.path.join(os.path.dirname(__file__), ".streamlit", "icon_b64.txt")
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return ""

PERMISSIONS = {
    "admin":      {"buscar", "visualizar", "registrar", "editar", "excluir", "desfazer", "status"},
    "secretaria": {"buscar", "visualizar", "registrar", "editar", "excluir", "desfazer", "status"},
    "operador":   {"buscar", "visualizar", "status"},
}

def login_page():
    logo_b64 = _get_logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="width:110px;height:110px;object-fit:contain;border-radius:20px;'
        f'box-shadow:0 4px 24px rgba(16,68,181,0.25);margin-bottom:8px;" />'
    ) if logo_b64 else "🔐"

    st.markdown("""
    <style>
    [data-testid="stSidebarNav"]   { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"]      { display: none !important; }
    [data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    /* Centraliza o bloco de login e limita largura máxima */
    [data-testid="stAppViewContainer"] > section.main > div.block-container {
        max-width: 420px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: clamp(1rem, 8vh, 4rem) !important;
        padding-bottom: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div style="text-align:center;margin-bottom:12px;">{logo_html}</div>',
        unsafe_allow_html=True
    )
    st.markdown("---")
    with st.form("login_form"):
        usuario    = st.text_input("Usuário", autocomplete="off")
        senha      = st.text_input("Senha", type="password", autocomplete="off")
        lembrar    = st.checkbox("Permanecer conectado neste dispositivo", value=False)
        entrar     = st.form_submit_button("Entrar", use_container_width=True)

    if entrar:
        users = st.secrets.get("users", {})
        if usuario in users and users[usuario]["password"] == senha:
            st.session_state.logged_in  = True
            st.session_state.usuario    = usuario
            st.session_state.role       = users[usuario]["role"]
            st.session_state.nome       = users[usuario]["nome"]
            st.session_state.lembrar    = lembrar
            if lembrar:
                _save_session(usuario, users[usuario]["role"], users[usuario]["nome"], True)
            else:
                # Limpa sessao se nao quiser permanecer conectado
                _clear_session()
            # Limpa query params para garantir que sempre vá para página principal
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

def require_login():
    # Processa logout via query param
    if st.query_params.get("logout") == "1":
        st.query_params.clear()
        _clear_session()
        for k in ["logged_in", "usuario", "role", "nome", "lembrar"]:
            st.session_state.pop(k, None)

    # Se nao estiver logado, tenta restaurar sessao salva (soh se marcou "Permanecer conectado")
    if not st.session_state.get("logged_in"):
        saved = _load_session()
        if saved and saved.get("lembrar", False):
            st.session_state.logged_in = True
            st.session_state.usuario   = saved["usuario"]
            st.session_state.role      = saved["role"]
            st.session_state.nome      = saved["nome"]
            st.session_state.lembrar   = True

    if not st.session_state.get("logged_in"):
        login_page()
        st.stop()

def can(permission: str) -> bool:
    role = st.session_state.get("role", "")
    return permission in PERMISSIONS.get(role, set())

def logout_button():
    logo_b64 = _get_logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" style="width:160px;height:160px;object-fit:contain;border-radius:14px;" />'
    ) if logo_b64 else ""

    nome       = st.session_state.get("nome", "")
    role       = st.session_state.get("role", "")
    label      = {"admin": "👑 ", "secretaria": "📋 ", "operador": ""}.get(role, "")
    role_label = {"admin": "管理者", "secretaria": "秘書", "operador": "オーナー"}.get(role, role)

    st.sidebar.markdown(f"""
    <style>
    @keyframes glowPulse {{
        0%   {{ box-shadow: 0 0 18px 6px rgba(100,160,255,0.35); }}
        50%  {{ box-shadow: 0 0 38px 14px rgba(100,200,255,0.55); }}
        100% {{ box-shadow: 0 0 18px 6px rgba(100,160,255,0.35); }}
    }}
    @keyframes glowOrbit {{
        0%   {{ background-position: 0% 50%; }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    .sb-logo-glow {{
        border-radius: 18px;
        background: linear-gradient(270deg, #1044b5, #64c8ff, #0d2a6e, #64c8ff);
        background-size: 400% 400%;
        animation: glowPulse 3s ease-in-out infinite, glowOrbit 6s ease infinite;
        padding: 3px;
        display: inline-block;
    }}
    .sb-logo-glow img {{ display: block; border-radius: 14px; }}
    .sb-header {{
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 18px 0 10px 0;
        gap: 8px;
    }}
    /* Dropdown de logout — CSS puro com checkbox hack */
    #sb-logout-toggle {{ display: none; }}
    #sb-config-toggle {{ display: none; }}
    .sb-user-name {{
        color: #FFFFFF;
        font-size: 1rem;
        font-weight: 700;
        text-align: center;
        cursor: pointer;
        user-select: none;
        display: block;
    }}
    .sb-user-name:hover {{ opacity: 0.85; }}
    .sb-user-role {{
        color: rgba(255,255,255,0.55);
        font-size: 0.78rem;
        text-align: center;
    }}
    .sb-logout-popup {{
        display: none;
        margin-top: 8px;
        text-align: center;
    }}
    #sb-logout-toggle:checked ~ .sb-logout-popup {{ display: block; }}
    .sb-logout-popup a {{
        display: inline-block;
        background: rgba(200,40,40,0.35);
        border: 1px solid rgba(255,80,80,0.5);
        color: #fff !important;
        border-radius: 7px;
        padding: 6px 28px;
        font-size: 0.82rem;
        font-weight: 500;
        text-decoration: none !important;
        margin: 4px 0;
    }}
    .sb-logout-popup a:hover {{ background: rgba(200,40,40,0.65); }}
    .sb-config-btn {{
        display: inline-block;
        background: rgba(100,100,100,0.35);
        border: 1px solid rgba(150,150,150,0.5);
        color: #fff !important;
        border-radius: 7px;
        padding: 6px 28px;
        font-size: 0.82rem;
        font-weight: 500;
        text-decoration: none !important;
        margin: 4px 0;
        cursor: pointer;
    }}
    .sb-config-btn:hover {{ background: rgba(100,100,100,0.65); }}
    .sb-config-btn {{ cursor: pointer; }}
    </style>
    <div class="sb-header">
        <div class="sb-logo-glow">{logo_html}</div>
        <div style="text-align:center;">
            <input type="checkbox" id="sb-logout-toggle">
            <label class="sb-user-name" for="sb-logout-toggle">{label}{nome} ▾</label>
            <div class="sb-user-role">{role_label}</div>
            <div class="sb-logout-popup">
                <a href="?logout=1">⏻ Sair</a>
                <br>
                <a href="?config=1" target="_self" class="sb-config-btn">⚙️ Configurações</a>
            </div>
        </div>
    </div>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.15);margin:8px 0;">
    """, unsafe_allow_html=True)

