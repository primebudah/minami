import os
import requests

# Carrega credenciais
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yuwvcmwadzhrzwrcbdla.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_-1v_XqztUK5G2-SYG9L1_w_s6feZneZ")

# Lê o SQL
with open("atualizar_funcao_rpc.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

print("SQL a ser executado:")
print(sql_content)
print("\n" + "="*50 + "\n")

# Executa SQL via API REST do Supabase
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Endpoint para executar SQL
url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

try:
    response = requests.post(url, headers=headers, json={"query": sql_content})
    if response.status_code == 200:
        print("✅ SQL executado com sucesso!")
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Erro: {e}")
