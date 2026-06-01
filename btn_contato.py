#!/usr/bin/env python3
with open('pages/1_Registros.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Adiciona botão "Salvar mesmo assim" para contato inválido
old = '''            # Validação do contato
            if contato:
                ok, msg, pode = _validar_contato_form(contato)
                if not ok:
                    st.warning(f"⚠️ {msg}")'''

new = '''            # Validação do contato
            if contato:
                ok, msg, pode = _validar_contato_form(contato)
                if not ok:
                    st.warning(f"⚠️ {msg}")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.button("✅ OK", key="btn_ok_contato")
                    with col2:
                        if st.button("➕ Salvar mesmo assim", key="btn_salvar_contato"):
                            st.session_state._contato_ignorar = True
                            st.rerun()'''

if old in c:
    c = c.replace(old, new)
    
    # Modifica validação no submit para respeitar a flag
    old2 = '''                # Contato - aviso se inválido
                if contato and str(contato).strip():
                    _digits = re.sub(r"[\\s\\-\\(\\)]", "", str(contato))
                    if not (re.match(r"^0[789]0\\d{8}$", _digits) or re.match(r"^0\\d{9,10}$", _digits)):
                        _avisos.append("Contato fora do padrão japonês")'''
    
    new2 = '''                # Contato - aviso se inválido (só avisa se não clicou "Salvar mesmo assim")
                if contato and str(contato).strip() and not st.session_state.get("_contato_ignorar", False):
                    _digits = re.sub(r"[\\s\\-\\(\\)]", "", str(contato))
                    if not (re.match(r"^0[789]0\\d{8}$", _digits) or re.match(r"^0\\d{9,10}$", _digits)):
                        _avisos.append("Contato fora do padrão japonês")'''
    
    if old2 in c:
        c = c.replace(old2, new2)
    
    # Limpa a flag após adicionar com sucesso
    old3 = '''                # Limpa flag de confirmação
                st.session_state._confirma_aviso = False'''
    
    new3 = '''                # Limpa flags
                st.session_state._confirma_aviso = False
                st.session_state._contato_ignorar = False'''
    
    if old3 in c:
        c = c.replace(old3, new3)
    
    with open('pages/1_Registros.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("✅ Botão 'Salvar mesmo assim' para contato adicionado!")
else:
    print("⚠️ Código não encontrado")
