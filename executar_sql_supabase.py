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

# Executa SQL via API REST do Supabase (endpoint SQL)
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Endpoint para executar SQL direto
url = f"{SUPABASE_URL}/rest/v1/"

try:
    # Tenta executar usando o endpoint de SQL
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/atualizar_cliente_rpc",
        headers=headers,
        json={
            "p_id": 0,  # ID dummy para teste
            "p_nome": "test",
            "p_data_conclusao": "2024-01-01"
        }
    )
    print(f"Teste RPC: {response.status_code}")
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n⚠️  Para executar o SQL no Supabase, você precisa:")
print("1. Abrir https://supabase.com/dashboard/project/yuwvcmwadzhrzwrcbdla/sql/new")
print("2. Colar o conteúdo do arquivo atualizar_funcao_rpc.sql")
print("3. Clicar em Run")
print("\nA API REST do Supabase não permite execução direta de SQL por segurança.")
