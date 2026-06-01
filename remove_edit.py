#!/usr/bin/env python3
with open('pages/1_Registros.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Troca data_editor por dataframe (só visualização)
old = '''    # Versionador para forçar recriação do editor quando dados mudam
    if "_fila_editor_v" not in st.session_state:
        st.session_state._fila_editor_v = 0
    
    editor_fila = st.data_editor(
        df_fila_view,
        use_container_width=True,
        num_rows="fixed",
        key=f"editor_fila_{st.session_state._fila_editor_v}",
        column_config=_col_cfg
    )

    # Atualiza registros da fila com valores do editor (edição simples)
    for i, row in editor_fila.iterrows():
        for col in colunas_presentes:
            v_new = str(row.get(col, "") or "")
            v_atual = str(st.session_state.fila_registros[i].get(col, "") or "")
            if v_new != v_atual:
                st.session_state.fila_registros[i][col] = v_new'''

new = '''    # Mostra tabela como visualização apenas (sem edição inline)
    st.dataframe(
        df_fila_view,
        use_container_width=True,
        hide_index=True
    )
    
    # Info sobre edição
    st.info("💡 Para corrigir, exclua o registro da fila e adicione novamente pelo formulário.")'''

if old in c:
    c = c.replace(old, new)
    with open('pages/1_Registros.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("✅ Tabela da fila agora é só visualização (sem edição)")
else:
    print("⚠️ Código não encontrado")
