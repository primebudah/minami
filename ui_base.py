import os
import streamlit as st
import streamlit.components.v1 as components

def inject_base_css():
    st.markdown("""
    <style>
    /* Nav e controles nativos */
    [data-testid="stSidebarNav"]      { display: none !important; }

    /* GARANTE que botão de toggle da sidebar esteja sempre visível */
    button[kind="header"],
    button[aria-label="sidebar"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"],
    [data-testid="stToolbar"] button,
    header button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
    }

    /* Header com cor azul da sidebar */
    header,
    [data-testid="stHeader"] {
        background: linear-gradient(270deg, #1044b5, #64c8ff, #0d2a6e, #64c8ff) !important;
        background-size: 400% 400% !important;
    }

    /* Oculta botões específicos do GitHub/Fork no header */
    [data-testid="stHeader"] button[title*="Fork"],
    [data-testid="stHeader"] button[title*="GitHub"],
    [data-testid="stHeader"] button[title*="git"],
    header button[title*="Fork"],
    header button[title*="GitHub"],
    header button[title*="git"] {
        display: none !important;
    }

    /* Garante que botão Open sidebar continue visível */
    button[aria-label="Open sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        background: #1a6fba !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-size: 18px !important;
    }
    button[aria-label="Open sidebar"]::before {
        content: "▶ " !important;
    }

    /* Remove espaço vazio no topo da sidebar */
    [data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem !important; }
    [data-testid="stSidebarContent"]            { padding-top: 0 !important; }
    section[data-testid="stSidebar"] > div      { padding-top: 0.5rem !important; }

    /* Remove espaço vazio no topo do conteúdo principal */
    [data-testid="stAppViewContainer"] > section.main > div.block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stMain"] > div { padding-top: 0.5rem !important; }

    /* Centraliza a tabela (data_editor com largura fixa) */
    [data-testid="stDataEditorContainer"],
    [data-testid="stDataFrame"] {
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* Oculta apenas menu principal e footer (não afetam sidebar) */
    #MainMenu                          { display: none !important; }
    footer                             { display: none !important; }

    /* Oculta apenas elementos de toolbar específicos (não afetam sidebar) */
    [data-testid="stDataFrameToolbar"]         { display: none !important; }
    [data-testid="stElementToolbar"]           { display: none !important; }
    [data-testid="stElementToolbarButton"]     { display: none !important; }
    [data-testid="stSendElement"]              { display: none !important; }
    [data-testid="stShareButton"]              { display: none !important; }
    [data-testid="stDecoration"]               { display: none !important; }
    [class*="stElementToolbar"]                { display: none !important; }
    /* NÃO ocultar stToolbar - contém botão da sidebar */
    /* [class*="stToolbar"]                       { display: none !important; } */
    button[title="Send element"]               { display: none !important; }
    button[title="Send console errors"]        { display: none !important; }
    button[aria-label="Send element"]          { display: none !important; }
    button[aria-label="Send console errors"]   { display: none !important; }
    /* Remove cursor de bloqueado em botões desabilitados */
    button[disabled], button:disabled { cursor: default !important; }

    /* Botões de modo Tabela/Colunas — azul fixo */
    button[data-testid="btn_tabela"],
    button[data-testid="btn_colunas"] {
        background: #1a6fba !important;
        color: #fff !important;
        border: none !important;
        opacity: 1 !important;
    }
    /* Botão Avisos — azul (sem avisos) */
    button[data-testid="toggle_avisos"] {
        background: #1a6fba !important;
        color: #fff !important;
        border: none !important;
    }
    /* Oculta menu de contexto do data_editor */
    [data-testid="stDataFrameResizeHandle"] { display: none !important; }
    [data-testid="stDataFrameColumnMenuButton"] { display: none !important; }
    [data-testid="stDataFrameColumnMenu"]       { display: none !important; }
    [class*="columnMenu"]                       { display: none !important; }
    [class*="ColumnMenu"]                       { display: none !important; }
    [class*="headerMenu"]                       { display: none !important; }
    [class*="glideDataEditor"] [role="menu"]    { display: none !important; }
    [data-testid="stDataFrameActionBar"]    { display: none !important; }
    [data-testid="stDataFrameActionBarContainer"] { display: none !important; }
    [data-testid="stDataEditorActionBar"]   { display: none !important; }
    button[aria-label="More options"]       { display: none !important; }
    button[aria-label="Options"]            { display: none !important; }
    [class*="actionBar"]                    { display: none !important; }
    [class*="ActionBar"]                    { display: none !important; }
    /* Campos de input — fundo branco */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-baseweb="input"] input { background-color: #FFFFFF !important; color: #000000 !important; }
    [data-testid="stDateInput"] > div,
    [data-testid="stDateInput"] div[data-baseweb="input"] { background-color: #FFFFFF !important; }
    /* File uploader — fundo branco */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] section > div,
    [data-testid="stFileUploaderDropzone"] { background-color: #FFFFFF !important; color: #000000 !important; }
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] span { color: #333333 !important; }

    /* Erros/warnings flutuantes no canto */
    [data-testid="stStatusWidget"]             { display: none !important; }
    [data-testid="stException"]                { display: none !important; }
    ._profileContainer                         { display: none !important; }
    ._profilePreview                           { display: none !important; }

    /* Streamlit puro - sem CSS de layout */
    </style>
    """, unsafe_allow_html=True)
