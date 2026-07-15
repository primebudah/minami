# =========================================================
# IMPORTS
# =========================================================

import os
from datetime import date
import re

import pandas as pd
import streamlit as st

from database import inicializar_banco, salvar_cliente, listar_clientes, atualizar_cliente, deletar_cliente, desfazer_ultima_acao
from ocr_service import extrair_dados_do_documento, converter_data_japonesa, traduzir_veiculo
from ui_base import inject_base_css
from auth import require_login, can, logout_button, _load_config

# =========================================================
# CONFIG
# =========================================================

# Carrega ícone da logo
_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "icon_b64.txt")
_page_icon = "🚗"
try:
    with open(_icon_path, "r") as f:
        _icon_data = f.read().strip()
        if _icon_data:
            _page_icon = f"data:image/png;base64,{_icon_data}"
except:
    pass

st.set_page_config("Central Shaken - Registros", layout="wide", initial_sidebar_state="expanded", page_icon=_page_icon)
inject_base_css()

# Meta tags para PWA
st.markdown(f"""
<meta name="application-name" content="Central Shaken">
<meta name="apple-mobile-web-app-title" content="Central Shaken">
<meta name="theme-color" content="#0d2a6e">
<link rel="shortcut icon" href="{_page_icon}" type="image/png">
""", unsafe_allow_html=True)

require_login()

inicializar_banco()

def _norm_chassi(valor):
    v = "" if valor is None else str(valor).strip()
    if not v or v.lower() in ("nan", "none", "null"):
        return ""
    if "NÃO IDENTIFICADO" in v.upper() or "VERIFICAR" in v.upper():
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", v).upper()

def _chassi_canonico(row_dict):
    simples = _norm_chassi(row_dict.get("chassi", ""))
    completo = _norm_chassi(row_dict.get("chassi_completo", ""))
    return simples or completo

def _chassi_visivel(row_dict):
    return _norm_chassi(row_dict.get("chassi", ""))

def _chassi_visivel_exato(row_dict):
    v = "" if row_dict.get("chassi") is None else str(row_dict.get("chassi")).strip()
    if not v or v.lower() in ("nan", "none", "null"):
        return ""
    if "NÃO IDENTIFICADO" in v.upper() or "VERIFICAR" in v.upper():
        return ""
    return re.sub(r"\s+", "", v).upper()

def _chassis_existentes_canonicos(df_existente):
    chassis = set()
    if df_existente is not None and not df_existente.empty:
        if "chassi_completo" in df_existente.columns:
            chassis.update(_norm_chassi(c) for c in df_existente["chassi_completo"].dropna())
        if "chassi" in df_existente.columns:
            chassis.update(_norm_chassi(c) for c in df_existente["chassi"].dropna())
    chassis.discard("")
    return chassis

def _indices_duplicados_na_fila(registros):
    vistos = {}
    duplicados = {}
    for idx, reg in enumerate(registros):
        chassi = _chassi_visivel_exato(reg)
        if len(chassi) >= 5:
            if chassi in vistos:
                duplicados[idx] = chassi
            else:
                vistos[chassi] = idx
    return duplicados

def _assinatura_chassis_visiveis(registros):
    return tuple(_chassi_visivel(reg) for reg in registros)

# Carrega configurações de modo escuro
config = _load_config()
dark_mode = config.get("dark_mode", False)

