# Teste isolado de layout - sem autenticação, sem login
import streamlit as st

st.set_page_config(layout="wide")

st.title("TESTE LAYOUT - Página Completa")

st.write("Se isso aparecer completo, o Streamlit está OK")

# Criar dados de teste
import pandas as pd
df_teste = pd.DataFrame([
    {"Nome": "Cliente 1", "Veículo": "Toyota", "Status": "Ativo"},
    {"Nome": "Cliente 2", "Veículo": "Honda", "Status": "Pendente"},
    {"Nome": "Cliente 3", "Veículo": "Nissan", "Status": "Concluído"},
    {"Nome": "Cliente 4", "Veículo": "Mazda", "Status": "Ativo"},
    {"Nome": "Cliente 5", "Veículo": "Subaru", "Status": "Pendente"},
    {"Nome": "Cliente 6", "Veículo": "Mitsubishi", "Status": "Concluído"},
    {"Nome": "Cliente 7", "Veículo": "Suzuki", "Status": "Ativo"},
    {"Nome": "Cliente 8", "Veículo": "Daihatsu", "Status": "Pendente"},
])

st.subheader("Tabela de Teste")
st.dataframe(df_teste, use_container_width=True)

st.subheader("Conteúdo adicional para testar scroll")
for i in range(20):
    st.write(f"Linha de conteúdo {i+1} - Testando se a página completa aparece e se o scroll funciona corretamente no tablet e no navegador Savana.")

st.success("Se você está vendo esta mensagem no final, o layout está funcionando!")
