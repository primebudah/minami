# CSS MINIMALISTA - SOMENTE ESSENCIAL
# Sem nenhuma regra que afete layout responsivo do Streamlit

import streamlit as st

def inject_base_css_minimal():
    """Versão minimalista do CSS - apenas esconde menus, nada de layout"""
    st.markdown("""
    <style>
    /* APENAS esconder menus indesejados - NÃO afeta layout */
    #MainMenu { display: none !important; }
    footer { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