# Aplica CSS para modo escuro (sidebar continua azul)
if dark_mode:
    st.markdown("""
    <style>
    /* Modo escuro - apenas conteúdo principal, sidebar continua azul */
    .stApp {
        background-color: #1a1a2e !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #1a1a2e !important;
    }
    [data-testid="stMain"] {
        background-color: #1a1a2e !important;
    }
    /* Tabelas em modo escuro */
    .stDataFrame {
        background-color: #16213e !important;
        color: #eaeaea !important;
    }
    .stDataFrame [data-testid="stDataFrame"] {
        background-color: #16213e !important;
    }
    .stDataFrame [data-testid="stDataFrame"] thead th {
        background-color: #0f3460 !important;
        color: #eaeaea !important;
        border-bottom: 2px solid #e94560 !important;
    }
    .stDataFrame [data-testid="stDataFrame"] tbody tr {
        background-color: #16213e !important;
        color: #eaeaea !important;
        border-bottom: 1px solid #0f3460 !important;
    }
    .stDataFrame [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #1a1a2e !important;
    }
    /* Inputs e campos de texto */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #87ceeb !important;
        color: #1a1a2e !important;
    }
    /* Botões */
    .stButton > button {
        background-color: #1044b5 !important;
        color: #ffffff !important;
    }
    .stButton > button *,
    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stFormSubmitButton"] button * {
        color: #ffffff !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        background-color: #1044b5 !important;
        border-color: #1044b5 !important;
    }
    .stButton > button:hover {
        background-color: #0d2a6e !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #0d2a6e !important;
        border-color: #0d2a6e !important;
    }
    /* File uploader - botão e texto visível */
    div[data-testid="stFileUploader"] button {
        background-color: #1044b5 !important;
        color: #ffffff !important;
        border-color: #1044b5 !important;
    }
    div[data-testid="stFileUploader"] button * {
        color: #ffffff !important;
    }
    div[data-testid="stFileUploader"] button:hover {
        background-color: #0d2a6e !important;
        border-color: #0d2a6e !important;
    }
    div[data-testid="stFileUploader"] {
        color: #eaeaea !important;
    }
    div[data-testid="stFileUploader"] span {
        color: #eaeaea !important;
    }
    div[data-testid="stFileUploader"] p {
        color: #eaeaea !important;
    }
    div[data-testid="stFileUploader"] label {
        color: #eaeaea !important;
    }
    div[data-testid="stFileUploader"] small {
        color: #87ceeb !important;
    }
    /* Alertas */
    div[data-testid="stAlert"],
    div[data-testid="stAlert"] *,
    div[data-baseweb="notification"],
    div[data-baseweb="notification"] * {
        color: #ffffff !important;
    }
    div[data-testid="stAlert"] {
        background-color: #0f3460 !important;
        border: 1px solid #87ceeb !important;
        border-radius: 8px !important;
    }
    .reg-alert-box,
    .reg-alert-box *,
    .reg-dup-alert,
    .reg-dup-alert * {
        color: #ffffff !important;
    }
    .reg-alert-box,
    .reg-dup-alert {
        background: #0f3460 !important;
        border-left: 4px solid #87ceeb !important;
        border-radius: 8px !important;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #0f3460 !important;
        color: #eaeaea !important;
    }
    /* Texto geral */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #eaeaea !important;
    }
    /* Sidebar mantém azul (sobrescreve modo escuro) */
    [data-testid="stSidebar"] {
        background-color: #1044b5 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #1044b5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def _validar_campo_obrigatorio(valor, nome_campo):
    """Valida campo obrigatório"""
    if not valor or not str(valor).strip():
        return False, f"{nome_campo} é obrigatório", False
    return True, "", True

def _validar_contato_form(valor):
    """Valida contato japonês"""
    if not valor or not str(valor).strip():
        return True, "", True  # Opcional
    v = re.sub(r"[\s\-\(\)]", "", str(valor))
    # Padrão japonês: 0[7-9]0 + 8 dígitos OU 0 + 9-10 dígitos
    if re.match(r"^0[789]0\d{8}$", v) or re.match(r"^0\d{9,10}$", v):
        return True, "", True
    return False, "Atenção: Contato fora do padrão (ex: 09012345678)", True

def _validar_data_form(valor, nome_campo):
    """Valida data no formato japonês ou ISO"""
    if not valor or not str(valor).strip():
        return True, "", True  # Opcional
    v = str(valor).strip()
    # AAAAMMDD
    if re.match(r"^\d{8}$", v):
        return True, "", True
    # DD/MM/AAAA ou DD-MM-AAAA
    if re.match(r"^\d{2}[/-]\d{2}[/-]\d{4}$", v):
        return True, "", True
    # AAAA-MM-DD (ISO)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        return True, "", True
    return False, f"{nome_campo} inválida. Use DD/MM/AAAA ou AAAAMMDD", True

def _validar_chassi_form(valor, df_existente=None):
    """Valida chassi no formulário. Retorna (ok, msg, pode_ignorar)"""
    if not valor or not str(valor).strip():
        return False, "Chassi é obrigatório", False
    v = str(valor).strip()
    # Padrão mínimo
    if not re.match(r"^[A-Za-z0-9\-]{5,}$", v):
        return False, "Chassi fora do padrão (mín. 5 caracteres alfanuméricos)", True
    # Duplicado
    if df_existente is not None:
        _ch = v.lower()
        _existe = any(str(c).strip().lower() == _ch for c in df_existente["chassi"].dropna())
        if _existe:
            return False, "Chassi já existe no banco", False
    return True, "", True

if not can("registrar"):
    st.warning("⚠️ Esta página é apenas para admin/secretaria. Redirecionando para a página principal...")
    st.switch_page("app.py")

st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d2a6e 0%, #1044b5 60%, #0a1f5c 100%) !important;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] details summary {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] details summary:hover,
[data-testid="stSidebar"] details summary:focus,
[data-testid="stSidebar"] details[open] summary {
    background: rgba(255,255,255,0.08) !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] details > div {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 0 0 8px 8px !important;
}
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] button:hover,
[data-testid="stSidebar"] button:focus,
[data-testid="stSidebar"] button:active {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "fila_registros" not in st.session_state:
    st.session_state.fila_registros = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "fila_delete_mode" not in st.session_state:
    st.session_state.fila_delete_mode = False

if "fila_linhas_excluidas" not in st.session_state:
    st.session_state.fila_linhas_excluidas = []

if "_fila_editor_v" not in st.session_state:
    st.session_state._fila_editor_v = 0

if "fila_ultima_edicao" not in st.session_state:
    st.session_state.fila_ultima_edicao = None

if "_reg_duplicados_persistente" not in st.session_state:
    st.session_state._reg_duplicados_persistente = []

# Session state para validação em tempo real do formulário
if "_form_chassi_aviso" not in st.session_state:
    st.session_state._form_chassi_aviso = None
if "_form_nome_aviso" not in st.session_state:
    st.session_state._form_nome_aviso = None
if "_form_veiculo_aviso" not in st.session_state:
    st.session_state._form_veiculo_aviso = None
if "_form_contato_aviso" not in st.session_state:
    st.session_state._form_contato_aviso = None
if "_form_shaken_aviso" not in st.session_state:
    st.session_state._form_shaken_aviso = None
if "_form_data_aviso" not in st.session_state:
    st.session_state._form_data_aviso = None

if "_reg_salvos_count" not in st.session_state:
    st.session_state._reg_salvos_count = 0

# Sistema de avisos de validação (OK + Salvar mesmo assim)
if "_reg_aviso" not in st.session_state:
    st.session_state._reg_aviso = None

if "_reg_salvar_mesmo_assim" not in st.session_state:
    st.session_state._reg_salvar_mesmo_assim = False

# Controle de fluxo para confirmação do contato
if "_form_dados_pendentes" not in st.session_state:
    st.session_state._form_dados_pendentes = None  # Guarda dados quando espera confirmação
if "_form_etapa" not in st.session_state:
    st.session_state._form_etapa = "preencher"  # "preencher", "confirmar_contato", "concluido"

# Limpa keys antigas do formulário que podem estar causando problemas
for key in ["nome", "veiculo", "chassi", "contato"]:
    if key in st.session_state:
        del st.session_state[key]

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<style>
.nav-btn-active {
    background: linear-gradient(135deg, #1044b5, #0d2a6e) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(16,68,181,0.35) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    cursor: default !important;
}
div[data-testid="stColumns"] > div:nth-child(3) button {
    background: linear-gradient(135deg, #1044b5, #0d2a6e) !important;
    color: #FFFFFF !important;
    border: none !important;
    cursor: default !important;
}
[data-testid="stTextInput"] input {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

_nav_cols = st.columns([1, 0.5, 0.5, 1])
with _nav_cols[1]:
    if st.button("🔍 Central Shaken", key="nav_home", use_container_width=True):
        st.switch_page("app.py")
with _nav_cols[2]:
    st.button("📋 Registrar", key="nav_reg", disabled=True, use_container_width=True)

st.caption("Adicione registros manualmente ou via foto. Confira a fila e clique em **Salvar Registros** para enviar à tabela principal.")
st.divider()

# =========================================================
# FORMULÁRIOS LADO A LADO
# =========================================================

col_manual, col_foto = st.columns(2)

# ---------- REGISTRO MANUAL ----------
with col_manual:
    with st.expander("📝 Registro Manual", expanded=False):
        # Versionador para limpar form quando necessário
        if "_form_v" not in st.session_state:
            st.session_state._form_v = 0
        if st.session_state.get("_limpar_form", False):
            st.session_state._form_v += 1
            st.session_state._limpar_form = False
        
        # Inicializa valores no session_state se não existirem
        _form_key = f"manual_{st.session_state._form_v}"
        for _campo, _default in [("nome", ""), ("veiculo", ""), ("placa", ""), ("chassi", ""), ("contato", "")]:
            if f"{_form_key}_{_campo}" not in st.session_state:
                st.session_state[f"{_form_key}_{_campo}"] = _default
        if f"{_form_key}_shaken" not in st.session_state:
            st.session_state[f"{_form_key}_shaken"] = date.today().replace(year=date.today().year + 2)
        if f"{_form_key}_data_reg" not in st.session_state:
            st.session_state[f"{_form_key}_data_reg"] = date.today().strftime("%d/%m/%Y")
        
        with st.form(_form_key, clear_on_submit=False):
            # Usa session_state como fallback quando variável local não existe
            nome    = st.text_input("Nome", key=f"{_form_key}_nome", autocomplete="off")
            veiculo = st.text_input("Veículo", key=f"{_form_key}_veiculo", autocomplete="off")
            placa   = st.text_input("Placa", key=f"{_form_key}_placa", autocomplete="off")
            chassi  = st.text_input("Chassi", key=f"{_form_key}_chassi", autocomplete="off")
            contato = st.text_input("Contato", key=f"{_form_key}_contato", autocomplete="off")
            
            shaken  = st.date_input("Vencimento Shaken", key=f"{_form_key}_shaken")
            data_reg_raw = st.text_input("Data de Registro", key=f"{_form_key}_data_reg", autocomplete="off")

            submitted = st.form_submit_button("➕ Adicionar à fila")
        
        # Adiciona direto na fila - validação será feita na conferência
        if submitted:
                _dr = data_reg_raw.strip()
                _dr_clean = _dr.replace("/", "").replace("-", "")
                if len(_dr_clean) == 8 and _dr_clean.isdigit():
                    if int(_dr_clean[:4]) > 1900:
                        data_reg = f"{_dr_clean[:4]}-{_dr_clean[4:6]}-{_dr_clean[6:8]}"
                    else:
                        data_reg = f"{_dr_clean[4:8]}-{_dr_clean[2:4]}-{_dr_clean[:2]}"
                else:
                    data_reg = str(date.today())
                registro = {
                    "nome": nome,
                    "contato": contato,
                    "shaken_vencimento": str(shaken),
                    "veiculo": traduzir_veiculo(veiculo),
                    "chassi": chassi,
                    "data_registro": data_reg,
                    "_origem": "manual"
                }
                st.session_state.fila_registros.append(registro)
                st.session_state._fila_editor_v += 1
                # Limpa flag após adicionar com sucesso
                st.session_state._confirma_aviso = False
                st.success(f"'{nome}' adicionado à fila.")
                st.session_state._limpar_form = True
                st.rerun()

# ---------- TELA DE CONFIRMAÇÃO (quando contato inválido) ----------
if st.session_state._form_etapa == "confirmar_contato" and st.session_state._form_dados_pendentes:
    st.divider()
    st.warning("⚠️ Atenção: Contato fora do padrão japonês!")
    st.write(f"Contato digitado: **{st.session_state._form_dados_pendentes['contato']}**")
    st.write("Deseja corrigir ou salvar assim mesmo?")
    
    col_ok, col_ignorar = st.columns([1, 1])
    
    with col_ok:
        if st.button("✅ OK, corrigir", use_container_width=True, key="btn_ok_contato"):
            # Volta para etapa de preenchimento (mantém dados no form via rerun)
            st.session_state._form_etapa = "preencher"
            st.session_state._form_dados_pendentes = None
            st.rerun()
    
    with col_ignorar:
        if st.button("➕ Salvar mesmo assim", use_container_width=True, key="btn_salvar_contato"):
            # Muda para etapa concluído e processa o envio
            st.session_state._form_etapa = "concluido"
            st.rerun()
    
    st.stop()  # Não mostra mais nada até resolver

# Quando está na etapa concluido, processa o envio
if st.session_state._form_etapa == "concluido" and st.session_state._form_dados_pendentes:
    # Recupera dados pendentes
    _dados = st.session_state._form_dados_pendentes
    _dr_raw = _dados["data_reg_raw"].strip()
    _dr_clean = _dr_raw.replace("/", "").replace("-", "")
    if len(_dr_clean) == 8 and _dr_clean.isdigit():
        if int(_dr_clean[:4]) > 1900:
            data_reg = f"{_dr_clean[:4]}-{_dr_clean[4:6]}-{_dr_clean[6:8]}"
        else:
            data_reg = f"{_dr_clean[4:8]}-{_dr_clean[2:4]}-{_dr_clean[:2]}"
    else:
        data_reg = str(date.today())
    
    registro = {
        "nome": _dados["nome"],
        "contato": _dados["contato"],
        "shaken_vencimento": str(_dados["shaken"]),
        "veiculo": traduzir_veiculo(_dados["veiculo"]),
        "chassi": _dados["chassi"],
        "data_registro": data_reg,
        "_origem": "manual"
    }
    st.session_state.fila_registros.append(registro)
    st.success(f"'{_dados['nome']}' adicionado à fila (com contato não validado).")
    
    # Reseta para próximo e limpa form
    st.session_state._form_etapa = "preencher"
    st.session_state._limpar_form = True
    st.session_state._form_dados_pendentes = None
    st.rerun()

# ---------- REGISTRO POR FOTO ----------
with col_foto:
    with st.expander("📸 Registro por Foto", expanded=False):
        st.caption("📱 Selecione até **10 fotos por vez**. Pode repetir várias vezes — todas vão para a fila.")
        files = st.file_uploader(
            "Selecione até 10 fotos",
            accept_multiple_files=True,
            type=["jpg", "jpeg", "png"],
            key=f"uploader_{st.session_state.get('uploader_key', 0)}"
        )

        if files:
            # Limita a 10 fotos
            if len(files) > 10:
                st.warning(f"⚠️ Você selecionou {len(files)} fotos. O limite é 10 fotos por vez. Processando apenas as 10 primeiras.")
                files = files[:10]
            st.write(f"**{len(files)} foto(s) selecionada(s):**")
            for f in files:
                st.write(f"📄 {f.name}")

            if st.button("🔍 Processar Fotos"):
                ok, err = 0, 0
                progress = st.progress(0)
                status = st.empty()
                total = len(files)
                with st.spinner("Processando fotos..."):
                    for idx, f in enumerate(files, start=1):
                        status.info(f"Processando {idx}/{total}: {f.name}")
                        try:
                            d = extrair_dados_do_documento(f)
                            if not d or (not d.get("chassi") and not d.get("veiculo")):
                                status.warning(f"⚠️ {idx}/{total}: {f.name} - não foi possível ler dados essenciais")
                                err += 1
                                continue
                            if d.get("data_registro"):
                                dr = d["data_registro"]
                                if re.match(r"^\d{4}-\d{2}-\d{2}$", dr):
                                    if not (1900 <= int(dr[:4]) <= 2100):
                                        d["data_registro"] = str(date.today())
                            d["_origem"] = f"foto:{f.name}"
                            st.session_state.fila_registros.append(d)
                            ok += 1
                            status.success(f"✅ {idx}/{total}: {f.name} processada")
                        except Exception as e:
                            st.error(f"Erro em {f.name}: {e}")
                            err += 1
                        progress.progress(idx / total)
                status.empty()
                if ok:
                    st.success(f"{ok} foto(s) processada(s) e adicionada(s) à fila.")
                if err:
                    st.warning(f"{err} erro(s).")
                if ok:
                    st.session_state._fila_editor_v += 1
                    st.session_state.uploader_key = st.session_state.get('uploader_key', 0) + 1
                st.rerun()

# =========================================================
# FILA DE REGISTROS PENDENTES
# =========================================================

st.divider()

# ── Notificações pós-salvamento ──────────────────────────
_salvos_count = st.session_state.get("_reg_salvos_count", 0)
_dups_persist = st.session_state.get("_reg_duplicados_persistente", [])

# Sincroniza: remove duplicados que já foram excluídos da fila
if _dups_persist:
    _chassi_fila = {_chassi_canonico(r) for r in st.session_state.fila_registros}
    _chassi_fila.discard("")
    _dups_persist = [d for d in _dups_persist if _chassi_canonico(d) in _chassi_fila]
    st.session_state._reg_duplicados_persistente = _dups_persist

if _salvos_count > 0:
    _sc1, _sc2 = st.columns([10, 1])
    with _sc1:
        st.success(f"✅ {_salvos_count} registro(s) salvo(s) com sucesso na tabela principal!")
    with _sc2:
        if st.button("OK", key="ok_salvos"):
            st.session_state._reg_salvos_count = 0
            st.rerun()

if _dups_persist:
    _msgs = "".join(
        f"<li><b>{d.get('nome','—')}</b> — chassi <b>{d.get('chassi','—')}</b></li>"
        for d in _dups_persist
    )
    st.markdown(f"""
    <div class='reg-dup-alert' style='padding:10px 14px;margin-bottom:4px;background:#fff3cd;
                border-left:4px solid #dc7800;border-radius:8px;font-size:0.85rem;color:#7a4500;'>
      <b>⚠️ {len(_dups_persist)} registro(s) já constam na tabela principal e não foram salvos:</b>
      <ul style='margin:6px 0 0 0;padding-left:18px;color:#7a4500'>{_msgs}</ul>
      <span style='color:#a05800;font-size:0.78rem;'>
        As linhas duplicadas permanecem na fila abaixo para exclusão manual.
      </span>
    </div>""", unsafe_allow_html=True)
    if st.button("OK — entendido", key="ok_dups"):
        st.session_state._reg_duplicados_persistente = []
        st.rerun()

# ── Aviso de registros com erros que ficaram na fila ─────
_com_erros = st.session_state.get("_reg_com_erros", [])
if _com_erros:
    st.warning(f"⚠️ {len(_com_erros)} registro(s) com erro permanecem na fila para correção:")
    for item in _com_erros:
        reg = item["reg"]
        probs = item.get("probs", [])
        prob_str = "; ".join([p[1] for p in probs]) if probs else "Erro de validação"
        st.write(f"• **{reg.get('nome','—')}** — {prob_str}")
    if st.button("OK — entendido", key="ok_erros"):
        st.session_state._reg_com_erros = []
        st.rerun()

st.subheader(f"🗂️ Fila de Registros Pendentes  ({len(st.session_state.fila_registros)})")

if not st.session_state.fila_registros:
    st.info("Nenhum registro na fila. Adicione manualmente ou via foto acima.")
else:
    # ── Botões de ação fixos ──────────────────────────────
    _ac1, _ac2 = st.columns([1, 1])

    with _ac1:
        _lbl_del = "✅ Modo Exclusão ON" if st.session_state.fila_delete_mode else "🗑️ Modo Exclusão"
        if st.button(_lbl_del, use_container_width=True):
            st.session_state.fila_delete_mode = not st.session_state.fila_delete_mode
            st.rerun()

    with _ac2:
        if st.session_state.fila_delete_mode:
            st.session_state._fila_excluir_btn = st.button("❌ Excluir Selecionados", type="primary", use_container_width=True)



    # ── Tabela editável da fila ───────────────────────────
    df_fila = pd.DataFrame(st.session_state.fila_registros)
    colunas_exibir = ["nome", "veiculo", "placa", "chassi", "contato", "shaken_vencimento", "data_registro"]
    colunas_presentes = [c for c in colunas_exibir if c in df_fila.columns]
    df_fila_view = df_fila[colunas_presentes].copy()
    df_fila_view.index = range(1, len(df_fila_view) + 1)

    def _col_width(col, label):
        try:
            if col in df_fila_view.columns and not df_fila_view.empty:
                lengths = df_fila_view[col].dropna().astype(str).str.len()
                max_data = int(lengths.max()) if not lengths.empty else 0
            else:
                max_data = 0
        except Exception:
            max_data = 0
        return max(50, min(350, int(max(max_data, len(label)) * 11) + 16))

    if st.session_state.fila_delete_mode:
        df_fila_view.insert(0, "Apagar", [False] * len(df_fila_view))

    _col_cfg = {
        "nome":              st.column_config.TextColumn("Nome", width=_col_width("nome", "Nome")),
        "veiculo":           st.column_config.TextColumn("Veículo", width=_col_width("veiculo", "Veículo")),
        "placa":             st.column_config.TextColumn("Placa", width=_col_width("placa", "Placa")),
        "chassi":            st.column_config.TextColumn("Chassi", width=_col_width("chassi", "Chassi")),
        "contato":           st.column_config.TextColumn("Contato", width=_col_width("contato", "Contato")),
        "shaken_vencimento": st.column_config.TextColumn("Venc. Shaken", width=_col_width("shaken_vencimento", "Venc. Shaken")),
        "data_registro":     st.column_config.TextColumn("Data Registro", width=_col_width("data_registro", "Data Registro")),
    }
    if st.session_state.fila_delete_mode:
        _col_cfg["Apagar"] = st.column_config.CheckboxColumn("🗑️", default=False)

    editor_fila = st.data_editor(
        df_fila_view,
        use_container_width=True,
        num_rows="fixed",
        key=f"editor_fila_{st.session_state._fila_editor_v}",
        column_config=_col_cfg,
        disabled=False
    )

    # Atualiza registros da fila com valores do editor (edição simples)
    # Processa TODAS as edições antes de qualquer validação
    _houve_edicao = False
    editor_dict = editor_fila.to_dict("records")
    
    # Primeiro, aplica todas as edições ao session_state
    for i, row in enumerate(editor_dict):
        for col in colunas_presentes:
            v_new = str(row.get(col, "") or "")
            v_atual = str(st.session_state.fila_registros[i].get(col, "") or "")
            if v_new != v_atual:
                st.session_state.fila_registros[i][col] = v_new
                if col == "chassi":
                    st.session_state.fila_registros[i]["chassi_completo"] = v_new
                _houve_edicao = True
    
    # Limpa aviso de validação se houve edição
    if _houve_edicao:
        st.session_state._reg_aviso = None
        st.session_state._reg_duplicados_persistente = []

    _assinatura_atual = _assinatura_chassis_visiveis(st.session_state.fila_registros)
    if st.session_state.get("_reg_aviso") and st.session_state._reg_aviso.get("assinatura_chassis") != _assinatura_atual:
        st.session_state._reg_aviso = None

    # Processa exclusão selecionada
    if st.session_state.fila_delete_mode and st.session_state.get("_fila_excluir_btn"):
        excluidos = []
        mantidos = []
        for i, row in enumerate(editor_fila.to_dict("records")):
            if row.get("Apagar", False):
                excluidos.append(st.session_state.fila_registros[i])
            else:
                mantidos.append(st.session_state.fila_registros[i])
        if excluidos:
            st.session_state.fila_linhas_excluidas.append(excluidos)
        st.session_state.fila_registros = mantidos
        st.session_state._fila_editor_v += 1
        st.session_state._reg_aviso = None
        st.session_state._reg_duplicados_persistente = []
        st.session_state.fila_delete_mode = False
        st.session_state._fila_excluir_btn = False
        st.rerun()

    # ── Função de salvamento parcial ─────────────────────
    def _executar_salvamento_parcial():
        """Salva registros válidos na principal, mantém com erros na fila."""
        _df_existente = listar_clientes()
        _chassis_existentes = _chassis_existentes_canonicos(_df_existente)
        _registros_visiveis = editor_fila.to_dict("records")
        _indices_duplicados_fila = _indices_duplicados_na_fila(_registros_visiveis)
        
        # Re-valida para montar mapa de problemas
        _todos_problemas = []
        for i, reg in enumerate(_registros_visiveis):
            _probs = _validar_registro(reg, i, _chassis_existentes, _indices_duplicados_fila)
            _todos_problemas.extend(_probs)
        
        _mapa_problemas = {}
        for emoji, msg in _todos_problemas:
            import re
            m = re.search(r"Registro (\d+)", msg)
            if m:
                idx = int(m.group(1)) - 1
                _mapa_problemas.setdefault(idx, []).append((emoji, msg))
        
        salvos = 0
        com_erros = []
        fila_restante = []
        _chassis_ja_vistos = set()
        
        for i, row in enumerate(editor_fila.to_dict("records")):
            registro = _registros_visiveis[i].copy()
            for col in colunas_presentes:
                val = row[col]
                if col in ("data_registro", "shaken_vencimento"):
                    raw = str(val).strip().replace("-", "").replace("/", "")
                    if len(raw) == 8 and raw.isdigit():
                        val = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                if col == "veiculo":
                    val = traduzir_veiculo(str(val))
                registro[col] = val
            
            _probs_do_reg = _mapa_problemas.get(i, [])
            _tem_erro = any(e == "🔴" for e, _ in _probs_do_reg)
            _chassi = _chassi_canonico(registro)
            _dup_banco = _chassi and _chassi in _chassis_existentes
            _dup_fila = i in _indices_duplicados_fila
            _dup_loop = _chassi and _chassi in _chassis_ja_vistos
            
            if _tem_erro or _dup_banco or _dup_fila or _dup_loop:
                com_erros.append({"reg": registro, "idx": i, "probs": _probs_do_reg})
                fila_restante.append(st.session_state.fila_registros[i])
            else:
                registro.pop("_origem", None)
                salvar_cliente(registro)
                salvos += 1
                if _chassi:
                    _chassis_ja_vistos.add(_chassi)
        
        st.session_state.fila_registros = fila_restante
        st.session_state._fila_editor_v += 1
        st.session_state._reg_salvos_count = salvos
        st.session_state._reg_com_erros = com_erros
        if "df" in st.session_state:
            del st.session_state["df"]
    
    # ── Função de validação (Parte 1) ─────────────────────
    def _validar_registro(row_dict, idx, chassis_existentes, indices_duplicados_fila):
        """Valida um registro e retorna lista de problemas."""
        _probs = []
        _nome = str(row_dict.get("nome", "")).strip()
        _veiculo = str(row_dict.get("veiculo", "")).strip()
        _chassi = str(row_dict.get("chassi", "")).strip()
        _contato = str(row_dict.get("contato", "")).strip()
        _shaken = str(row_dict.get("shaken_vencimento", "")).strip()
        _data_reg = str(row_dict.get("data_registro", "")).strip()
        
        # Campos obrigatórios
        _faltando = []
        if not _nome: _faltando.append("Nome")
        if not _veiculo: _faltando.append("Veículo")
        if not _chassi: _faltando.append("Chassi")
        if _faltando:
            _probs.append(("🔴", f"Registro {idx+1}: faltam {', '.join(_faltando)}"))
        
        # Data inválida
        for _campo, _lbl, _val in [("shaken_vencimento", "Shaken", _shaken), ("data_registro", "Registro", _data_reg)]:
            if _val:
                _raw = _val.replace("-", "").replace("/", "")
                if "VERIFICAR" in _val:
                    _probs.append(("🟡", f"Registro {idx+1} ({_lbl}): data requer verificação manual"))
                elif not (len(_raw) == 8 and _raw.isdigit()):
                    _probs.append(("🟡", f"Registro {idx+1} ({_lbl}): data inválida"))
        
        # Chassi duplicado no banco - usa chassi completo quando disponível
        if _chassi:
            _ch_para_comparar = _chassi_canonico(row_dict)
            _ch_visivel = _chassi_visivel(row_dict)
            _ch_visivel_exato = _chassi_visivel_exato(row_dict)
            _pode_comparar_chassi = len(_ch_para_comparar) >= 5
            _duplicado_banco = _pode_comparar_chassi and _ch_para_comparar in chassis_existentes
            _duplicado_fila = len(_ch_visivel_exato) >= 5 and idx in indices_duplicados_fila

            if _duplicado_banco:
                _probs.append(("🔴", f"Registro {idx+1} (Chassi {_ch_para_comparar or 'vazio'}): já existe na tabela principal"))
            elif _duplicado_fila:
                _probs.append(("🔴", f"Registro {idx+1} (Chassi {_ch_visivel_exato or 'vazio'}): duplicado na fila"))
        
        # Contato formato
        if _contato:
            _digits = re.sub(r"[\s\-]", "", _contato)
            _ok = bool(re.match(r"^0[789]0\d{8}$", _digits)) or bool(re.match(r"^0\d{9,10}$", _digits))
            if not _ok:
                _probs.append(("🟡", f"Registro {idx+1} (Contato): fora do padrão japonês"))
        
        # Placa formato (aviso não bloqueante)
        _placa = str(row_dict.get("placa", "")).strip()
        if _placa:
            _ok_placa = bool(re.match(r"^[A-Za-z0-9\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff\-]+(?:[\s\-]+[A-Za-z0-9\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff\-]+)+$", _placa))
            if not _ok_placa:
                _probs.append(("🟡", f"Registro {idx+1} (Placa): formato incompleto ou inválido"))
        
        return _probs
    
    # ── UI de aviso de validação ──────────────────────────
    if st.session_state._reg_aviso:
        _av = st.session_state._reg_aviso
        _msgs = "<br>".join([f"{e} {m}" for e, m in _av["problemas"]])
        st.markdown(f"<div class='reg-alert-box' style='padding:10px;background:#fff3cd;border-left:4px solid #dc7800;border-radius:6px;'><b>⚠️ Atenção:</b><br>{_msgs}</div>", unsafe_allow_html=True)
        _c1, _c2 = st.columns([1, 2])
        with _c1:
            if st.button("✅ OK", key="reg_ok"):
                st.session_state._reg_aviso = None
                st.rerun()
        with _c2:
            if _av.get("pode_salvar"):
                _label_btn = "💾 Salvar válidos" if _av.get("salvar_apenas_validos") else "💾 Salvar mesmo assim"
                if st.button(_label_btn, key="reg_salvar_mesmo"):
                    st.session_state._reg_salvar_mesmo_assim = True
                    st.session_state._reg_aviso = None
                    # Executa salvamento parcial diretamente
                    _executar_salvamento_parcial()
                    st.rerun()
    
    # ── Salvar / Limpar ───────────────────────────────────
    col_salvar, col_limpar = st.columns([2, 1])

    with col_salvar:
        if st.button("💾 Salvar Registros", type="primary", use_container_width=True):
            # Se clicou em Salvar mesmo assim, pula validação
            _forcar_salvar = st.session_state.pop('_reg_salvar_mesmo_assim', False)
            # Validação antes de salvar
            _df_existente = listar_clientes()
            _chassis_existentes = _chassis_existentes_canonicos(_df_existente)
            _registros_visiveis = editor_fila.to_dict("records")
            _assinatura_validacao = _assinatura_chassis_visiveis(_registros_visiveis)
            _indices_duplicados_fila = _indices_duplicados_na_fila(_registros_visiveis)
            _todos_problemas = []
            for i, reg in enumerate(_registros_visiveis):
                _probs = _validar_registro(reg, i, _chassis_existentes, _indices_duplicados_fila)
                _todos_problemas.extend(_probs)
            _mapa_problemas_por_idx = {}
            for emoji, msg in _todos_problemas:
                # Extrai número do registro da mensagem (ex: "Registro 5 (Chassi...)")
                import re
                m = re.search(r"Registro (\d+)", msg)
                if m:
                    idx = int(m.group(1)) - 1
                    _mapa_problemas_por_idx.setdefault(idx, []).append((emoji, msg))

            _tem_bloqueantes = any(e == "🔴" for e, _ in _todos_problemas)
            _tem_avisos = any(e == "🟡" for e, _ in _todos_problemas)

            # Se tem bloqueantes e não está forçando, mostra alerta com opção de salvar válidos mesmo assim
            if _tem_bloqueantes and not _forcar_salvar:
                st.session_state._reg_aviso = {
                    "problemas": _todos_problemas,
                    "pode_salvar": True,
                    "salvar_apenas_validos": True,
                    "assinatura_chassis": _assinatura_validacao
                }
                st.rerun()
            salvos = 0
            com_erros = []
            fila_restante = []
            _chassis_ja_vistos = set()

            for i, row in enumerate(editor_fila.to_dict("records")):
                registro = _registros_visiveis[i].copy()
                for col in colunas_presentes:
                    val = row[col]
                    if col in ("data_registro", "shaken_vencimento"):
                        raw = str(val).strip().replace("-", "").replace("/", "")
                        if len(raw) == 8 and raw.isdigit():
                            val = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                    if col == "veiculo":
                        val = traduzir_veiculo(str(val))
                    registro[col] = val

                # Verifica se este registro tem erros bloqueantes
                _probs_do_reg = _mapa_problemas_por_idx.get(i, [])
                _tem_erro_bloqueante = any(e == "🔴" for e, _ in _probs_do_reg)

                _chassi_novo = _chassi_canonico(registro)
                _duplicado_banco = _chassi_novo and _chassi_novo in _chassis_existentes
                _duplicado_fila = i in _indices_duplicados_fila
                _duplicado_loop = _chassi_novo and _chassi_novo in _chassis_ja_vistos

                if _tem_erro_bloqueante or _duplicado_banco or _duplicado_fila or _duplicado_loop:
                    # Tem erro: mantém na fila para conferência
                    com_erros.append({"reg": registro, "idx": i, "probs": _probs_do_reg})
                    fila_restante.append(st.session_state.fila_registros[i])
                else:
                    # Válido: salva na principal
                    registro.pop("_origem", None)
                    salvar_cliente(registro)
                    salvos += 1
                    if _chassi_novo:
                        _chassis_ja_vistos.add(_chassi_novo)

            st.session_state.fila_registros = fila_restante
            st.session_state._fila_editor_v += 1
            if "df" in st.session_state:
                del st.session_state["df"]

            st.session_state._reg_salvos_count = salvos
            st.session_state._reg_com_erros = com_erros

            st.rerun()

    with col_limpar:
        if st.button("🗑️ Limpar Fila", use_container_width=True):
            st.session_state.fila_registros = []
            st.session_state._fila_editor_v += 1
            st.rerun()
